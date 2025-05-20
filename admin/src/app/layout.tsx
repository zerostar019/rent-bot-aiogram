import Wrapper from "./components/Layout/Wrapper/Wrapper";
import "./styles/globals.css";
import "./styles/reset.css";
import { Metadata, Viewport } from "next";

export const viewport: Viewport = {
  initialScale: 1.0,
  width: "device-width",
  maximumScale: 1.0,
  minimumScale: 1.0,
  userScalable: false,
};

export const metadata: Metadata = {
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
    <html>
      <body>
        <Wrapper>{children}</Wrapper>
      </body>
    </html>
  );
}
