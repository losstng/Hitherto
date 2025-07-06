// src/pages/index.tsx
import { useState } from "react";
import ReloadButton     from "@/components/ReloadButton";
import CategorySelect   from "@/components/CategorySelect";
import NewsletterTable  from "@/components/NewsletterTable";
import { useCategory }  from "@/hooks/useIngest";

export default function Dashboard() {
  const [cat, setCat] = useState("");
  const { data, isFetching } = useCategory(cat);

  return (
    <main className="p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Hitherto – Dashboard</h1>

      <div className="flex gap-4">
        <ReloadButton />
        <CategorySelect value={cat} onChange={setCat} />
      </div>

      {isFetching && <p>Loading newsletters…</p>}
      {data && <NewsletterTable data={data} />}
    </main>
  );
}
