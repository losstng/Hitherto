"use client";
import { useVectorizeAll } from "@/hooks/useIngest";

export default function VectorizeAllButton() {
  const vectorizeAll = useVectorizeAll();
  return (
    <button
      className="py-2 px-4 bg-purple-500 hover:bg-purple-600 text-white font-semibold rounded-md flex-shrink-0"
      onClick={() => vectorizeAll.mutate()}
      disabled={vectorizeAll.isPending}
    >
      {vectorizeAll.isPending ? "Vectorizing…" : "Vectorize All"}
    </button>
  );
}
