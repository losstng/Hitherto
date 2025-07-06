// src/components/ReloadButton.tsx
"use client";
import { useReload } from "@/hooks/useIngest";

export default function ReloadButton() {
  const reload = useReload();
  return (
    <button
      className="py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-md"
      onClick={() => reload.mutate()}
      disabled={reload.isPending}
    >
      {reload.isPending ? "Reloading…" : "Reload"}
      
    </button>
  );
}
