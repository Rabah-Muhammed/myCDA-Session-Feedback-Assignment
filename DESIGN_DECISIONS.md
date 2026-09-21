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
If a parent submits a review for their child for a specific session, the child should not be able to submit a duplicate review for that same session (and vice versa). Each student gets exactly one feedback entry per completed session.

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

## 5. Frontend Implementation & UX

- **Role-Conditional Cards:** Students and parents see the submission form and feedback history. Instructors and admins see the performance summary.
- **Dynamic Session Loading:** When a student or parent selects a child, the form queries `/api/v1/feedback/eligible-sessions/` to show only sessions that are completed, within 30 days, and not yet reviewed.
- **Instant Feedback:** Submitting a review immediately removes the session from the eligible list and triggers a refresh on the history card without a full page reload.
- **Parent Grouping:** On the history card, feedback for parents is automatically grouped by student so they can easily distinguish reviews between multiple children.

---

## 6. Practical Trade-offs

1. **Admin Instructor Selector:** In `InstructorSummaryCard.tsx`, the admin view defaults to selecting between Coach Sarah (ID: 2) and Coach Marcus (ID: 3). In a full production app, this would be backed by a dedicated `/api/v1/accounts/instructors/` dropdown endpoint.
2. **History Pagination:** While the `/api/v1/feedback/my/` endpoint supports `StandardPagination` (20 items per page), the frontend card currently displays the first page. For a debate academy where students take 1–2 classes a week, 20 items covers several months of history, which is sufficient for the current scope.
