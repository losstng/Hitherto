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
          <Sidebar />
          <main className="ml-56 flex-1 overflow-y-auto p-4">{children}</main>
          <ChatPanel />
        </Providers>
      </body>
    </html>
  );
}