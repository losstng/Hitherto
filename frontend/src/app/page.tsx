"use client";
import { useState } from "react";
import ReloadButton from "@/components/ReloadButton";
import CategorySelect from "@/components/CategorySelect";
import DateSelect from "@/components/DateSelect";
import NewsletterTable from "@/components/NewsletterTable";
import Sidebar from "@/components/Sidebar";
import ChatPanel from "@/components/ChatPanel";
import { useFilter } from "@/hooks/useIngest";

export default function EmailsPage() {
  const [cat, setCat] = useState("");
  const [date, setDate] = useState("");
  const { data, isFetching } = useFilter(cat, date);

  return (
    <div className="flex w-full h-screen overflow-hidden">
      <div className="w-[15%]">
        <Sidebar />
      </div>
      <div className="flex flex-1 h-full">
        <div className="w-1/2 space-y-4 p-4 overflow-y-auto h-full">
          {isFetching && <p>Loading emails…</p>}
          {data && <NewsletterTable data={data} />}
        </div>
        <div className="w-1/2 flex flex-col h-full">
          <div className="flex items-center gap-4 p-2 border-b bg-white/75 backdrop-blur sticky top-0">
            <CategorySelect value={cat} onChange={setCat} />
            <DateSelect value={date} onChange={setDate} />
            <ReloadButton />
          </div>
          <div className="flex-1">
            <ChatPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
