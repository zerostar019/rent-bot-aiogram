import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { WebSocketMessage } from "../types/WebsocketTypes";
import dayjs from "dayjs";
import { NotificationInstance } from "antd/es/notification/interface";
import { ChatUsersInterface } from "../types/Users";
import { scrollDown } from "../utils/utils";
import { sortUsersByUnreadDesc } from "../components/Pages/Chat/ChatUsers";

const useWebSocket = (
  url: string,
  selectedUser: number | undefined,
  api: NotificationInstance,
  setSelectedUser: Dispatch<SetStateAction<ChatUsersInterface | undefined>>,
  users: ChatUsersInterface[],
  setUsers: Dispatch<SetStateAction<ChatUsersInterface[]>>
) => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    const connect = () => {
      const socket = new WebSocket(url);
      setWs(socket);

      socket.onopen = () => {
        socket.send(JSON.stringify("admin connected"));
      };

      socket.onerror = () => {
        setError(true);
      };

      socket.onclose = () => {
        connect();
      };
    };

    connect();

    return () => {
      if (ws) {
        ws.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  useEffect(() => {
    if (ws) {
      ws.onmessage = ({ data }) => {
        const userMessage: WebSocketMessage = JSON.parse(data);
        if (selectedUser && selectedUser === userMessage.user_id) {
          setMessages((prevMessages) => [...prevMessages, userMessage]);
          setTimeout(() => scrollDown(), 500);
          return;
        }
        if (users && users.length > 0 && selectedUser !== userMessage.user_id) {
          const newUsers = users.map((user) => {
            if (user.user_id === userMessage.user_id) {
              return {
                ...user,
                unread_count: (user.unread_count ?? 0) + 1,
              };
            }
            return { ...user };
          });
          const sortedUsers = sortUsersByUnreadDesc(newUsers);
          setUsers(sortedUsers);
        }
        api.info({
          onClick: () => setSelectedUser({ user_id: userMessage.user_id }),
          message: "Новое сообщение от " + userMessage.user_id,
          description:
            userMessage.message.length > 100
              ? userMessage.message.slice(0, 100) + "..."
              : userMessage.message,
        });
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedUser, ws, api]);

  const sendMessage = (message: {
    user_id: number | undefined;
    message: string;
  }) => {
    const uniqueID = generateUniqueIntKey();
    const newMessages: WebSocketMessage[] = [
      {
        id: uniqueID,
        user_id: 111,
        message: message.message,
        created_at: dayjs(),
      },
    ];
    if (ws) {
      ws.send(JSON.stringify(message));
      setTimeout(() => scrollDown(), 1000);
      setMessages((prevMessages) => [...prevMessages, ...newMessages]);
    }
  };

  return { messages, setMessages, sendMessage, error };
};

export default useWebSocket;

function generateUniqueIntKey() {
  const time = Date.now();
  const random = Math.floor(Math.random() * 1000);
  return time * 1000 + random;
}
