# myCDA -- Session Feedback Assignment

## What is this?

A starter repo for the myCDA platform. Your task is to build the **Session Feedback** feature. Read `ASSIGNMENT_SPEC.md` for full requirements and `TEST_ACCOUNTS.md` for test credentials.

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

### Run existing tests

```bash
python manage.py test
```

All existing tests must continue to pass after your changes.

## Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend runs at `http://localhost:3000`. It expects the backend at `http://localhost:8000` (configured in `.env.local`).

## Project structure

```
backend/
  config/          # Django settings, root URL config
  core/            # Shared base classes -- READ THESE FIRST
    serializers.py # BaseModelSerializer (all serializers extend this)
    permissions.py # HasRole() factory and role permission classes
    pagination.py  # StandardPagination (project-wide)
    middleware.py  # RequestAuditMiddleware (attaches user to thread-local)
  accounts/        # User model, FamilyLink, auth endpoints
  classes/         # Class, ClassEnrollment, Session models and endpoints
  feedback/        # YOUR WORK GOES HERE

frontend/
  src/
    app/
      login/       # Login page (done)
      dashboard/   # Dashboard shell (done) -- add your cards here
    components/    # Shared components
      DashboardCard.tsx    # Card wrapper -- use this for your cards
      ActiveClassesCard.tsx # Example card (study this pattern)
      ProfileCard.tsx       # Example card with role-conditional content
      Sidebar.tsx           # Nav sidebar -- add your routes here
    contexts/
      AuthContext.tsx # Auth state management
    lib/
      api.ts       # API client -- use this for all backend calls
      types.ts     # TypeScript types
```

## What to submit

1. Your completed code (the full repo with your additions)
2. A `DESIGN_DECISIONS.md` file in the repo root explaining your choices
3. Make sure `python manage.py test` passes
4. Make sure both backend and frontend start without errors
