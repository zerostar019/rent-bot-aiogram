"use client";
import SideBar from "@/app/components/Layout/SideBar/SideBar";
import styles from "./styles.module.scss";
import { TelegramProvider } from "@/app/contexts/TelegramWebProvider";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <TelegramProvider>
      <div className={styles["dashboard-layout"]}>
        <SideBar className={styles["sidebar-position"]} />
        {children}
      </div>
    </TelegramProvider>
  );
}
