// src/app/page.tsx
"use client";
import { useState } from "react";
import ReloadButton from "@/components/ReloadButton";
import CategorySelect from "@/components/CategorySelect";
import NewsletterTable from "@/components/NewsletterTable";
import { useCategory } from "@/hooks/useIngest";

export default function Home() {
  const [cat, setCat] = useState("");
  const { data, isFetching } = useCategory(cat);

  return (
    <div className="max-w-4xl mx-auto py-10 space-y-6">
      <h1 className="text-3xl font-semibold">Hitherto Dashboard</h1>

      <div className="flex gap-4">
        <ReloadButton />
        <CategorySelect value={cat} onChange={setCat} />
      </div>

      {isFetching && <p>Loading…</p>}
      {data && <NewsletterTable data={data} />}
    </div>
  );
}
