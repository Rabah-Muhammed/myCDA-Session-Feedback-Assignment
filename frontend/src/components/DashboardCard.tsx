"use client";

import type { ReactNode } from "react";

interface DashboardCardProps {
  title: string;
  /** Optional subtitle shown in lighter text next to the title */
  subtitle?: string;
  /** Optional action element (button/link) rendered in the card header */
  action?: ReactNode;
  children: ReactNode;
  /** If true, the card body has no padding (useful for tables/lists) */
  flush?: boolean;
}

/**
 * Standard card wrapper for the myCDA dashboard.
 *
 * All dashboard cards should use this component for consistent styling.
 * Do not create one-off card containers -- wrap your content in this.
 *
 * Usage:
 *   <DashboardCard title="My Card" subtitle="3 items">
 *     <p>Card content here</p>
 *   </DashboardCard>
 */
export default function DashboardCard({
  title,
  subtitle,
  action,
  children,
  flush = false,
}: DashboardCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          {subtitle && (
            <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>

      {/* Body */}
      <div className={flush ? "" : "px-5 py-4"}>{children}</div>
    </div>
  );
}
