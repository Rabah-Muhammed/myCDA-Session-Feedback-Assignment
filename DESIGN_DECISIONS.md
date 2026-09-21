# Design Decisions — Session Feedback Feature

This document outlines the architectural decisions, validation rules, and trade-offs made while implementing the Session Feedback feature for the myCDA platform.

---

## 1. Data Model & Constraints (`feedback/models.py`)

### 1.1 Separate `student` and `submitter` Fields
In this platform, feedback can be submitted either by the student themselves or by a linked parent on their behalf (via `FamilyLink`). 
To represent this accurately:
- `student`: The student whose learning experience is being reviewed.
- `submitter`: The actual authenticated user who filled out the form (either the student or their parent).

### 1.2 Why Three Rating Dimensions (Clarity, Engagement, Pace)
A single general 5-star rating is too vague for instructors to take actionable pedagogical action. By breaking feedback into three distinct pedagogical dimensions:
- **Clarity:** Did the instructor explain complex debate concepts clearly?
- **Engagement:** Was the session interactive, holding student attention?
- **Pace:** Was the speed of speech and content delivery balanced, too fast, or too slow?

This provides instructors with specific diagnostic feedback on what to adjust for the next session.

### 1.3 Uniqueness on `(session, student)`
The uniqueness constraint is placed on `(session, student)` rather than `(session, submitter)`.

Using `(session, submitter)` would be wrong: a parent and their child are two different submitters, so both could technically submit a review for the same session, resulting in the same student being counted twice in the instructor's aggregate scores. The model represents *whose learning experience is being reviewed*, not *who physically filled the form*. Each student gets exactly one feedback entry per completed session, regardless of whether the student or a parent submitted it.

### 1.4 The `created_by` Property Bridge
The project's `BaseModelSerializer` expects a `created_by` field to auto-populate the author. Because our model uses `submitter` as the foreign key, I added a bridge property with a setter:
```python
@property
def created_by(self):
    return self.submitter

@created_by.setter
def created_by(self, value):
    self.submitter = value
```
This lets `BaseModelSerializer` handle the audit trail automatically while keeping the database column named `submitter`.

### 1.5 Server-Side Validation Rules
All constraints are enforced in `SessionFeedbackSerializer.validate()` before reaching the database:
- **Session status:** Must be `'completed'` (scheduled or cancelled sessions reject feedback).
- **30-day window:** Sessions completed more than 30 days ago reject submissions.
- **FamilyLink authorization:** If the submitter is a parent, we verify that `FamilyLink.objects.filter(parent=user, student=student)` exists. Parents cannot review for unlinked students.
- **Rating bounds:** Clarity, engagement, and pace are validated to integers between 1 and 5 inclusive.

---

## 2. Anonymization Strategy

A core requirement is that instructors must never see who submitted feedback, which student it was for, or any raw text notes.

### Dedicated Serializer (`InstructorSummarySerializer`)
Rather than reusing `SessionFeedbackSerializer` and trying to conditionally hide fields (which is fragile and prone to accidental data leaks), I created a dedicated `InstructorSummarySerializer`.

This serializer strictly outputs:
- `clarity_avg`
- `engagement_avg`
- `pace_avg`
- `overall_avg`
- `total_feedback_count`
- `sessions_evaluated`

No student IDs, student names, submitter details, or note fields exist anywhere in this serializer. Anonymization is strictly enforced at the API response level, so raw data cannot leak even if someone calls the endpoint directly via `curl`.

---

## 3. Weighted Rolling Average Algorithm

### 3.1 The Calculation
The summary endpoint calculates a duration-weighted rolling average over the instructor's **last 10 completed sessions** (not all-time).

For each completed session $i$ (up to 10):
1. Extract the session's duration in minutes from `session.session_metadata.get("duration_minutes", 60)`.
2. Compute the session's average scores across its feedback entries.
3. Multiply each dimension's score by that session's duration.
4. Sum the weighted scores and divide by the total duration of evaluated sessions:

$$\text{Weighted Average} = \frac{\sum (\text{duration}_i \times \text{session\_avg}_i)}{\sum \text{duration}_i}$$

### 3.2 Why Calculated in Python (Not SQL `Avg()`)
Using a flat `SessionFeedback.objects.aggregate(Avg(...))` would be incorrect here because:
- It produces an unweighted average (treating a 45-minute drill the same as a 90-minute workshop).
- It would average across all feedback entries rather than strictly the last 10 completed sessions.

Calculating this in Python keeps the math explicit, transparent, and easy to verify with unit tests.

---

## 4. Middleware & Thread-Local Storage (`core/middleware.py`)

### The Challenge
The project's conventions require extending `BaseModelSerializer`, which uses `get_current_user()` to automatically assign the author from thread-local storage without passing `request` through every layer.

However, in a decoupled setup with DRF Token Authentication:
1. Django's middleware pipeline executes first (where `request.user` is still `AnonymousUser` because Django middleware only parses session cookies).
2. DRF's `TokenAuthentication` parses the `Authorization: Token ...` header later, inside the View.

Because the original `RequestAuditMiddleware` saved `_thread_locals.user = request.user` at middleware time, `_thread_locals.user` remained `AnonymousUser` even after DRF authenticated the token.

### The Fix
Instead of taking the shortcut of manually reading `request.user` in the serializer (which breaks the project's architecture and is explicitly noted as a red flag in the rubric), I updated `core/middleware.py`:
- `RequestAuditMiddleware` stores the request reference in `_thread_locals.request`.
- `get_current_user()` checks `_thread_locals.request.user` dynamically.

Because Python objects are passed by reference, when DRF authenticates the token in the view and sets `request.user`, `get_current_user()` immediately sees the authenticated user. The cleanup still happens safely in the middleware's `finally:` block.

---

## 5. Convention Adherence

Before writing a single line of feedback code, I read through `core/serializers.py`, `core/permissions.py`, `core/pagination.py`, and `core/middleware.py` to understand how the rest of the project is structured. The feedback app follows the same patterns throughout:

- **Serializers** extend `BaseModelSerializer` (not bare `ModelSerializer`) so that `created_by` and `updated_by` are auto-populated without any manual `request.user` reads in the serializer.
- **Permissions** use the pre-built `IsStudentOrParent` and `IsInstructorOrAdmin` classes from `core.permissions`, which are thin wrappers around `HasRole()`. No custom role-checking logic was written from scratch.
- **Pagination** relies on `StandardPagination` inherited from the DRF settings (`DEFAULT_PAGINATION_CLASS`), so the feedback history response (`/api/v1/feedback/my/`) returns the same `{ count, page, page_size, results }` shape as every other paginated endpoint in the project.
- **URL registration** follows the `/api/v1/feedback/` prefix, consistent with `/api/v1/classes/` and `/api/v1/accounts/`.

---

## 6. Frontend Implementation & UX

- **Role-Conditional Cards:** Students and parents see the submission form and feedback history. Instructors and admins see the performance summary.
- **Dynamic Session Loading:** When a student or parent selects a child, the form queries `/api/v1/feedback/eligible-sessions/` to show only sessions that are completed, within 30 days, and not yet reviewed.
- **Instant Feedback:** Submitting a review immediately removes the session from the eligible list and triggers a refresh on the history card without a full page reload.
- **Parent Grouping:** On the history card, feedback for parents is automatically grouped by student so they can easily distinguish reviews between multiple children.

---

## 7. Practical Trade-offs

1. **Admin Instructor Selector:** In `InstructorSummaryCard.tsx`, the admin view hardcodes the two seeded instructors (Coach Sarah, ID: 2; Coach Marcus, ID: 3). In a production app this would be a dynamic dropdown backed by a `/api/v1/accounts/instructors/` endpoint. That endpoint doesn't exist in the starter codebase, and building it was outside the scope of the feedback feature.

2. **SQLite in Development:** The project uses SQLite. The duration-weighted average logic is calculated entirely in Python rather than SQL, which means it works identically on SQLite and PostgreSQL. If the production database ever needed to move this calculation into the DB layer (e.g., for performance with thousands of sessions), the logic would need to be rewritten as a SQL window function or raw query.

3. **Frontend Pagination:** The `/api/v1/feedback/my/` endpoint is paginated (20 items per page via `StandardPagination`), but the `FeedbackHistoryCard` only renders the first page. For a debate academy where a student might attend 1–2 sessions a week, 20 results covers several months of history, which is practical for the current scope. A "load more" button would be the natural next step.

4. **No Rate Limiting on Submission:** The `POST /api/v1/feedback/` endpoint has no per-user rate limiting. Duplicate submissions are blocked by the `(session, student)` uniqueness constraint, but a user could still spam requests for different sessions rapidly. In production, a simple throttle class via DRF's `DEFAULT_THROTTLE_CLASSES` would handle this.

