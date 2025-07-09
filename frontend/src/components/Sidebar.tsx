"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import StockPrices from "./StockPrices";

export default function Sidebar() {
  const pathname = usePathname();

  const { data, isLoading } = useQuery({
    queryKey: ["gmail_status"],
    queryFn: async () => {
      const { data } = await api.get("/ingest/gmail_status");
      return data.data.connected as boolean;
    },
  });

  const Status = () => (
    <div className="text-sm font-medium px-4 py-2 border-b">
      {isLoading ? "Checking…" : data ? "🟢 Gmail Connected" : "🔴 Gmail Disconnected"}
    </div>
  );

  return (
    <aside className="flex flex-col h-full w-full bg-gray-100 shadow">
      <Status />
      <StockPrices />
      <nav className="p-4 space-y-2">
        <Link
          href="/"
          className={`block px-3 py-2 rounded-md text-sm ${pathname === "/" ? "bg-white shadow" : "hover:bg-gray-200"}`}
        >
          Emails
        </Link>
      </nav>
    </aside>
  );
}
