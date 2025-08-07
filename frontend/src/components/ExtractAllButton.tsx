"use client";
import { useExtractAll } from "@/hooks";

export default function ExtractAllButton() {
  const extractAll = useExtractAll();
  return (
    <button
      className="py-2 px-4 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-md flex-shrink-0"
      onClick={() => extractAll.mutate()}
      disabled={extractAll.isPending}
    >
      {extractAll.isPending ? "Extracting…" : "Extract All"}
    </button>
  );
}
