"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import type { InstructorSummary } from "@/lib/types";
import DashboardCard from "./DashboardCard";

export default function InstructorSummaryCard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<InstructorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // For Admin switching between instructors
  const [selectedInstructorId, setSelectedInstructorId] = useState<number>(2); // Default to Sarah (ID: 2)

  useEffect(() => {
    if (!user) return;

    let path = "/feedback/instructor-summary/";
    if (user.role === "admin") {
      path += `?instructor_id=${selectedInstructorId}`;
    }

    setLoading(true);
    setError("");
    api
      .get<InstructorSummary>(path)
      .then(setSummary)
      .catch(() => setError("Could not load instructor feedback summary."))
      .finally(() => setLoading(false));
  }, [user, selectedInstructorId]);

  if (loading) {
    return (
      <DashboardCard title="Feedback Performance Summary">
        <p className="text-sm text-gray-400">Computing rolling averages...</p>
      </DashboardCard>
    );
  }

  if (error) {
    return (
      <DashboardCard title="Feedback Performance Summary">
        <p className="text-sm text-red-500">{error}</p>
      </DashboardCard>
    );
  }

  if (!summary || summary.total_feedback_count === 0) {
    return (
      <DashboardCard
        title="Feedback Performance Summary"
        subtitle="Duration-weighted rolling scores"
      >
        <div className="space-y-3">
          {user?.role === "admin" && (
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-600">Instructor:</label>
              <select
                value={selectedInstructorId}
                onChange={(e) => setSelectedInstructorId(Number(e.target.value))}
                className="rounded border border-gray-200 px-2 py-1 text-xs"
              >
                <option value={2}>Coach Sarah Chen</option>
                <option value={3}>Coach Marcus Rivera</option>
              </select>
            </div>
          )}
          <p className="text-sm text-gray-500">
            No feedback entries received yet for recent completed sessions.
          </p>
        </div>
      </DashboardCard>
    );
  }

  const renderMetricBar = (label: string, score: number, colorClass: string) => {
    const percentage = Math.min(Math.max((score / 5.0) * 100, 0), 100);
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-xs font-medium">
          <span className="text-gray-700">{label}</span>
          <span className="font-semibold text-gray-900">{score.toFixed(2)} / 5.00</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
          <div
            className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <DashboardCard
      title="Feedback Performance Summary"
      subtitle={`Based on last 10 completed sessions (${summary.total_feedback_count} reviews across ${summary.sessions_evaluated} sessions)`}
    >
      <div className="space-y-5">
        {/* Admin Instructor Selector */}
        {user?.role === "admin" && (
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <span className="text-xs font-medium text-gray-500">Evaluating Instructor:</span>
            <select
              value={selectedInstructorId}
              onChange={(e) => setSelectedInstructorId(Number(e.target.value))}
              className="rounded-md border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-900 focus:outline-none"
            >
              <option value={2}>Coach Sarah Chen</option>
              <option value={3}>Coach Marcus Rivera</option>
            </select>
          </div>
        )}

        {/* Overall Score Highlight */}
        <div className="flex items-center justify-between rounded-lg bg-gray-50 p-4 border border-gray-100">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Overall Weighted Average
            </p>
            <p className="text-2xl font-bold text-cda-navy">
              {summary.overall_avg.toFixed(2)}{" "}
              <span className="text-xs font-normal text-gray-400">/ 5.00</span>
            </p>
          </div>
          <div className="text-right">
            <span className="inline-flex items-center rounded-full bg-cda-mint/20 px-2.5 py-1 text-xs font-semibold text-cda-navy">
              Weighted by duration
            </span>
          </div>
        </div>

        {/* Dimension Metric Bars */}
        <div className="space-y-3">
          {renderMetricBar("Concept Clarity", summary.clarity_avg, "bg-cda-blue")}
          {renderMetricBar("Student Engagement", summary.engagement_avg, "bg-cda-mint")}
          {renderMetricBar("Pacing & Rhythm", summary.pace_avg, "bg-cda-gold")}
        </div>

        {/* Anonymity Note */}
        <div className="rounded border border-blue-100 bg-blue-50/50 p-2.5 text-center text-xs text-cda-blue">
          🔒 Anonymized and aggregated. Individual student identities and raw notes are never shared.
        </div>
      </div>
    </DashboardCard>
  );
}