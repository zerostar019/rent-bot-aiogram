import Wrapper from "./components/Layout/Wrapper/Wrapper";
import "./styles/globals.css";
import "./styles/reset.css";
import { Metadata, Viewport } from "next";
import { Manrope, JetBrains_Mono } from "next/font/google";

// Manrope и JetBrains Mono поддерживают кириллицу — интерфейс русскоязычный.
const fontSans = Manrope({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const fontMono = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const viewport: Viewport = {
  initialScale: 1.0,
  width: "device-width",
  maximumScale: 1.0,
  minimumScale: 1.0,
  userScalable: false,
  themeColor: "#15665a",
};

export const metadata: Metadata = {
  title: {
    default: "Панель администратора",
    template: "%s · Панель администратора",
  },
  description:
    "Управление бронированиями, чатами с гостями и настройками апартаментов.",
  robots: { index: false, follow: false },
  other: {
    chrome: "nointentdetection",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${fontSans.variable} ${fontMono.variable}`}>
      <body>
        <Wrapper>{children}</Wrapper>
      </body>
    </html>
  );
}
