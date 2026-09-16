"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ClassItem, PaginatedResponse } from "@/lib/types";
import DashboardCard from "./DashboardCard";

export default function ActiveClassesCard() {
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<PaginatedResponse<ClassItem>>("/classes/")
      .then((res) => setClasses(res.results))
      .catch(() => setError("Could not load classes."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardCard title="Active Classes">
        <p className="text-sm text-gray-400">Loading...</p>
      </DashboardCard>
    );
  }

  if (error) {
    return (
      <DashboardCard title="Active Classes">
        <p className="text-sm text-red-500">{error}</p>
      </DashboardCard>
    );
  }

  if (classes.length === 0) {
    return (
      <DashboardCard title="Active Classes">
        <p className="text-sm text-gray-500">No active classes found.</p>
      </DashboardCard>
    );
  }

  return (
    <DashboardCard
      title="Active Classes"
      subtitle={`${classes.length} class${classes.length !== 1 ? "es" : ""}`}
      flush
    >
      <ul className="divide-y divide-gray-100">
        {classes.map((cls) => (
          <li key={cls.id} className="flex items-center justify-between px-5 py-3">
            <div>
              <p className="text-sm font-medium text-gray-900">{cls.name}</p>
              <p className="text-xs text-gray-500">
                {cls.instructor_display.display_name}
              </p>
            </div>
            <span className="rounded-full bg-cda-mint/20 px-2 py-0.5 text-xs font-medium text-cda-navy">
              {cls.student_count} student{cls.student_count !== 1 ? "s" : ""}
            </span>
          </li>
        ))}
      </ul>
    </DashboardCard>
  );
}
