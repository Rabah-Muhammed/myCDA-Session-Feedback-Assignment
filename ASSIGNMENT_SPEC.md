# Session Feedback Feature -- Assignment Spec

## Overview

You are joining the **myCDA** platform team. myCDA is a dashboard used by students, parents, instructors, and admins at a debate academy. The backend is Django 5.1 + Django REST Framework. The frontend is Next.js 14 (App Router) with Tailwind CSS.

Your task: **build the Session Feedback feature end to end.** After a class session is marked as completed, students (or parents on behalf of their linked students) can leave a short structured review. Instructors see aggregated scores on their dashboard -- but never the raw text or student identity tied to any individual review.

You have **one working day** to deliver this.

---

## What already exists

The starter repo gives you:

- A working Django backend with `accounts`, `classes`, and an empty `feedback` app
- User authentication via token auth (login endpoint provided)
- A working Next.js frontend with a login page, dashboard shell, sidebar, and two pre-built cards (Active Classes, Profile)
- Seed data: 2 instructors, 5 students, 3 parents, 1 admin, 3 classes, and ~30 sessions with various statuses
- A `core` app with shared base classes, permissions, and middleware that all apps use

**Read the existing code before you start building.** The codebase has conventions. Follow them.

---

## Backend requirements

### Data model

Create a `SessionFeedback` model in the `feedback` app. Each feedback entry captures:

- **The session** it refers to (FK to `Session`)
- **The student** who is being represented (FK to `User`, must have role `student`)
- **The submitter** (FK to `User` -- could be the student themselves or their parent)
- **Three ratings**, each an integer from 1 to 5:
  - `rating_clarity` -- how clearly the instructor explained concepts
  - `rating_engagement` -- how engaging the session was
  - `rating_pace` -- whether the pacing felt right
- **An optional text note** (max 500 characters)
- Timestamps

### Constraints (enforce server-side)

1. Feedback can only be submitted for sessions with `status = 'completed'`
2. Feedback cannot be submitted for sessions completed more than 30 days ago
3. One feedback per student per session (no duplicates). The uniqueness is on `(session, student)`, not `(session, submitter)` -- a parent re-submitting for the same student on the same session is still a duplicate
4. All three ratings must be between 1 and 5 inclusive
5. Only the student themselves or a parent linked to that student (via `FamilyLink`) can submit feedback for that student
6. The `submitter` field should be auto-populated from the authenticated user -- not accepted in the request body

### API endpoints

All endpoints live under `/api/v1/feedback/`. Follow the URL and serializer conventions already in the project.

**POST `/api/v1/feedback/`**
Submit feedback. Request body includes `session`, `student` (required if submitter is a parent, optional if submitter is the student themselves -- default to self), and the three ratings + optional note. Returns the created feedback.

**GET `/api/v1/feedback/my/`**
List feedback submitted by the current user (or for the current user's linked students if they are a parent). Ordered by most recent first. Paginated.

**GET `/api/v1/feedback/instructor-summary/`**
Available to instructors and admins only. Returns aggregated feedback for the requesting instructor (or for a specific instructor if admin passes `?instructor_id=X`).

The aggregation must:
- Return the **weighted rolling average** of the last 10 completed sessions (not all-time)
- Weight each session's average score by that session's `duration_minutes` (found inside `Session.session_metadata["duration_minutes"]`)
- Group by rating dimension (clarity, engagement, pace) and also return an overall weighted average
- Return the total number of feedback entries across those sessions
- **Never expose student identity, submitter identity, or raw text notes in this endpoint**

### What "anonymized" means

The instructor-summary endpoint must not include:
- Student name, ID, email, or any identifying field
- Submitter name, ID, email
- Raw text notes
- Any data that could be cross-referenced to identify a student (e.g., if only one student is in a class, don't return per-session breakdowns that reveal them)

If an AI tool generates a serializer that includes a `student` field on the instructor-facing response, that is a security failure.

---

## Frontend requirements

### Feedback submission form

- Accessible from the dashboard when logged in as a student or parent
- Shows a list of sessions eligible for feedback (completed, within 30 days, not yet reviewed)
- For parents: a dropdown to select which linked student they are submitting for
- Three slider or star-rating inputs for the three dimensions
- Optional text area for the note (with character count)
- Optimistic UI: show the feedback as submitted immediately, roll back on error
- Proper error handling: show server validation errors (e.g., "Feedback already submitted for this session")

### Feedback history (student/parent view)

- A dashboard card showing previously submitted feedback
- Each entry shows: session date, class name, the three ratings, and the note (if any)
- If parent: shows feedback for all linked students, grouped by student

### Instructor summary card

- A dashboard card visible only to instructors (and admins)
- Shows the weighted rolling average for each dimension and overall
- Shows total feedback count
- Clearly labeled that these are aggregated, anonymized scores
- Visual treatment: bar chart, radial chart, or simple number display -- your choice, but it should be readable at a glance

---

## Submission requirements

1. Your code must run. `python manage.py migrate && python manage.py seed_data` then `python manage.py runserver` for the backend. `npm install && npm run dev` for the frontend.
2. Include a `DESIGN_DECISIONS.md` file explaining:
   - How you modeled the data and why
   - How you implemented the anonymization
   - How you computed the weighted rolling average
   - Any trade-offs you made given the time constraint
3. All existing tests must still pass
4. Use AI tools however you like, but you must be able to explain every line of your code if asked

---

## Test accounts

See `TEST_ACCOUNTS.md` for login credentials for each role. Use these to manually verify your feature works for every user type.

---

## Evaluation criteria

We are looking at:

1. **Does it work?** Can each user type do what they need to?
2. **Is the data model sound?** Constraints, validation, and uniqueness enforced correctly?
3. **Is the anonymization real?** Not just hidden in the UI but enforced at the API layer?
4. **Does the code follow the project's existing conventions?** Base serializer, permission classes, URL patterns, middleware usage?
5. **Is the weighted rolling average correct?** Not a simple average, not all-time, weighted by session duration?
6. **Can you explain your decisions?** The DESIGN_DECISIONS.md and a follow-up conversation will tell us how you think.
