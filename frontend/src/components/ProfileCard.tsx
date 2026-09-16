"use client";

import { useAuth } from "@/contexts/AuthContext";
import DashboardCard from "./DashboardCard";

export default function ProfileCard() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <DashboardCard title="Profile">
      <div className="space-y-2">
        <div>
          <p className="text-xs text-gray-500">Name</p>
          <p className="text-sm font-medium">
            {user.first_name} {user.last_name}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Email</p>
          <p className="text-sm">{user.email}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Role</p>
          <p className="text-sm capitalize">{user.role}</p>
        </div>

        {/* Parent-specific: show linked students */}
        {user.family_links && user.family_links.length > 0 && (
          <div>
            <p className="text-xs text-gray-500">Linked Students</p>
            <ul className="mt-1 space-y-1">
              {user.family_links.map((link) => (
                <li key={link.id} className="text-sm">
                  {link.student_display.display_name}
                  <span className="ml-1 text-xs text-gray-400">
                    ({link.relationship})
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </DashboardCard>
  );
}
