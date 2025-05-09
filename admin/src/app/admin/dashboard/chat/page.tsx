"use client";
import { Card, notification } from "antd";
import styles from "./styles.module.scss";
import ChatUsers from "@/app/components/Pages/Chat/ChatUsers";
import Chat from "@/app/components/Pages/Chat/Chat";
import { useState } from "react";
import { ChatUsersInterface } from "@/app/types/Users";
import classNames from "classnames";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import useWebSocket from "@/app/hooks/useWebsocket";
import { DB_URL } from "@/app/constants";

export default function Page() {
  const [selectedUser, setSelectedUser] = useState<
    ChatUsersInterface | undefined
  >(undefined);
  const [api, contextHolder] = notification.useNotification();
  const [users, setUsers] = useState<Array<ChatUsersInterface>>([]);
  const { messages, sendMessage, setMessages, error } = useWebSocket(
    `${DB_URL}/chat`,
    selectedUser?.user_id,
    api,
    setSelectedUser,
    users,
    setUsers
  );

  const isMobile = useMediaQuery("(max-width: 1024px)");

  return (
    <Card
      style={{
        maxHeight: "100%",
        overflow: "hidden",
      }}
      styles={{
        body: {
          height: "100%",
          overflow: "hidden",
          padding: 0,
        },
      }}
    >
      {contextHolder}
      <div
        className={classNames(styles["chat"], {
          [styles["chat-mobile-users"]]: isMobile && !selectedUser?.user_id,
          [styles["chat-mobile-chat"]]: isMobile && selectedUser?.user_id,
        })}
      >
        {!selectedUser?.user_id && isMobile && (
          <ChatUsers
            users={users}
            setUsers={setUsers}
            selectedUser={selectedUser}
            setSelectedUser={setSelectedUser}
            className={classNames(styles["chat-users"])}
          />
        )}
        {selectedUser?.user_id && isMobile && (
          <Chat
            messages={messages}
            sendMessage={sendMessage}
            setMessages={setMessages}
            error={error}
            api={api}
            setSelectedUser={setSelectedUser}
            selectedUser={selectedUser}
            className={classNames(styles["chat-chat"], {
              [styles["chat-chat-disabled"]]:
                isMobile && !selectedUser?.user_id,
            })}
          />
        )}
        {!isMobile && (
          <>
            <ChatUsers
              users={users}
              setUsers={setUsers}
              selectedUser={selectedUser}
              setSelectedUser={setSelectedUser}
              className={classNames(styles["chat-users"])}
            />
            <Chat
              messages={messages}
              sendMessage={sendMessage}
              setMessages={setMessages}
              error={error}
              api={api}
              setSelectedUser={setSelectedUser}
              selectedUser={selectedUser}
              className={classNames(styles["chat-chat"], {
                [styles["chat-chat-disabled"]]:
                  isMobile && !selectedUser?.user_id,
              })}
            />
          </>
        )}
      </div>
    </Card>
  );
}
