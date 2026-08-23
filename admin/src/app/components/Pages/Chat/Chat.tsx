"use client";
import classNames from "classnames";
import styles from "./styles.module.scss";
import { Button, Skeleton, Tooltip, UploadFile } from "antd";
import { ArrowDownOutlined, ArrowLeftOutlined, SendOutlined } from "@ant-design/icons";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { ChatUsersInterface } from "@/app/types/Users";
import useMessages from "@/app/hooks/useMessages";
import Message from "./Message/Message";
import { WebSocketMessage } from "@/app/types/WebsocketTypes";
import { DB_URL } from "@/app/constants";
import { FileType, getBase64 } from "@/app/utils/utils";
import UploadButton from "./UploadButton/UploadButton";
import { message as msg } from "antd";
import PreviewBlock from "./PreviewBlock/PreviewBlock";
import { KeyedMutator } from "swr";
import { MessageInstance } from "antd/es/message/interface";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import { NotificationInstance } from "antd/es/notification/interface";
import { ConnectionStatus } from "@/app/hooks/useWebsocket";
import { useVirtualizer } from "@tanstack/react-virtual";
import dayjs from "dayjs";

const ADMIN_ID = 111;

type Row =
  | { kind: "day"; key: string; label: string }
  | { kind: "message"; key: string; message: WebSocketMessage };

const dayLabel = (value: unknown) => {
  const d = dayjs(value as string);
  if (!d.isValid()) return "";
  const today = dayjs().startOf("day");
  const diff = today.diff(d.startOf("day"), "day");
  if (diff === 0) return "Сегодня";
  if (diff === 1) return "Вчера";
  return d.format("D MMMM YYYY");
};

const statusLabel: Record<ConnectionStatus, string> = {
  connecting: "Подключение…",
  open: "На связи",
  reconnecting: "Переподключение…",
  offline: "Нет соединения",
};

const Chat = ({
  className,
  selectedUser,
  setSelectedUser,
  messages,
  sendMessage,
  setMessages,
  error,
  status,
}: {
  className: string;
  selectedUser: ChatUsersInterface | undefined;
  setSelectedUser: Dispatch<SetStateAction<ChatUsersInterface | undefined>>;
  messages: WebSocketMessage[];
  sendMessage: (message: {
    user_id: number | undefined;
    message: string;
  }) => boolean;
  setMessages: Dispatch<SetStateAction<WebSocketMessage[]>>;
  error: boolean;
  api: NotificationInstance;
  status: ConnectionStatus;
}) => {
  const [messageApi, messageContext] = msg.useMessage();
  const [draft, setDraft] = useState<string>("");
  const [sendLoading, setSendLoading] = useState<boolean>(false);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [previewFiles, setPreviewFiles] = useState<UploadFile[]>([]);
  const [atBottom, setAtBottom] = useState<boolean>(true);

  const { userMessages, isLoading, mutate } = useMessages(selectedUser?.user_id);
  const isMobile = useMediaQuery("(max-width: 1024px)");

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (userMessages?.data) {
      setMessages(userMessages.data);
    }
  }, [userMessages, setMessages]);

  // Плоский список строк: разделители дат вперемешку с сообщениями.
  const rows = useMemo<Row[]>(() => {
    const list = Array.isArray(messages) ? messages : [];
    const result: Row[] = [];
    let lastDay = "";
    for (const message of list) {
      const day = dayjs(message.created_at as unknown as string).format("YYYY-MM-DD");
      if (day !== lastDay) {
        lastDay = day;
        result.push({ kind: "day", key: `day-${day}`, label: dayLabel(message.created_at) });
      }
      result.push({ kind: "message", key: `m-${message.id}`, message });
    }
    return result;
  }, [messages]);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    // Сообщения разной высоты, поэтому оценка уточняется измерением.
    estimateSize: (index) => (rows[index]?.kind === "day" ? 44 : 84),
    overscan: 10,
    getItemKey: (index) => rows[index]?.key ?? index,
  });

  const scrollToBottom = useCallback(
    (behavior: ScrollBehavior = "smooth") => {
      const el = scrollRef.current;
      if (!el) return;
      el.scrollTo({ top: el.scrollHeight, behavior });
    },
    []
  );

  // Отслеживаем позицию через ref-колбэк: раньше removeEventListener
  // получал новую функцию и слушатель не снимался никогда,
  // накапливаясь при каждом ресайзе.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      setAtBottom(distance < 80);
    };
    onScroll();
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [selectedUser?.user_id]);

  // Автопрокрутка вниз — только если админ и так внизу,
  // иначе чтение истории будет прерываться новыми сообщениями.
  useLayoutEffect(() => {
    if (rows.length === 0) return;
    if (atBottom) {
      virtualizer.scrollToIndex(rows.length - 1, { align: "end" });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows.length]);

  useEffect(() => {
    if (selectedUser?.user_id) {
      setAtBottom(true);
      requestAnimationFrame(() => scrollToBottom("auto"));
    }
  }, [selectedUser?.user_id, scrollToBottom]);

  useEffect(() => {
    const generatePreviews = async () => {
      const updated = await Promise.all(
        files.map(async (file) => {
          if (file.originFileObj && file.type?.startsWith("image") && !file.preview) {
            try {
              const preview = await getBase64(file.originFileObj as FileType);
              return { ...file, preview };
            } catch {
              return file;
            }
          }
          return file;
        })
      );
      setPreviewFiles(updated);
    };
    if (files.length > 0) generatePreviews();
    else setPreviewFiles([]);
  }, [files]);

  const submit = useCallback(() => {
    if (!selectedUser?.user_id) return;
    if (files.length > 0) {
      sendFiles(
        files, draft, selectedUser.user_id, mutate,
        messageApi, setFiles, setDraft, setSendLoading
      );
      return;
    }
    const text = draft.trim();
    if (!text) return;

    const ok = sendMessage({ user_id: selectedUser.user_id, message: text });
    if (!ok) return;

    // Оптимистичная вставка: сообщение видно сразу, до ответа сервера.
    // Отрицательный id помечает временную запись — её заменит broadcast.
    setMessages((prev) => [
      ...prev,
      {
        id: -Date.now(),
        user_id: ADMIN_ID,
        chat_id: selectedUser.user_id,
        message: text,
        created_at: dayjs() as never,
      } as WebSocketMessage,
    ]);
    setDraft("");
    setAtBottom(true);
    requestAnimationFrame(() => scrollToBottom());
    inputRef.current?.focus();
  }, [draft, files, selectedUser?.user_id, sendMessage, setMessages, mutate, messageApi, scrollToBottom]);

  const disabled = !selectedUser?.user_id;
  const canSend = !disabled && !sendLoading && (draft.trim() !== "" || files.length > 0);

  return (
    <section className={classNames(className, styles["chat"])}>
      {messageContext}

      <header className={styles["chat-header"]}>
        {isMobile && selectedUser?.user_id && (
          <Button
            type="text"
            aria-label="Назад к списку чатов"
            icon={<ArrowLeftOutlined />}
            onClick={() => setSelectedUser({ user_id: undefined })}
          />
        )}
        {selectedUser?.user_id ? (
          <>
            <div className={styles["chat-header-main"]}>
              <h1 className={styles["chat-header-title"]}>
                Гость {selectedUser.user_id}
              </h1>
              <span
                className={classNames(
                  styles["chat-status"],
                  styles[`chat-status--${status}`]
                )}
              >
                <i aria-hidden="true" />
                {statusLabel[status]}
              </span>
            </div>
          </>
        ) : (
          <h1 className={styles["chat-header-title"]}>Сообщения</h1>
        )}
      </header>

      <div className={styles["chat-body"]} ref={scrollRef} id="chat-body">
        {disabled && (
          <div className={styles["chat-placeholder"]}>
            <div className={styles["chat-placeholder-mark"]} aria-hidden="true" />
            <h2>Выберите чат</h2>
            <p>
              Слева — все обращения гостей. Непрочитанные подняты наверх.
            </p>
          </div>
        )}

        {!disabled && isLoading && rows.length === 0 && (
          <div className={styles["chat-skeleton"]}>
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} active paragraph={{ rows: 1 }} title={false} />
            ))}
          </div>
        )}

        {!disabled && !isLoading && rows.length === 0 && (
          <div className={styles["chat-placeholder"]}>
            <h2>Здесь пока пусто</h2>
            <p>Напишите первым — гость получит сообщение в Telegram.</p>
          </div>
        )}

        {rows.length > 0 && (
          <div
            className={styles["chat-virtual"]}
            style={{ height: virtualizer.getTotalSize() }}
          >
            {virtualizer.getVirtualItems().map((item) => {
              const row = rows[item.index];
              if (!row) return null;
              return (
                <div
                  key={item.key}
                  ref={virtualizer.measureElement}
                  data-index={item.index}
                  className={styles["chat-row"]}
                  style={{ transform: `translateY(${item.start}px)` }}
                >
                  {row.kind === "day" ? (
                    <div className={styles["chat-day"]}>
                      <span>{row.label}</span>
                    </div>
                  ) : (
                    <Message message={row.message} mutate={mutate} />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {!atBottom && rows.length > 0 && (
        <Tooltip title="К последним сообщениям">
          <button
            type="button"
            className={styles["chat-jump"]}
            onClick={() => scrollToBottom()}
            aria-label="Прокрутить к последним сообщениям"
          >
            <ArrowDownOutlined />
          </button>
        </Tooltip>
      )}

      <footer className={styles["chat-input"]}>
        {previewFiles.length > 0 && (
          <PreviewBlock
            previewFiles={previewFiles}
            files={files}
            setFiles={setFiles}
          />
        )}
        <div className={styles["chat-input-row"]}>
          <UploadButton
            sendLoading={sendLoading}
            selectedUser={selectedUser}
            fileList={files}
            setFiles={setFiles}
            messageApi={messageApi}
          />
          {/* Управляемое поле вместо contentEditable: раньше после отправки
              текст оставался в DOM, потому что React не владел содержимым. */}
          <textarea
            ref={inputRef}
            className={styles["chat-input-field"]}
            value={draft}
            disabled={disabled || sendLoading}
            placeholder={
              disabled ? "Выберите чат, чтобы начать" : "Напишите сообщение…"
            }
            aria-label="Текст сообщения"
            rows={1}
            onChange={(e) => {
              setDraft(e.target.value);
              const el = e.currentTarget;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
          />
          <Button
            type="primary"
            shape="circle"
            size="large"
            loading={sendLoading}
            disabled={!canSend}
            onClick={submit}
            aria-label="Отправить сообщение"
            icon={<SendOutlined />}
          />
        </div>
        {error && status !== "open" && (
          <p className={styles["chat-input-warning"]} role="status">
            Соединение потеряно — восстанавливаем. Сообщения пока не уходят.
          </p>
        )}
      </footer>
    </section>
  );
};

export default Chat;

async function sendFiles(
  fileList: UploadFile[],
  messageText: string,
  user_id: number | undefined,
  mutate: KeyedMutator<unknown>,
  messageApi: MessageInstance,
  setFiles: Dispatch<SetStateAction<UploadFile[]>>,
  setMessage: Dispatch<SetStateAction<string>>,
  setSendLoading: Dispatch<SetStateAction<boolean>>
) {
  setSendLoading(true);
  const formData = new FormData();
  fileList.forEach((file) =>
    formData.append("files", file.originFileObj as File)
  );
  formData.append("message_text", messageText === "" ? "empty" : messageText);
  formData.append("user_id", user_id ? user_id.toString() : "111");

  // Раньше сетевая ошибка выбрасывалась наружу и setSendLoading(false)
  // не выполнялся — кнопка залипала в состоянии загрузки навсегда.
  try {
    const response = await fetch(DB_URL + "/upload/panel", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    if (!result.success) throw new Error("upload rejected");

    messageApi.success("Файлы отправлены");
    setFiles([]);
    setMessage("");
    mutate();
  } catch {
    messageApi.error("Не удалось отправить файлы. Попробуйте ещё раз.");
  } finally {
    setSendLoading(false);
  }
}
