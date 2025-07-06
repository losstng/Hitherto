// src/app/layout.tsx
import React from "react";
import "@/styles/globals.css";
import Providers from "@/components/Providers";
import Sidebar from "@/components/Sidebar";
import ChatPanel from "@/components/ChatPanel";

export const metadata = { title: "Hitherto" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 flex">
        <Providers>
          <div className="flex w-full">
            <div className="flex w-[80%]">
              <Sidebar />
              <main className="flex-1 overflow-y-auto p-4">{children}</main>
            </div>
            <ChatPanel />
          </div>
        </Providers>
      </body>
    </html>
  );
}