"use client";
import { useState } from "react";
import {
  ReloadButton,
  ExtractAllButton,
  VectorizeAllButton,
  CategorySelect,
  DateRangeFilter,
  NewsletterTable,
  Sidebar,
  ChatPanel,
} from "@/components";
import { useFilters } from "@/hooks";

export default function EmailsPage() {
  const [cat, setCat] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const { data, isFetching } = useFilters(cat, start, end);

  return (
    <div className="flex w-full h-screen overflow-hidden">
      <div className="w-[15%]">
        <Sidebar />
      </div>
      <div className="flex flex-1 h-full">
        <div className="w-1/2 space-y-4 p-4 overflow-y-auto h-full">
          <p className="italic text-rose-900 text-center font-semibold mb-2">
            &quot;Do what you know best, trust yourself&quot;
          </p>
          {isFetching && <p>Loading emails…</p>}
          {data && <NewsletterTable data={data} />}
        </div>
        <div className="w-1/2 flex flex-col h-full">
          <div className=" flex max-h-[6vh] items-center gap-4 p-2 border-b bg-white/75 backdrop-blur sticky top-0">
            <CategorySelect value={cat} onChange={setCat} />
            <DateRangeFilter
              start={start}
              end={end}
              onChangeStart={setStart}
              onChangeEnd={setEnd}
            />
            <ReloadButton />
            <ExtractAllButton />
            <VectorizeAllButton />
          </div>
          <div className="flex-1">
            <ChatPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
