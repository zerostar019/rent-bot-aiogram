"use client";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { ConfigProvider } from "antd";
import locale from "antd/locale/ru_RU";

const Wrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <AntdRegistry>
      <ConfigProvider locale={locale}>{children}</ConfigProvider>
    </AntdRegistry>
  );
};

export default Wrapper;
