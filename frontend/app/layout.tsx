import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "SKU Lifecycle Tracker",
  description: "Search any SKU and inspect its timeline.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
