# myCDA -- Session Feedback Assignment

## What is this?

A starter repo for the myCDA platform with the **Session Feedback** feature implemented. Read `ASSIGNMENT_SPEC.md` for requirements, `TEST_ACCOUNTS.md` for test credentials, and `DESIGN_DECISIONS.md` for architecture and implementation details.

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

## Backend setup

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed the database with test data
python manage.py seed_data

# Start the dev server
python manage.py runserver
```

The backend runs at `http://localhost:8000`. API base: `http://localhost:8000/api/v1/`.

### Verify it works

```bash
# Login and get a token
curl -X POST http://localhost:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student.emma", "password": "testpass123"}'

# Use the token to hit a protected endpoint
curl http://localhost:8000/api/v1/classes/ \
  -H "Authorization: Token <your-token-here>"
```

### Run tests

```bash
python manage.py test
```

All 28 tests (13 core + 15 feedback tests) pass.

## Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend runs at `http://localhost:3000`. It expects the backend at `http://localhost:8000` (configured in `.env.local`).

## Implemented Feedback Endpoints

All feedback endpoints are authenticated via `Authorization: Token <token>`:

| Endpoint | Method | Allowed Roles | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/feedback/` | `POST` | Student, Parent | Submit session feedback (1–5 ratings + optional notes). |
| `/api/v1/feedback/my/` | `GET` | Student, Parent | Paginated list of past submissions for the user or linked children. |
| `/api/v1/feedback/eligible-sessions/` | `GET` | Student, Parent | Attended sessions within 30 days eligible for feedback (accepts `?student_id=` for parents). |
| `/api/v1/feedback/instructor-summary/` | `GET` | Instructor, Admin | Duration-weighted rolling metrics across last 10 completed sessions (accepts `?instructor_id=` for admins). |

## Project structure

```
backend/
  config/          # Django settings, root URL config
  core/            # Shared base classes
    serializers.py # BaseModelSerializer (all serializers extend this)
    permissions.py # HasRole() factory and role permission classes
    pagination.py  # StandardPagination (project-wide)
    middleware.py  # RequestAuditMiddleware (attaches user to thread-local)
  accounts/        # User model, FamilyLink, auth endpoints
  classes/         # Class, ClassEnrollment, Session models and endpoints
  feedback/        # ⭐ Session Feedback app
    models.py      # SessionFeedback model with unique(session, student) constraint
    serializers.py # SessionFeedbackSerializer & InstructorSummarySerializer
    views.py       # Feedback submission, history, eligibility, and instructor summary
    urls.py        # /api/v1/feedback/ routing
    tests.py       # 15 unit and integration tests

frontend/
  src/
    app/
      login/       # Login page
      dashboard/   # Dashboard shell rendering role-conditional cards
    components/    # Shared components
      DashboardCard.tsx          # Card wrapper
      FeedbackFormCard.tsx       # Feedback submission form (student & parent proxy)
      FeedbackHistoryCard.tsx    # Past submissions list (grouped for parents)
      InstructorSummaryCard.tsx  # Weighted metrics & instructor selector for admins
      ActiveClassesCard.tsx      # Active classes list
      ProfileCard.tsx            # Profile card
      Sidebar.tsx                # Nav sidebar
    contexts/
      AuthContext.tsx # Auth state management
    lib/
      api.ts       # API client with feedback methods
      types.ts     # TypeScript types
```

## Additional Documentation

- `DESIGN_DECISIONS.md` — Detailed explanation of data modeling, parent proxy submission, anonymization guarantees, duration-weighted average math, and middleware lifecycle.
- `TEST_ACCOUNTS.md` — Seeded test accounts across all roles (Student, Parent, Instructor, Admin).
