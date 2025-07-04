// src/app/layout.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import "@/styles/globals.css";
import Providers from "@/components/Providers";

export const metadata = { title: "Hitherto" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}