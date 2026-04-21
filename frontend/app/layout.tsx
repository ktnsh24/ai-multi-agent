import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Multi-Agent Platform",
  description:
    "Watch AI agents collaborate in real-time to research, analyze, write, and review",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
