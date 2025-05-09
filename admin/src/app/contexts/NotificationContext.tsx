"use client";
import { createContext, Dispatch, SetStateAction, useState } from "react";

export interface NotificationContextType {
  text: string;
  isShow: boolean;
}

interface NotificationContextInterface {
  notif: NotificationContextType;
  setNotif: Dispatch<SetStateAction<NotificationContextType>>;
}

const initialNotifContext: NotificationContextInterface = {
  notif: {
    isShow: false,
    text: "",
  },
  setNotif: (() => {}) as Dispatch<SetStateAction<NotificationContextType>>,
};

export const NotificationContext =
  createContext<NotificationContextInterface>(initialNotifContext);

const NotificationProvider = ({ children }: { children: React.ReactNode }) => {
  const [notif, setNotif] = useState<NotificationContextType>(
    initialNotifContext.notif
  );
  return (
    <NotificationContext.Provider value={{ notif, setNotif }}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;
