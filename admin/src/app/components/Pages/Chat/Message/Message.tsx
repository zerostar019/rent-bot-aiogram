import {WebSocketMessage} from "@/app/types/WebsocketTypes";
import styles from "./styles.module.scss";
import classNames from "classnames";
import dayjs from "dayjs";
import {DB_URL} from "@/app/constants";
import {Dispatch, SetStateAction, useEffect, useRef, useState} from "react";
import {Button, Image, message as msg} from "antd";
import {CheckOutlined, CloseOutlined} from "@ant-design/icons";
import {KeyedMutator} from "swr";


interface FilesInterface {
    file_name: string;
    file_url: string;
}

function escapeHtml(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML.replace(/\n\n/g, "<br/><br/>");
}

const Message = (
        {
            message,
            mutate
        }:
        {
            message: WebSocketMessage,
            mutate: KeyedMutator<unknown>
        }) => {
        const [fileData, setFileData] = useState<FilesInterface | null>(null);
        const [isImage, setImage] = useState<boolean>(false);
        const prevFileUrl = useRef<string | null>(null);

        useEffect(() => {
            if (message.file_id) {
                fetchFile(message.file_id, setFileData, setImage, prevFileUrl);
            }
        }, [message.file_id]);

        useEffect(() => {
            return () => {
                if (fileData?.file_url) {
                    URL.revokeObjectURL(fileData.file_url);
                }
            };
        }, [fileData]);

        // Раньше loading висел на обеих кнопках сразу — спиннер крутился
        // и на той, по которой не кликали.
        const [pending, setPending] = useState<"approve" | "decline" | null>(null);

        return (
            <div
                className={classNames(styles["message"], {
                    [styles["message-right"]]: message.user_id === 111,
                })}
            >
          <span
              dangerouslySetInnerHTML={{__html: escapeHtml(message.message || "")}}
              className={styles["message-text"]}></span>

                {!isImage && message.file_id && fileData && !fileData.file_name.includes(".pdf")
                    && (
                        <a
                            href={fileData.file_url}
                            download={fileData.file_name}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles["message-file"]}
                        >
                            📎 {fileData.file_name}
                        </a>
                    )}
                {!isImage && message.file_id && fileData && fileData.file_name.includes(".pdf")
                    && (
                        // Раньше PDF открывался во встроенном docs.google.com/gview —
                        // документы гостей уходили на сторонний сервис, а сам
                        // просмотрщик занимал пол-экрана чёрным прямоугольником.
                        // Показываем карточку файла: открывается по клику.
                        <a
                            href={fileData.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles["message-doc"]}
                        >
                            <span className={styles["message-doc-icon"]} aria-hidden="true">
                                PDF
                            </span>
                            <span className={styles["message-doc-meta"]}>
                                <span className={styles["message-doc-name"]}>
                                    {fileData.file_name}
                                </span>
                                <span className={styles["message-doc-hint"]}>
                                    Открыть документ
                                </span>
                            </span>
                        </a>
                    )}
                {isImage && message.file_id && fileData && (
                    <div className={styles["message-media"]}>
                        <Image
                            width={220}
                            height={220}
                            style={{objectFit: "cover", display: "block"}}
                            src={fileData.file_url}
                            alt={fileData.file_name || "Вложение из чата"}
                        />
                    </div>
                )}

                <span className={styles["message-time"]}>
        {dayjs(message.created_at).format("HH:mm")}
      </span>
                {message.booking_id && !message.approved && (
                    <div className={styles["booking-actions"]}>
                        <span className={styles["booking-actions-label"]}>
                            Запрос на бронирование
                        </span>
                        <div className={styles["booking-actions-row"]}>
                            <Button
                                type="primary"
                                icon={<CheckOutlined/>}
                                className={styles["booking-approve"]}
                                onClick={() => applyToBooking(
                                    setPending,
                                    true,
                                    mutate,
                                    message.user_id,
                                    message.booking_id)}
                                loading={pending === "approve"}
                                disabled={pending !== null}
                            >
                                Подтвердить
                            </Button>
                            <Button
                                icon={<CloseOutlined/>}
                                className={styles["booking-decline"]}
                                onClick={() => applyToBooking(
                                    setPending,
                                    false,
                                    mutate,
                                    message.user_id,
                                    message.booking_id)}
                                loading={pending === "decline"}
                                disabled={pending !== null}
                            >
                                Отклонить
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        )
            ;
    }
;

export default Message;

const fetchFile = async (
    file_id: number,
    setFileData: Dispatch<SetStateAction<FilesInterface | null>>,
    setImage: Dispatch<SetStateAction<boolean>>,
    prevFileUrl: React.MutableRefObject<string | null>
) => {
    try {
        if (prevFileUrl.current) {
            URL.revokeObjectURL(prevFileUrl.current);
        }

        const response = await fetch(`${DB_URL}/get-file?file_id=${file_id}`);

        if (!response.ok) {
            throw new Error("Ошибка загрузки файла");
        }
        const blob = await response.blob();

        if (blob.type.startsWith("image")) {
            setImage(true);
        }

        const disposition = response.headers.get("Content-Disposition");
        let fileName: string | null = "downloaded_file";
        if (disposition) {
            fileName = getFileNameFromContentDisposition(disposition);
        }

        const fileUrl = URL.createObjectURL(blob);
        prevFileUrl.current = fileUrl;
        setFileData({file_name: fileName!, file_url: fileUrl});
    } catch (error) {
        console.error("Ошибка при загрузке файла:", error);
        setFileData(null);
    }
};

function getFileNameFromContentDisposition(header: string): string | null {
    if (!header) return null;

    const utf8FilenameRegex = /filename\*=UTF-8''([\w%\-\.]+)/i;
    const asciiFilenameRegex = /filename="?([^"]+)"?/;

    const utf8Matches = header.match(utf8FilenameRegex);
    if (utf8Matches && utf8Matches[1]) {
        try {
            return decodeURIComponent(utf8Matches[1]);
        } catch (e) {
            console.warn("Не удалось декодировать UTF-8 имя файла", e);
        }
    }

    const asciiMatches = header.match(asciiFilenameRegex);
    if (asciiMatches && asciiMatches[1]) {
        return asciiMatches[1];
    }

    return null;
}


const applyToBooking = async (
    setPending: Dispatch<SetStateAction<"approve" | "decline" | null>>,
    approved: boolean,
    mutate: KeyedMutator<unknown>,
    user_id: number,
    rental_id ?: number
) => {
    setPending(approved ? "approve" : "decline");
    const formData = new FormData();
    formData.append("approved", String(approved));
    formData.append("id_rental", String(rental_id));
    formData.append("user_id", String(user_id));
    try {
        const response = await fetch(`${DB_URL}/update-rental-status`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            msg.error("Не удалось обновить статус");
            setPending(null);
            return
        }

        const result = await response.json();
        if (result.success) {
            msg.success(approved ? "Бронирование подтверждено" : "Бронирование отклонено");
            await mutate();
            setPending(null);
            return
        }
        msg.error("Не удалось обновить статус");
        setPending(null);
        return
    } catch {
        msg.error("Нет связи с сервером");
        setPending(null);
    }
}