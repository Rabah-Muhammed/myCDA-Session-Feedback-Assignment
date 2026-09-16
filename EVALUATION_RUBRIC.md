# Evaluation Rubric (Internal -- Do Not Share With Candidates)

Score each section 0-3:
- 0 = Missing or fundamentally broken
- 1 = Attempted but significant issues
- 2 = Works with minor issues
- 3 = Solid, follows conventions, handles edge cases

---

## 1. Data Model (0-3)

**What to check:**
- [ ] SessionFeedback model exists with correct fields (session FK, student FK, submitter FK, three rating fields, note, timestamps)
- [ ] `unique_together` on (session, student) -- not (session, submitter)
- [ ] Rating fields have validators (1-5 range) or equivalent constraint
- [ ] `created_by` / submitter field is a FK to User
- [ ] Model has `created_at` and `updated_at` (auto_now_add / auto_now)

**Red flags (vibe coding tells):**
- Rating stored as a single field instead of three separate dimensions
- No uniqueness constraint at all
- Submitter accepted in request body instead of auto-populated
- No FK to Session or student -- just stores IDs as integers

---

## 2. Convention Adherence (0-3)

**What to check:**
- [ ] Serializers extend `core.serializers.BaseModelSerializer` (not bare `ModelSerializer`)
- [ ] Permission classes use `core.permissions.HasRole()` or the pre-built classes
- [ ] URLs registered under `/api/v1/feedback/` following the existing pattern
- [ ] Pagination uses `StandardPagination` (or inherits it from settings)
- [ ] `created_by` auto-populated via BaseModelSerializer's `create()` method (leverages the middleware)

**Red flags:**
- Imports `ModelSerializer` from rest_framework directly
- Writes own `IsAuthenticated` or role-check logic from scratch
- Custom pagination class that doesn't match the project's response shape
- Manually reads `request.user` in the serializer instead of letting the base class handle it

---

## 3. Anonymization (0-3) -- CRITICAL

**What to check:**
- [ ] Instructor-summary endpoint returns ONLY aggregated numbers -- no student IDs, names, emails
- [ ] Raw text notes are NOT included in the instructor-summary response
- [ ] Submitter info is NOT included in the instructor-summary response
- [ ] The serializer itself enforces this (not just "hidden in the UI")
- [ ] Per-session breakdowns (if any) don't enable identification of students

**How to test:**
```bash
# Log in as coach.sarah, hit the instructor-summary endpoint, inspect raw JSON
curl -H "Authorization: Token <sarah_token>" http://localhost:8000/api/v1/feedback/instructor-summary/

# The response should have NO student-identifying fields
# Check: no "student", "student_id", "student_name", "submitter", "note" keys
```

**Red flags:**
- A single serializer used for both student-facing and instructor-facing views
- Student FK included in the instructor serializer (even if labeled "read_only")
- Notes field present in the aggregation response
- Using the same endpoint for both submission list and instructor summary

---

## 4. Weighted Rolling Average (0-3)

**What to check:**
- [ ] Averages are computed over the LAST 10 completed sessions only (not all-time)
- [ ] Each session's score is WEIGHTED by its `duration_minutes` from `session_metadata`
- [ ] The three dimensions (clarity, engagement, pace) are averaged separately
- [ ] An overall weighted average is also returned
- [ ] Total feedback count is included in the response

**How to verify the math:**
Suppose the last 10 sessions have these profiles:
- Session A: 90 min, avg clarity = 4.0
- Session B: 60 min, avg clarity = 3.0
- ...

Weighted avg = sum(duration_i * avg_score_i) / sum(duration_i)

90*4.0 + 60*3.0 = 540/150 = 3.6 (not the simple average of 3.5)

**Red flags:**
- Simple `Avg()` aggregation across all feedback entries
- No limit to 10 sessions
- Duration not used in the calculation (unweighted)
- Duration read from a hardcoded default instead of `session_metadata`
- Averaging across all time instead of rolling window

---

## 5. Validation and Edge Cases (0-3)

**What to check:**
- [ ] Rejects feedback for non-completed sessions (scheduled, cancelled)
- [ ] Rejects feedback for sessions completed > 30 days ago
- [ ] Rejects duplicate feedback (same student + same session)
- [ ] Rejects ratings outside 1-5 range
- [ ] Only allows student themselves OR a linked parent to submit for that student
- [ ] Rejects a parent submitting for a student not linked via FamilyLink
- [ ] Submitter field auto-populated, not accepted in request body

**Test commands:**
```bash
# Try submitting for a cancelled session
# Try submitting duplicate feedback
# Try submitting as parent.priya for student.emma (not linked)
# Try submitting rating 0 or rating 6
```

**Red flags:**
- No validation on session status
- No 30-day window check
- Parent can submit for any student (no FamilyLink check)
- Uniqueness only checked at DB level with no friendly error message

---

## 6. Frontend Implementation (0-3)

**What to check:**
- [ ] Feedback form works for students (self-submission)
- [ ] Feedback form works for parents (select child, then submit)
- [ ] Shows only eligible sessions (completed, within 30 days, not yet reviewed)
- [ ] Three rating inputs (sliders, stars, or similar) for the three dimensions
- [ ] Optional note with character count
- [ ] Error states displayed (validation errors, duplicates)
- [ ] Feedback history card shows past submissions
- [ ] Instructor summary card shows aggregated scores (no student info)
- [ ] Cards use `DashboardCard` wrapper component
- [ ] Role-conditional rendering (students/parents see submission, instructors see summary)

**Red flags:**
- No error handling -- form silently fails
- All users see all cards regardless of role
- Instructor card shows raw student data
- Custom card styling that doesn't use `DashboardCard`
- No loading states

---

## 7. DESIGN_DECISIONS.md Quality (0-3)

**What to check:**
- [ ] Explains the data model choices (why separate submitter and student, why three rating fields)
- [ ] Explains how anonymization works at the serializer/view level
- [ ] Explains the weighted rolling average algorithm
- [ ] Mentions trade-offs made due to time constraints
- [ ] Demonstrates understanding of the codebase (references existing patterns)

**Red flags:**
- Generic or boilerplate explanations that could apply to any project
- No mention of the base serializer or middleware
- Can't explain why uniqueness is on (session, student) not (session, submitter)
- Claims "I used AI to generate this" without showing understanding

---

## Scoring

| Section | Weight | Score (0-3) | Weighted |
|---------|--------|-------------|----------|
| Data Model | 15% | | |
| Convention Adherence | 15% | | |
| Anonymization | 20% | | |
| Weighted Rolling Avg | 15% | | |
| Validation / Edge Cases | 15% | | |
| Frontend | 10% | | |
| Design Decisions Doc | 10% | | |
| **Total** | **100%** | | |

**Thresholds:**
- 2.5+ weighted average: Strong hire signal
- 2.0-2.4: Proceed to interview, probe weak areas
- 1.5-1.9: Borderline, only if other signals are strong
- Below 1.5: Pass

**Immediate disqualifiers:**
- Student names/emails visible in the instructor-summary API response
- Existing tests broken
- App doesn't run at all
- Cannot explain their own code in follow-up
