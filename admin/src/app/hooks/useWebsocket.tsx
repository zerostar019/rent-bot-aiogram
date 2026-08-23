import { Dispatch, SetStateAction, useCallback, useEffect, useRef, useState } from "react";
import { WebSocketMessage } from "../types/WebsocketTypes";
import { NotificationInstance } from "antd/es/notification/interface";
import { ChatUsersInterface } from "../types/Users";

export type ConnectionStatus = "connecting" | "open" | "reconnecting" | "offline";

/** Пауза перед повторным подключением: 1с, 2с, 4с… но не дольше 15с. */
const backoffDelay = (attempt: number) =>
  Math.min(1000 * 2 ** Math.min(attempt, 4), 15000);

const HEARTBEAT_INTERVAL = 25000;

const useWebSocket = (
  url: string,
  selectedUser: number | undefined,
  api: NotificationInstance,
  setSelectedUser: Dispatch<SetStateAction<ChatUsersInterface | undefined>>,
  users: ChatUsersInterface[],
  setUsers: Dispatch<SetStateAction<ChatUsersInterface[]>>
) => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [error, setError] = useState<boolean>(false);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAllowed = useRef(true);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const attemptRef = useRef(0);

  // Актуальные значения держим в ref, чтобы не переподключать сокет
  // при каждой смене выбранного пользователя.
  const selectedUserRef = useRef(selectedUser);
  const usersRef = useRef(users);
  const apiRef = useRef(api);

  useEffect(() => {
    selectedUserRef.current = selectedUser;
  }, [selectedUser]);
  useEffect(() => {
    usersRef.current = users;
  }, [users]);
  useEffect(() => {
    apiRef.current = api;
  }, [api]);

  const handleIncoming = useCallback(
    (raw: string) => {
      let payload: WebSocketMessage;
      try {
        payload = JSON.parse(raw);
      } catch {
        return; // сервисные кадры (pong и пр.) просто игнорируем
      }
      if (!payload || typeof payload !== "object" || payload.id === undefined) {
        return;
      }

      const chatId = payload.chat_id ?? payload.user_id;

      // Сообщение в открытом чате — дописываем в ленту.
      if (selectedUserRef.current && selectedUserRef.current === chatId) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === payload.id)) return prev;
          // Заменяем оптимистичную копию, если она есть.
          const optimistic = prev.findIndex(
            (m) => m.id < 0 && m.message === payload.message
          );
          if (optimistic !== -1) {
            const next = [...prev];
            next[optimistic] = payload;
            return next;
          }
          return [...prev, payload];
        });
        return;
      }

      // Сообщение в другом чате — увеличиваем счётчик непрочитанных.
      setUsers((prev) => {
        const known = prev.some((u) => u.user_id === chatId);
        const next = known
          ? prev.map((u) =>
              u.user_id === chatId
                ? { ...u, unread_count: (u.unread_count || 0) + 1 }
                : u
            )
          : [{ user_id: chatId, unread_count: 1 }, ...prev];
        return next;
      });

      apiRef.current.info({
        key: `msg-${chatId}`,
        onClick: () => setSelectedUser({ user_id: chatId }),
        message: `Новое сообщение от ${chatId}`,
        description:
          payload.message && payload.message.length > 100
            ? payload.message.slice(0, 100) + "…"
            : payload.message || "Вложение",
      });
    },
    [setSelectedUser, setUsers]
  );

  useEffect(() => {
    reconnectAllowed.current = true;

    const clearTimers = () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (heartbeatTimer.current) clearInterval(heartbeatTimer.current);
      reconnectTimer.current = null;
      heartbeatTimer.current = null;
    };

    const connect = () => {
      if (!reconnectAllowed.current) return;

      const socket = new WebSocket(url);
      socketRef.current = socket;
      setStatus(attemptRef.current === 0 ? "connecting" : "reconnecting");

      socket.onopen = () => {
        attemptRef.current = 0;
        setError(false);
        setStatus("open");
        // Периодический кадр не даёт прокси разорвать простаивающее соединение.
        heartbeatTimer.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "ping" }));
          }
        }, HEARTBEAT_INTERVAL);
      };

      socket.onmessage = ({ data }) => handleIncoming(data);

      socket.onerror = () => {
        setError(true);
      };

      socket.onclose = () => {
        if (heartbeatTimer.current) {
          clearInterval(heartbeatTimer.current);
          heartbeatTimer.current = null;
        }
        if (!reconnectAllowed.current) return;

        // Раньше здесь стоял мгновенный connect() без паузы: при недоступном
        // сервере это давало бесконечный цикл переподключений,
        // который нагружал и браузер, и сам сервер.
        const delay = backoffDelay(attemptRef.current);
        attemptRef.current += 1;
        setStatus(attemptRef.current > 2 ? "offline" : "reconnecting");
        reconnectTimer.current = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      reconnectAllowed.current = false;
      clearTimers();
      const socket = socketRef.current;
      if (socket && socket.readyState <= WebSocket.OPEN) {
        socket.close();
      }
      socketRef.current = null;
    };
  }, [url, handleIncoming]);

  const sendMessage = useCallback(
    (message: { user_id: number | undefined; message: string }) => {
      const socket = socketRef.current;
      // Отправка в неоткрытый сокет бросает InvalidStateError —
      // раньше это роняло обработчик и сообщение терялось молча.
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        apiRef.current.warning({
          message: "Нет соединения",
          description: "Сообщение не отправлено. Дождитесь переподключения.",
        });
        return false;
      }
      socket.send(JSON.stringify(message));
      return true;
    },
    []
  );

  return { messages, setMessages, sendMessage, error, status };
};

export default useWebSocket;
