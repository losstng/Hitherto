"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import ReloadButton from "./ReloadButton";

export default function Sidebar() {
  const pathname = usePathname();
  const [auth, setAuth] = useState<boolean | null>(null);

  useEffect(() => {
    async function check() {
      try {
        const res = await fetch("/auth/status");
        const json = await res.json();
        setAuth(!!json.authenticated);
      } catch {
        setAuth(false);
      }
    }
    check();
  }, []);

  const nav = [
    { label: "Dashboard", route: "/dashboard", icon: "📊" },
    { label: "Extracted", route: "/extracted", icon: "🧾" },
    { label: "Chunked", route: "/chunked", icon: "🔖" },
    { label: "Embeddings", route: "/embeddings", icon: "🧠" },
    { label: "All Newsletters", route: "/newsletters", icon: "📬" },
  ];

  return (
    <aside className="fixed inset-y-0 left-0 w-60 bg-gray-100 shadow-md flex flex-col justify-between p-4">
      <div>
        <div className="text-center font-bold text-xl tracking-wide">
          <span className="inline-flex items-center gap-2">
            <img src="/bloomberg.svg" className="h-6 w-6" alt="" />
            Hitherto Digest
          </span>
          <div className="bg-red-500 text-white p-8">If this isn't red, Tailwind is dead.</div>
        </div>
        <nav className="flex flex-col gap-y-2 mt-6">
          {nav.map((item) => (
            <Link
              key={item.route}
              href={item.route}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === item.route
                  ? "font-semibold underline"
                  : "hover:bg-gray-200 active:bg-gray-300"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="mt-auto space-y-3">
        <ReloadButton />
        <div className="text-sm">
          {auth === null
            ? "Checking…"
            : auth
            ? "🔓 Authenticated"
            : "🔒 Not Authenticated"}
        </div>
        <Link href="/settings" className="text-sm hover:underline">
          ⚙️ Settings
        </Link>
      </div>
    </aside>
  );
}
