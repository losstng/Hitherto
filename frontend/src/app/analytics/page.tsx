"use client";
import Sidebar from "@/components/Sidebar";
import Notebook from "@/components/notebook/Notebook";
import { NotebookProvider } from "@/components/notebook/NotebookProvider";

export default function AnalyticsPage() {
  return (
    <div className="flex w-full h-screen overflow-hidden">
      <div className="w-[15%]">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <NotebookProvider>
          <Notebook />
        </NotebookProvider>
      </div>
    </div>
  );
}

