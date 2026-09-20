"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import type { PaginatedResponse, SessionFeedback } from "@/lib/types";
import DashboardCard from "./DashboardCard";

interface FeedbackHistoryCardProps {
  refreshTrigger?: number;
}

export default function FeedbackHistoryCard({ refreshTrigger }: FeedbackHistoryCardProps) {
  const { user } = useAuth();
  const [feedbacks, setFeedbacks] = useState<SessionFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchHistory = useCallback(() => {
    setLoading(true);
    setError("");
    api
      .get<PaginatedResponse<SessionFeedback>>("/feedback/my/")
      .then((res) => setFeedbacks(res.results))
      .catch(() => setError("Could not load feedback history."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory, refreshTrigger]);

  if (loading) {
    return (
      <DashboardCard title="Feedback History">
        <p className="text-sm text-gray-400">Loading history...</p>
      </DashboardCard>
    );
  }

  if (error) {
    return (
      <DashboardCard title="Feedback History">
        <p className="text-sm text-red-500">{error}</p>
      </DashboardCard>
    );
  }

  if (feedbacks.length === 0) {
    return (
      <DashboardCard title="Feedback History">
        <p className="text-sm text-gray-500">No feedback submitted yet.</p>
      </DashboardCard>
    );
  }

  const renderFeedbackItem = (item: SessionFeedback) => (
    <li key={item.id} className="space-y-2 px-5 py-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-900">{item.class_name}</p>
          <p className="text-xs text-gray-500">
            Session: {new Date(item.session_date).toLocaleDateString()}
          </p>
        </div>
        <span className="text-xs text-gray-400">
          {new Date(item.created_at).toLocaleDateString()}
        </span>
      </div>

      {/* Ratings Badges */}
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded bg-blue-50 px-2 py-0.5 font-medium text-cda-blue">
          Clarity: {item.rating_clarity}/5
        </span>
        <span className="rounded bg-mint/20 px-2 py-0.5 font-medium text-cda-navy">
          Engagement: {item.rating_engagement}/5
        </span>
        <span className="rounded bg-amber-50 px-2 py-0.5 font-medium text-amber-800">
          Pacing: {item.rating_pace}/5
        </span>
      </div>

      {/* Optional Note */}
      {item.notes && (
        <p className="rounded bg-gray-50 p-2 text-xs italic text-gray-600">
          &ldquo;{item.notes}&rdquo;
        </p>
      )}
    </li>
  );

  // If Parent: Group by linked student
  if (user?.role === "parent") {
    // Group feedbacks by student display name
    const grouped = feedbacks.reduce<Record<string, SessionFeedback[]>>((acc, fb) => {
      const studentName = fb.student_display?.display_name || `Student #${fb.student}`;
      if (!acc[studentName]) acc[studentName] = [];
      acc[studentName].push(fb);
      return acc;
    }, {});

    return (
      <DashboardCard
        title="Feedback History"
        subtitle={`${feedbacks.length} review${feedbacks.length !== 1 ? "s" : ""} across linked students`}
        flush
      >
        <div className="divide-y divide-gray-200">
          {Object.entries(grouped).map(([studentName, studentFeedbacks]) => (
            <div key={studentName}>
              <div className="bg-gray-50 px-5 py-1.5 text-xs font-semibold text-cda-navy">
                {studentName} ({studentFeedbacks.length})
              </div>
              <ul className="divide-y divide-gray-100">
                {studentFeedbacks.map(renderFeedbackItem)}
              </ul>
            </div>
          ))}
        </div>
      </DashboardCard>
    );
  }

  // Student view: simple list
  return (
    <DashboardCard
      title="Feedback History"
      subtitle={`${feedbacks.length} submitted review${feedbacks.length !== 1 ? "s" : ""}`}
      flush
    >
      <ul className="divide-y divide-gray-100">
        {feedbacks.map(renderFeedbackItem)}
      </ul>
    </DashboardCard>
  );
}