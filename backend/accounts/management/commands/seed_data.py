"""
Seed the database with test data for the feedback assignment.

Usage: python manage.py seed_data

Creates:
- 1 admin, 2 instructors, 3 parents, 5 students
- 3 classes with enrollments
- ~30 sessions across classes (mix of completed, scheduled, cancelled)
- Family links between parents and students

Does NOT create any feedback entries -- that's the candidate's job to test.
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from accounts.models import User, FamilyLink
from classes.models import Class, ClassEnrollment, Session


class Command(BaseCommand):
    help = "Seed the database with test data"

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing data...")
        Session.objects.all().delete()
        ClassEnrollment.objects.all().delete()
        Class.objects.all().delete()
        FamilyLink.objects.all().delete()
        Token.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        now = timezone.now()

        # ---- Users ----

        self.stdout.write("Creating users...")

        admin = self._create_user(
            "admin", "admin@cda.test", "Admin", "User", "admin", "testpass123"
        )
        sarah = self._create_user(
            "coach.sarah", "coach.sarah@cda.test",
            "Sarah", "Chen", "instructor", "testpass123",
        )
        marcus = self._create_user(
            "coach.marcus", "coach.marcus@cda.test",
            "Marcus", "Rivera", "instructor", "testpass123",
        )
        james = self._create_user(
            "parent.james", "parent.james@cda.test",
            "James", "Wilson", "parent", "testpass123",
        )
        priya = self._create_user(
            "parent.priya", "parent.priya@cda.test",
            "Priya", "Sharma", "parent", "testpass123",
        )
        david = self._create_user(
            "parent.david", "parent.david@cda.test",
            "David", "Brown", "parent", "testpass123",
        )
        emma = self._create_user(
            "student.emma", "student.emma@cda.test",
            "Emma", "Wilson", "student", "testpass123",
        )
        liam = self._create_user(
            "student.liam", "student.liam@cda.test",
            "Liam", "Wilson", "student", "testpass123",
        )
        anika = self._create_user(
            "student.anika", "student.anika@cda.test",
            "Anika", "Sharma", "student", "testpass123",
        )
        noah = self._create_user(
            "student.noah", "student.noah@cda.test",
            "Noah", "Brown", "student", "testpass123",
        )
        zara = self._create_user(
            "student.zara", "student.zara@cda.test",
            "Zara", "Adams", "student", "testpass123",
        )

        # ---- Family Links ----

        self.stdout.write("Creating family links...")

        # James Wilson is parent of Emma and Liam Wilson
        FamilyLink.objects.create(parent=james, student=emma, relationship="parent")
        FamilyLink.objects.create(parent=james, student=liam, relationship="parent")

        # Priya Sharma is parent of Anika Sharma
        FamilyLink.objects.create(parent=priya, student=anika, relationship="parent")

        # David Brown is parent of Noah Brown
        FamilyLink.objects.create(parent=david, student=noah, relationship="parent")

        # Zara Adams has no parent linked (tests edge case)

        # ---- Classes ----

        self.stdout.write("Creating classes...")

        ld_class = Class.objects.create(
            name="Lincoln-Douglas Debate Fundamentals",
            description="Foundation course covering LD debate structure, values, and case writing.",
            instructor=sarah,
            is_active=True,
            created_by=admin,
        )
        pf_class = Class.objects.create(
            name="Public Forum Debate Advanced",
            description="Advanced PF strategies, crossfire techniques, and evidence handling.",
            instructor=marcus,
            is_active=True,
            created_by=admin,
        )
        congress_class = Class.objects.create(
            name="Congressional Debate Workshop",
            description="Bill analysis, speechwriting, and parliamentary procedure.",
            instructor=sarah,
            is_active=True,
            created_by=admin,
        )

        # ---- Enrollments ----

        self.stdout.write("Creating enrollments...")

        # LD: Emma, Liam, Anika
        for student in [emma, liam, anika]:
            ClassEnrollment.objects.create(class_obj=ld_class, student=student)

        # PF: Noah, Zara, Emma (Emma is in two classes)
        for student in [noah, zara, emma]:
            ClassEnrollment.objects.create(class_obj=pf_class, student=student)

        # Congress: Anika, Noah
        for student in [anika, noah]:
            ClassEnrollment.objects.create(class_obj=congress_class, student=student)

        # ---- Sessions ----

        self.stdout.write("Creating sessions...")

        # LD class sessions -- 12 sessions, mix of statuses
        ld_topics = [
            ("Introduction to LD format", 60),
            ("Value and criterion selection", 75),
            ("Case structure workshop", 90),
            ("Cross-examination techniques", 60),
            ("Refutation and rebuttal", 75),
            ("Flowing and time management", 60),
            ("Practice round: Privacy vs Security", 90),
            ("Feedback and improvement plans", 45),
            ("Advanced value debate", 75),
            ("Tournament preparation", 90),
            ("Mock tournament round 1", 90),
            ("Mock tournament round 2", 90),
        ]

        for i, (topic, duration) in enumerate(ld_topics):
            days_ago = (len(ld_topics) - i) * 7  # Weekly sessions going back
            if i < 8:
                status = "completed"
            elif i < 10:
                status = "completed"
            elif i == 10:
                status = "scheduled"  # Future
            else:
                status = "scheduled"

            # Make one session cancelled
            if i == 5:
                status = "cancelled"

            # Make one session older than 30 days (the first few)
            Session.objects.create(
                class_obj=ld_class,
                scheduled_date=now - timedelta(days=days_ago),
                status=status,
                session_metadata={
                    "duration_minutes": duration,
                    "topic_covered": topic,
                    "location": "Room A",
                },
            )

        # PF class sessions -- 10 sessions
        pf_topics = [
            ("PF format overview", 60),
            ("Constructive speech writing", 75),
            ("Crossfire strategy", 60),
            ("Evidence standards and cutting", 90),
            ("Summary and final focus", 75),
            ("Speed drills and clarity", 45),
            ("Practice round: Economic policy", 90),
            ("Advanced rebuttal techniques", 60),
            ("Weighing and impact calculus", 75),
            ("Pre-tournament drill", 90),
        ]

        for i, (topic, duration) in enumerate(pf_topics):
            days_ago = (len(pf_topics) - i) * 7
            if i < 7:
                status = "completed"
            elif i == 7:
                status = "cancelled"
            else:
                status = "scheduled"

            Session.objects.create(
                class_obj=pf_class,
                scheduled_date=now - timedelta(days=days_ago),
                status=status,
                session_metadata={
                    "duration_minutes": duration,
                    "topic_covered": topic,
                    "location": "Room B",
                },
            )

        # Congress class sessions -- 8 sessions
        congress_topics = [
            ("Parliamentary procedure basics", 60),
            ("Bill analysis framework", 75),
            ("Authorship and sponsorship speeches", 60),
            ("Questioning and PO duties", 90),
            ("Amendment strategy", 75),
            ("Practice session: Education bill", 90),
            ("Practice session: Healthcare bill", 90),
            ("Scoring and presiding practice", 60),
        ]

        for i, (topic, duration) in enumerate(congress_topics):
            days_ago = (len(congress_topics) - i) * 7
            if i < 5:
                status = "completed"
            elif i == 5:
                status = "completed"
            else:
                status = "scheduled"

            Session.objects.create(
                class_obj=congress_class,
                scheduled_date=now - timedelta(days=days_ago),
                status=status,
                session_metadata={
                    "duration_minutes": duration,
                    "topic_covered": topic,
                    "location": "Room C",
                },
            )

        # ---- Tokens ----

        self.stdout.write("Creating auth tokens...")
        for user in User.objects.all():
            Token.objects.get_or_create(user=user)

        # ---- Summary ----

        total_users = User.objects.count()
        total_sessions = Session.objects.count()
        completed = Session.objects.filter(status="completed").count()
        scheduled = Session.objects.filter(status="scheduled").count()
        cancelled = Session.objects.filter(status="cancelled").count()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed complete!"
            f"\n  Users: {total_users}"
            f"\n  Classes: {Class.objects.count()}"
            f"\n  Enrollments: {ClassEnrollment.objects.count()}"
            f"\n  Family links: {FamilyLink.objects.count()}"
            f"\n  Sessions: {total_sessions} "
            f"(completed: {completed}, scheduled: {scheduled}, cancelled: {cancelled})"
            f"\n\nAll users have password: testpass123"
            f"\nSee TEST_ACCOUNTS.md for login details."
        ))

    def _create_user(self, username, email, first, last, role, password):
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            role=role,
            password=password,
        )
        return user
