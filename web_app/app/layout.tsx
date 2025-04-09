// app/layout.tsx
import { Inter } from "next/font/google";
import "./app.css";
import RootLayoutClient from "./layout-client";
import { metadata } from './metadata'; // assuming you have a metadata file

const inter = Inter({ subsets: ["latin"] });

export { metadata };

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <RootLayoutClient>
          {children}
        </RootLayoutClient>
      </body>
    </html>
  );
}
