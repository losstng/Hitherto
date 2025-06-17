// src/components/ReloadButton.tsx
"use client";
import { useReload } from "@/hooks/useIngest";

export default function ReloadButton() {
  const reload = useReload();
  return (
    <button
      className="px-3 py-1 bg-indigo-600 text-white rounded"
      onClick={() => reload.mutate()}
      disabled={reload.isPending}
    >
      {reload.isPending ? "Reloading…" : "Reload Bloomberg"}
    </button>
  );
}
