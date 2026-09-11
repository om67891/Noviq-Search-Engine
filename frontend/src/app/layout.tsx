import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Noviq | Search. Verify. Discover.",
  description: "A secure, trust-aware AI search experience.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans`}>
        <header className="sticky top-0 z-50 w-full border-b border-gray-100 bg-white/80 backdrop-blur-md">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold tracking-tight text-[var(--color-navy-900)]">
                N<span className="gradient-text">o</span>vi<span className="relative">
                  q
                  <span className="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full gradient-bg"></span>
                </span>
              </span>
            </div>
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-[var(--color-text-secondary)]">
              <a href="#" className="hover:text-[var(--color-navy-900)] transition-colors">Search</a>
              <a href="#" className="hover:text-[var(--color-navy-900)] transition-colors">Research</a>
              <a href="#" className="hover:text-[var(--color-navy-900)] transition-colors">About</a>
            </nav>
            <div className="flex items-center">
              {/* Future: Auth/Settings buttons */}
            </div>
          </div>
        </header>
        <main className="flex-1 flex flex-col">
          {children}
        </main>
      </body>
    </html>
  );
}
