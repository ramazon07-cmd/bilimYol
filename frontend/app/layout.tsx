import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RBIS — Academic Diagnostic",
  description:
    "RBIS o‘quvchilari uchun diagnostika, natijalar va shaxsiy o‘quv yo‘li.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz">
      <body>{children}</body>
    </html>
  );
}
