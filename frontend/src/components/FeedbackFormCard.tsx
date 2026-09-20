"use client";

import { useEffect, useState, FormEvent } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { api, ApiError } from "@/lib/api";
import type { EligibleSession } from "@/lib/types";
import DashboardCard from "./DashboardCard";

interface FeedbackFormCardProps {
  onFeedbackSubmitted?: () => void;
}

export default function FeedbackFormCard({ onFeedbackSubmitted }: FeedbackFormCardProps) {
  const { user } = useAuth();

  // Selected student (for parents)
  const [selectedStudentId, setSelectedStudentId] = useState<number | "">("");

  // Sessions eligible for review
  const [eligibleSessions, setEligibleSessions] = useState<EligibleSession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<number | "">("");

  // Rating dimensions (1 to 5)
  const [ratingClarity, setRatingClarity] = useState<number>(5);
  const [ratingEngagement, setRatingEngagement] = useState<number>(5);
  const [ratingPace, setRatingPace] = useState<number>(5);
  const [notes, setNotes] = useState("");

  // Status & error handling
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Initialize selected student for parents
  useEffect(() => {
    if (user?.role === "parent" && user.family_links && user.family_links.length > 0) {
      setSelectedStudentId(user.family_links[0].student);
    }
  }, [user]);

  // Load eligible sessions whenever selected student changes (or on mount for students)
  useEffect(() => {
    if (!user) return;

    let path = "/feedback/eligible-sessions/";
    if (user.role === "parent") {
      if (!selectedStudentId) {
        setEligibleSessions([]);
        return;
      }
      path += `?student_id=${selectedStudentId}`;
    }

    setLoadingSessions(true);
    setErrorMessage("");
    api
      .get<EligibleSession[]>(path)
      .then((sessions) => {
        setEligibleSessions(sessions);
        setSelectedSessionId(sessions.length > 0 ? sessions[0].id : "");
      })
      .catch(() => {
        setErrorMessage("Could not load eligible sessions.");
      })
      .finally(() => setLoadingSessions(false));
  }, [user, selectedStudentId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedSessionId) {
      setErrorMessage("Please select a session to review.");
      return;
    }

    setSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    const payload: Record<string, unknown> = {
      session: selectedSessionId,
      rating_clarity: ratingClarity,
      rating_engagement: ratingEngagement,
      rating_pace: ratingPace,
      notes: notes.trim(),
    };

    if (user?.role === "parent") {
      payload.student = selectedStudentId;
    }

    // Optimistic UI: remember submitted session to remove it from list
    const sessionToRemove = selectedSessionId;

    try {
      await api.post("/feedback/", payload);
      setSuccessMessage("Thank you! Feedback submitted successfully.");
      setNotes("");

      // Optimistically remove session from eligible list
      const updated = eligibleSessions.filter((s) => s.id !== sessionToRemove);
      setEligibleSessions(updated);
      setSelectedSessionId(updated.length > 0 ? updated[0].id : "");

      // Notify parent to refresh history
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (err) {
      if (err instanceof ApiError && err.body) {
        const errors = err.body;
        if (errors.non_field_errors) {
          setErrorMessage((errors.non_field_errors as string[]).join(" "));
        } else if (errors.session) {
          setErrorMessage((errors.session as string[]).join(" "));
        } else if (errors.student) {
          setErrorMessage((errors.student as string[]).join(" "));
        } else {
          setErrorMessage("Failed to submit feedback. Please check your inputs.");
        }
      } else {
        setErrorMessage("An unexpected error occurred. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderRatingButtons = (
    label: string,
    value: number,
    onChange: (val: number) => void
  ) => (
    <div>
      <label className="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
        <span>{label}</span>
        <span className="font-semibold text-cda-navy">{value} / 5</span>
      </label>
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-colors ${
              value >= star
                ? "bg-cda-navy text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            ★ {star}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <DashboardCard title="Leave Session Feedback" subtitle="Share your thoughts on recent classes">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Parent child selector */}
        {user?.role === "parent" && user.family_links && user.family_links.length > 0 && (
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">
              Submitting for Student
            </label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(Number(e.target.value))}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-cda-blue focus:outline-none focus:ring-1 focus:ring-cda-blue"
            >
              {user.family_links.map((link) => (
                <option key={link.student} value={link.student}>
                  {link.student_display.display_name} ({link.relationship})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Eligible Session Dropdown */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-700">
            Select Completed Session
          </label>
          {loadingSessions ? (
            <p className="text-xs text-gray-400">Loading sessions...</p>
          ) : eligibleSessions.length === 0 ? (
            <p className="rounded-md bg-gray-50 p-3 text-xs text-gray-500">
              No sessions eligible for feedback at this time (must be completed within the last 30 days and not yet reviewed).
            </p>
          ) : (
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(Number(e.target.value))}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-cda-blue focus:outline-none focus:ring-1 focus:ring-cda-blue"
              required
            >
              {eligibleSessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.class_name} — {new Date(session.scheduled_date).toLocaleDateString()}
                  {session.topic ? ` (${session.topic})` : ""}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Rating Dimensions */}
        {eligibleSessions.length > 0 && (
          <>
            <div className="space-y-3 pt-2">
              {renderRatingButtons("Clarity of Explanation", ratingClarity, setRatingClarity)}
              {renderRatingButtons("Session Engagement", ratingEngagement, setRatingEngagement)}
              {renderRatingButtons("Class Pacing", ratingPace, setRatingPace)}
            </div>

            {/* Note Area with 500-char counter */}
            <div>
              <div className="mb-1 flex justify-between text-xs">
                <label className="font-medium text-gray-700">Optional Note</label>
                <span className={notes.length > 450 ? "text-amber-600" : "text-gray-400"}>
                  {notes.length} / 500
                </span>
              </div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                maxLength={500}
                rows={3}
                placeholder="What went well? Any areas for improvement?"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-cda-blue focus:outline-none focus:ring-1 focus:ring-cda-blue"
              />
            </div>

            {/* Messages */}
            {errorMessage && (
              <p className="rounded-md bg-red-50 p-2 text-xs text-red-600">{errorMessage}</p>
            )}
            {successMessage && (
              <p className="rounded-md bg-green-50 p-2 text-xs text-green-700">{successMessage}</p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-md bg-cda-navy px-4 py-2 text-sm font-medium text-white hover:bg-cda-navy/90 disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Submit Feedback"}
            </button>
          </>
        )}
      </form>
    </DashboardCard>
  );
}