"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import ActiveClassesCard from "@/components/ActiveClassesCard";
import ProfileCard from "@/components/ProfileCard";
import FeedbackFormCard from "@/components/FeedbackFormCard";
import FeedbackHistoryCard from "@/components/FeedbackHistoryCard";
import InstructorSummaryCard from "@/components/InstructorSummaryCard";

/**
 * myCDA Dashboard
 *
 * Cards are rendered based on the user's role.
 */
export default function DashboardPage() {
  const { user } = useAuth();
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState(0);

  if (!user) return null;

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold text-gray-900">Dashboard</h1>
      <p className="mb-6 text-sm text-gray-500">
        Welcome back, {user.display_name}
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Visible to everyone */}
        <ActiveClassesCard />
        <ProfileCard />

        {/* Students & Parents: Form & History Cards */}
        {(user.role === "student" || user.role === "parent") && (
          <>
            <FeedbackFormCard
              onFeedbackSubmitted={() => setHistoryRefreshTrigger((prev) => prev + 1)}
            />
            <FeedbackHistoryCard refreshTrigger={historyRefreshTrigger} />
          </>
        )}

        {/* Instructors & Admins: Aggregated Summary Card */}
        {(user.role === "instructor" || user.role === "admin") && (
          <InstructorSummaryCard />
        )}
      </div>
    </div>
  );
}