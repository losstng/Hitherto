"use client";
import Sidebar from "@/components/Sidebar";
import Notebook from "@/components/notebook/Notebook";
import NotebookSidebar from "@/components/notebook/NotebookSidebar";
import { NotebookProvider } from "@/components/notebook/NotebookProvider";

export default function AnalyticsPage() {
  return (
    <div className="flex w-full h-screen overflow-hidden">
      <div className="w-[15%]">
        <Sidebar />
      </div>
      <NotebookProvider>
        <div className="flex flex-1">
          <div className="w-[20%]">
            <NotebookSidebar />
          </div>
          <div className="flex-1 overflow-y-auto">
            <Notebook />
          </div>
        </div>
      </NotebookProvider>
    </div>
  );
}

