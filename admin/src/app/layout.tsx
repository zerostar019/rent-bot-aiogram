import { AntdRegistry } from "@ant-design/nextjs-registry";
import "./styles/globals.css";
import "./styles/reset.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html>
      <body>
        <AntdRegistry>
          {children}
        </AntdRegistry>
      </body>
    </html>
  );
}
