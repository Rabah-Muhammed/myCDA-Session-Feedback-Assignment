"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import type { UserRole } from "@/lib/types";

interface NavItem {
  label: string;
  href: string;
  roles: UserRole[];
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    roles: ["admin", "instructor", "parent", "student"],
  },
  // Candidates: add your feedback-related nav items here.
  // Follow the same pattern -- label, href, and which roles can see it.
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  if (!user) return null;

  const visibleItems = NAV_ITEMS.filter((item) =>
    item.roles.includes(user.role)
  );

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex h-14 items-center border-b border-gray-200 px-4">
        <span className="text-lg font-semibold text-cda-navy">myCDA</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {visibleItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-cda-navy/10 text-cda-navy"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User info + logout */}
      <div className="border-t border-gray-200 px-4 py-3">
        <p className="text-sm font-medium text-gray-900">
          {user.display_name}
        </p>
        <p className="text-xs text-gray-500 capitalize">{user.role}</p>
        <button
          onClick={logout}
          className="mt-2 text-xs text-gray-400 hover:text-red-600"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
