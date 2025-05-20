"use client";
import classNames from "classnames";
import styles from "./styles.module.scss";
import {Button, FloatButton, Input, Spin, UploadFile} from "antd";
import {
    DownOutlined,
    LeftCircleFilled,
    ThunderboltFilled,
    UpCircleOutlined,
} from "@ant-design/icons";
import {Dispatch, SetStateAction, useEffect, useState} from "react";
import {ChatUsersInterface} from "@/app/types/Users";
import useMessages from "@/app/hooks/useMessages";
import Message from "./Message/Message";
import {WebSocketMessage} from "@/app/types/WebsocketTypes";
import {DB_URL} from "@/app/constants";
import {
    FileType,
    getBase64,
    scrollButton,
    scrollDown,
} from "@/app/utils/utils";
import UploadButton from "./UploadButton/UploadButton";
import {message as msg} from "antd";
import PreviewBlock from "./PreviewBlock/PreviewBlock";
import {KeyedMutator} from "swr";
import {MessageInstance} from "antd/es/message/interface";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import {NotificationInstance} from "antd/es/notification/interface";

const Chat = ({
                  className,
                  selectedUser,
                  setSelectedUser,
                  messages,
                  sendMessage,
                  setMessages,
                  error,
                  api,
              }: {
    className: string;
    selectedUser: ChatUsersInterface | undefined;
    setSelectedUser: Dispatch<SetStateAction<ChatUsersInterface | undefined>>;
    messages: WebSocketMessage[];
    sendMessage: (message: {
        user_id: number | undefined;
        message: string;
    }) => void;
    setMessages: Dispatch<SetStateAction<WebSocketMessage[]>>;
    error: boolean;
    api: NotificationInstance;
}) => {
    const [messageApi, messageContext] = msg.useMessage();
    const [message, setMessage] = useState<string>("");

    const [loading, setLoading] = useState<boolean>(true);
    const {userMessages, mutate} = useMessages(selectedUser?.user_id);
    const [button, setButton] = useState<boolean>(false);
    const [files, setFiles] = useState<UploadFile[]>([]);
    const [previewFiles, setPreviewFiles] = useState<UploadFile[]>([]);
    const isMobile = useMediaQuery("(max-width: 1024px)");

    useEffect(() => {
        setLoading(true);
        if (userMessages) {
            setMessages(userMessages.data);
            setLoading(false);
        }
        setLoading(false);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userMessages]);

    useEffect(() => {
        if (error) {
            api.error({
                message: "Произошла ошибка",
                duration: null,
                closable: true,
                description: "Пожалуйста, обновите страницу!",
            });
        }
    }, [error, api]);

    useEffect(() => {
        if (isMobile) {
            setTimeout(() => scrollDown(), 500);
        }
        const chat: HTMLElement | null = document.getElementById("chat-body");
        if (chat) {
            chat.addEventListener("scroll", () => scrollButton(setButton));
        }
        return () => {
            if (chat) {
                chat.removeEventListener("scroll", () => scrollButton(setButton));
            }
        };
    }, [isMobile]);

    useEffect(() => {
        const generatePreviews = async () => {
            const updatedFiles = await Promise.all(
                files.map(async (file) => {
                    if (
                        file.originFileObj &&
                        file.type?.startsWith("image") &&
                        !file.preview
                    ) {
                        try {
                            const preview = await getBase64(file.originFileObj as FileType);
                            return {...file, preview};
                        } catch (error) {
                            console.error("Ошибка генерации preview:", error);
                            return file;
                        }
                    }
                    return file;
                })
            );
            setPreviewFiles(updatedFiles);
        };

        if (files.length > 0) {
            generatePreviews();
        } else {
            setPreviewFiles([]);
        }
    }, [files]);

    return (
        <div className={classNames(className, styles["chat"])}>
            {messageContext}
            {button && (
                <FloatButton
                    type="primary"
                    onClick={() => scrollDown()}
                    shape="circle"
                    icon={<DownOutlined/>}
                    style={{
                        marginBottom: "1.25rem",
                    }}
                />
            )}
            <div className={styles["chat-header"]}>
                {selectedUser?.user_id &&
                    (isMobile ? (
                        <span>
              <Button
                  onClick={() =>
                      setSelectedUser({
                          user_id: undefined,
                      })
                  }
                  size="large"
                  type="link"
                  color="primary"
                  variant="link"
                  icon={<LeftCircleFilled/>}
              />
              <ThunderboltFilled/> Пользователь {selectedUser?.user_id}
            </span>
                    ) : (
                        <span>
              <ThunderboltFilled/> Чат с пользователем {selectedUser?.user_id}
            </span>
                    ))}
            </div>
            <div id="chat-body" className={styles["chat-body"]}>
                {selectedUser?.user_id && loading && (
                    <div className={styles["loader-layout"]}>
                        <Spin/>
                    </div>
                )}
                {selectedUser?.user_id &&
                    !loading &&
                    messages &&
                    messages.length === 0 && (
                        <div className={styles["choose-chat-layout"]}>Сообщений нет</div>
                    )}
                {!selectedUser?.user_id && (
                    <div className={styles["choose-chat-layout"]}>Выберите чат...</div>
                )}
                {messages &&
                    messages.length > 0 &&
                    messages.map((message: WebSocketMessage) => (
                        <Message key={message.id} message={message} mutate={mutate}/>
                    ))}
            </div>
            <div className={styles["chat-input"]}>
                {previewFiles.length > 0 && (
                    <PreviewBlock
                        previewFiles={previewFiles}
                        files={files}
                        setFiles={setFiles}
                    />
                )}
                <UploadButton
                    selectedUser={selectedUser}
                    fileList={files}
                    setFiles={setFiles}
                    messageApi={messageApi}
                />
                <Input
                    disabled={selectedUser?.user_id ? false : true}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Написать сообщение..."
                    variant="borderless"
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            if (!selectedUser?.user_id) {
                                return;
                            }
                            if (files.length > 0) {
                                sendFiles(
                                    files,
                                    message,
                                    selectedUser?.user_id,
                                    mutate,
                                    messageApi,
                                    setFiles,
                                    setMessage
                                );
                                return;
                            }
                            sendMessageWS(
                                message,
                                setMessage,
                                sendMessage,
                                selectedUser?.user_id
                            );
                        }
                    }}
                />
                <Button
                    disabled={!selectedUser?.user_id}
                    onClick={() => {
                        if (!selectedUser?.user_id) {
                            return;
                        }
                        if (files.length > 0) {
                            sendFiles(
                                files,
                                message,
                                selectedUser?.user_id,
                                mutate,
                                messageApi,
                                setFiles,
                                setMessage
                            );
                            return;
                        }
                        sendMessageWS(
                            message,
                            setMessage,
                            sendMessage,
                            selectedUser?.user_id
                        );
                    }}
                    type="link"
                    icon={<UpCircleOutlined/>}
                />
            </div>
        </div>
    );
};

export default Chat;

function sendMessageWS(
    message: string,
    setMessage: Dispatch<SetStateAction<string>>,
    sendMessage: (message: {
        user_id: number | undefined;
        message: string;
    }) => void,
    user_id: number | undefined
) {
    if (message === "") return;
    sendMessage({
        user_id: user_id,
        message: message,
    });
    setMessage("");
}

async function sendFiles(
    fileList: UploadFile[],
    messageText: string,
    user_id: number | undefined,
    mutate: KeyedMutator<unknown>,
    messageApi: MessageInstance,
    setFiles: Dispatch<SetStateAction<UploadFile[]>>,
    setMessage: Dispatch<SetStateAction<string>>
) {
    const formData = new FormData();
    fileList.forEach((file) =>
        formData.append("files", file.originFileObj as File)
    );
    formData.append("message_text", messageText === "" ? "empty" : messageText);
    formData.append("user_id", user_id ? user_id.toString() : "111");
    const response = await fetch(DB_URL + "/upload/panel", {
        method: "POST",
        body: formData,
    });

    if (response.ok) {
        const result = await response.json();
        if (result.success) {
            messageApi.success("Файлы успешно отправлены!");
            setFiles([]);
            setMessage("");
            mutate();
            setTimeout(() => scrollDown(), 500);
            return;
        }
        messageApi.error("Ошибка отправки файлов!");
        setFiles([]);
        setMessage("");
        return;
    }
    messageApi.error("Ошибка отправки файлов!");
    setFiles([]);
    setMessage("");
    return;
}
