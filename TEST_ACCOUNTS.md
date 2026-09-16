# Test Accounts

All accounts use the password: **testpass123**

## Admin

| Username | Name | Notes |
|----------|------|-------|
| admin | Admin User | Can see all data. Use to verify instructor-summary endpoint accepts `?instructor_id=X`. |

## Instructors

| Username | Name | Teaches |
|----------|------|---------|
| coach.sarah | Sarah Chen | Lincoln-Douglas Debate Fundamentals, Congressional Debate Workshop |
| coach.marcus | Marcus Rivera | Public Forum Debate Advanced |

Log in as an instructor to verify:
- The instructor summary card shows aggregated, anonymized scores
- No student names, emails, or text notes are visible
- The weighted rolling average reflects the last 10 completed sessions

## Parents

| Username | Name | Linked Students |
|----------|------|-----------------|
| parent.james | James Wilson | Emma Wilson, Liam Wilson |
| parent.priya | Priya Sharma | Anika Sharma |
| parent.david | David Brown | Noah Brown |

Log in as a parent to verify:
- They can submit feedback on behalf of their linked student(s)
- They must select which student the feedback is for
- They can see feedback history for all their linked students
- They cannot submit feedback for a student not linked to them

## Students

| Username | Name | Enrolled In | Parent Linked? |
|----------|------|-------------|----------------|
| student.emma | Emma Wilson | LD Fundamentals, PF Advanced | Yes (James Wilson) |
| student.liam | Liam Wilson | LD Fundamentals | Yes (James Wilson) |
| student.anika | Anika Sharma | LD Fundamentals, Congress Workshop | Yes (Priya Sharma) |
| student.noah | Noah Brown | PF Advanced, Congress Workshop | Yes (David Brown) |
| student.zara | Zara Adams | PF Advanced | No parent linked |

Log in as a student to verify:
- They can submit feedback for completed sessions in their enrolled classes
- They cannot submit feedback for cancelled or scheduled sessions
- They cannot submit duplicate feedback for the same session
- They can see their own feedback history

## Edge cases to test

1. **Zara Adams** has no parent linked. She can only submit feedback herself.
2. **Emma Wilson** is in two classes (LD and PF) with different instructors. Her feedback should show up in the correct instructor's summary.
3. **James Wilson** has two children. When submitting feedback, he must choose which child it's for.
4. Sessions older than 30 days should not accept feedback. Check the earliest LD sessions.
5. Cancelled sessions (LD session 6, PF session 8) should reject feedback.
6. A parent trying to submit feedback for a student not linked to them should get a 403 or validation error.

## Classes and sessions overview

**Lincoln-Douglas Debate Fundamentals** (Coach Sarah)
- 12 sessions total
- Sessions 1-5, 7-10: completed (session 6: cancelled, 11-12: scheduled)
- Students: Emma, Liam, Anika
- Session durations vary: 45, 60, 75, 90 minutes

**Public Forum Debate Advanced** (Coach Marcus)
- 10 sessions total
- Sessions 1-7: completed (session 8: cancelled, 9-10: scheduled)
- Students: Noah, Zara, Emma
- Session durations vary: 45, 60, 75, 90 minutes

**Congressional Debate Workshop** (Coach Sarah)
- 8 sessions total
- Sessions 1-6: completed (7-8: scheduled)
- Students: Anika, Noah
- Session durations vary: 60, 75, 90 minutes
