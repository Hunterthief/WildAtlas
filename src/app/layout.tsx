import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { Providers } from "@/components/providers";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  weight: ["500", "600"],
  style: ["italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "WildAtlas | Discover the Animal Kingdom",
  description:
    "Explore beautiful, richly-detailed facts about animals from around the world. An animal encyclopedia inspired by Facts.app.",
  keywords: [
    "WildAtlas",
    "animals",
    "animal encyclopedia",
    "wildlife",
    "facts",
    "nature",
  ],
  authors: [{ name: "WildAtlas Project" }],
  openGraph: {
    title: "WildAtlas | Discover the Animal Kingdom",
    description:
      "Explore beautiful, richly-detailed facts about animals from around the world.",
    siteName: "WildAtlas",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "WildAtlas | Discover the Animal Kingdom",
    description:
      "Explore beautiful, richly-detailed facts about animals from around the world.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${playfair.variable} antialiased bg-background text-foreground`}
      >
        <Providers>{children}</Providers>
        <Toaster />
      </body>
    </html>
  );
}
