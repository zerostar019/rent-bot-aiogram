"use client";
import { notification } from "antd";
import styles from "./styles.module.scss";
import ChatUsers from "@/app/components/Pages/Chat/ChatUsers";
import Chat from "@/app/components/Pages/Chat/Chat";
import { useEffect, useState } from "react";
import { ChatUsersInterface } from "@/app/types/Users";
import classNames from "classnames";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import useWebSocket from "@/app/hooks/useWebsocket";
import { DB_URL } from "@/app/constants";
import { init, isTMA, viewport } from "@telegram-apps/sdk";

export default function Page() {
  const [selectedUser, setSelectedUser] = useState<
    ChatUsersInterface | undefined
  >(undefined);
  const [api, contextHolder] = notification.useNotification();
  const [users, setUsers] = useState<Array<ChatUsersInterface>>([]);
  const { messages, sendMessage, setMessages, error, status } = useWebSocket(
    `${DB_URL}/chat`,
    selectedUser?.user_id,
    api,
    setSelectedUser,
    users,
    setUsers
  );

  const isMobile = useMediaQuery("(max-width: 1024px)");
  const hasSelection = Boolean(selectedUser?.user_id);

  useEffect(() => {
    let mounted = false;
    const initializeTelegramApp = async () => {
      if (!isTMA()) return;
      try {
        init();
        await viewport.mount();
        mounted = true;
        if (viewport.expand.isAvailable()) {
          viewport.expand();
        }
      } catch (e) {
        console.error("Ошибка инициализации Telegram Web App:", e);
      }
    };
    initializeTelegramApp();

    return () => {
      // Размонтируем только то, что действительно смонтировали:
      // безусловный вызов падал вне Telegram.
      if (mounted) {
        try {
          viewport.unmount();
        } catch {
          /* уже размонтирован */
        }
      }
    };
  }, []);

  // На мобильном показываем одну из панелей, но сами компоненты
  // не размонтируем условно в двух ветках — иначе при смене
  // брейкпоинта терялось состояние чата и подписки.
  const showUsers = !isMobile || !hasSelection;
  const showChat = !isMobile || hasSelection;

  return (
    <main
      className={classNames(styles["chat"], {
        [styles["chat-mobile-users"]]: isMobile && !hasSelection,
        [styles["chat-mobile-chat"]]: isMobile && hasSelection,
      })}
    >
      {contextHolder}
      {showUsers && (
        <ChatUsers
          users={users}
          setUsers={setUsers}
          selectedUser={selectedUser}
          setSelectedUser={setSelectedUser}
          className={styles["chat-users"]}
        />
      )}
      {showChat && (
        <Chat
          messages={messages}
          sendMessage={sendMessage}
          setMessages={setMessages}
          error={error}
          status={status}
          api={api}
          setSelectedUser={setSelectedUser}
          selectedUser={selectedUser}
          className={styles["chat-chat"]}
        />
      )}
    </main>
  );
}
