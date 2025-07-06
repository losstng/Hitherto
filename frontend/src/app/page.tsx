"use client";
import { useState } from "react";
import ReloadButton from "@/components/ReloadButton";
import CategorySelect from "@/components/CategorySelect";
import NewsletterTable from "@/components/NewsletterTable";
import { useCategory } from "@/hooks/useIngest";

export default function EmailsPage() {
  const [cat, setCat] = useState("");
  const { data, isFetching } = useCategory(cat);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 sticky top-0 bg-white/75 backdrop-blur p-2 border-b">
        <CategorySelect value={cat} onChange={setCat} />
        <ReloadButton />
      </div>
      {isFetching && <p>Loading emails…</p>}
      {data && <NewsletterTable data={data} />}
    </div>
  );
}
