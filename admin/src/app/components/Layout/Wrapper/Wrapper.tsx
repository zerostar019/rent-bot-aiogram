"use client";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { App, ConfigProvider, theme } from "antd";
import locale from "antd/locale/ru_RU";
import dayjs from "dayjs";
import "dayjs/locale/ru";

// Ant Design локализован через ConfigProvider, но dayjs держит локаль
// глобально и по умолчанию форматировал даты по-английски.
dayjs.locale("ru");

/**
 * Тема Ant Design приведена к тем же токенам, что и остальной интерфейс.
 * Без этого дефолтный синий AntD спорил с акцентом панели.
 */
const antdTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#15665a",
    colorInfo: "#15665a",
    colorSuccess: "#3f7d4e",
    colorWarning: "#9a6a1b",
    colorError: "#b4402f",

    colorText: "#1c1b18",
    colorTextSecondary: "#6a655c",
    colorTextTertiary: "#9a948a",
    colorBorder: "#d6d2c8",
    colorBorderSecondary: "#e7e4dd",
    colorBgLayout: "#f7f6f3",
    colorBgContainer: "#ffffff",
    colorBgElevated: "#ffffff",

    borderRadius: 12,
    borderRadiusLG: 16,
    borderRadiusSM: 8,

    fontFamily: "var(--font-sans), ui-sans-serif, system-ui, sans-serif",
    fontSize: 14,
    controlHeight: 38,
    wireframe: false,
  },
  components: {
    Button: { fontWeight: 500, primaryShadow: "none", defaultShadow: "none" },
    Card: { boxShadowTertiary: "0 1px 3px rgba(48,42,32,0.07)" },
    Input: { activeShadow: "0 0 0 3px rgba(21,102,90,0.16)" },
    Table: { headerBg: "#f7f6f3", headerColor: "#6a655c", rowHoverBg: "#faf9f6" },
    Badge: { textFontSize: 11, textFontWeight: 600 },
  },
};

const Wrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <AntdRegistry>
      <ConfigProvider locale={locale} theme={antdTheme}>
        <App>{children}</App>
      </ConfigProvider>
    </AntdRegistry>
  );
};

export default Wrapper;
