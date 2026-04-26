// Root layout for the Next.js app - provides HTML structure and global styles
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reddit & LinkedIn Discovery",
  description: "Automate Reddit engagement, Reddit and LinkedIn Posts discovery",
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
