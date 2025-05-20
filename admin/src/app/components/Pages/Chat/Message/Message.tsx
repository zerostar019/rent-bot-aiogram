import {WebSocketMessage} from "@/app/types/WebsocketTypes";
import styles from "./styles.module.scss";
import classNames from "classnames";
import dayjs from "dayjs";
import {DB_URL} from "@/app/constants";
import {Dispatch, SetStateAction, useEffect, useState} from "react";
import {Button, Image, message as msg} from "antd";
import {KeyedMutator} from "swr";

interface FilesInterface {
    file_name: string;
    file_url: string;
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

    useEffect(() => {
        if (message.file_id) {
            fetchFile(message.file_id, setFileData, setImage);
        }
    }, [message.file_id]);

    useEffect(() => {
        return () => {
            if (fileData?.file_url) {
                URL.revokeObjectURL(fileData.file_url);
            }
        };
    }, [fileData]);

    const [loading, setLoading] = useState<boolean>(false);

    return (
        <div
            className={classNames(styles["message"], {
                [styles["message-right"]]: message.user_id === 111,
            })}
        >
      <span
          dangerouslySetInnerHTML={{__html: message.message.replaceAll("\n\n", "<br/><br/>")}}
          className={styles["message-text"]}></span>

            {!isImage && message.file_id && fileData && (
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
            {isImage && message.file_id && fileData && (
                <Image
                    width={200}
                    height={200}
                    style={{
                        objectFit: "cover",
                    }}
                    src={fileData.file_url}
                    alt={fileData.file_name}
                />
            )}

            <span className={styles["message-date"]}>
        {dayjs(message.created_at).format("DD.MM.YYYY HH:mm")}
      </span>
            {message.booking_id && !message.approved && <div
                className={styles["message-buttons-layout"]}
            >
                <Button
                    onClick={() => applyToBooking(setLoading, true, mutate, message.booking_id)}
                    loading={loading}
                >✅ Подтвердить</Button>
                <Button
                    onClick={() => applyToBooking(setLoading, false, mutate, message.booking_id)}
                    loading={loading}
                >❌ Отклонить</Button>
            </div>}
        </div>
    );
};

export default Message;

const fetchFile = async (
    file_id: number,
    setFileData: Dispatch<SetStateAction<FilesInterface | null>>,
    setImage: Dispatch<SetStateAction<boolean>>
) => {
    try {
        const response = await fetch(`${DB_URL}/get-file?file_id=${file_id}`);

        if (!response.ok) {
            throw new Error("Ошибка загрузки файла");
        }
        const blob = await response.blob();

        if (blob.type.startsWith("image")) {
            setImage(true);
        }

        // Извлекаем имя файла из заголовка Content-Disposition
        const disposition = response.headers.get("Content-Disposition");
        let fileName: string | null = "downloaded_file";
        if (disposition) {
            fileName = getFileNameFromContentDisposition(disposition);
        }

        const fileUrl = URL.createObjectURL(blob);
        setFileData({file_name: fileName!, file_url: fileUrl});
    } catch (error) {
        console.error("Ошибка при загрузке файла:", error);
        setFileData(null);
    }
};

function getFileNameFromContentDisposition(header: string): string | null {
    if (!header) return null;

    // Пытаемся найти закодированное имя файла с указанием кодировки (RFC 5987)
    const utf8FilenameRegex = /filename\*=UTF-8''([\w%\-\.]+)/i;
    const asciiFilenameRegex = /filename="?([^"]+)"?/;

    const utf8Matches = header.match(utf8FilenameRegex);
    if (utf8Matches && utf8Matches[1]) {
        try {
            // Декодируем URL-encoded строку
            return decodeURIComponent(utf8Matches[1]);
        } catch (e) {
            console.warn("Не удалось декодировать UTF-8 имя файла", e);
        }
    }

    // Если нет UTF-8 кодировки, пробуем обычное имя файла
    const asciiMatches = header.match(asciiFilenameRegex);
    if (asciiMatches && asciiMatches[1]) {
        return asciiMatches[1];
    }

    return null;
}


const applyToBooking = async (
    setLoading: Dispatch<SetStateAction<boolean>>,
    approved: boolean,
    mutate: KeyedMutator<unknown>,
    rental_id ?: number
) => {
    setLoading(true);
    const formData = new FormData();
    formData.append("approved", String(approved));
    formData.append("id_rental", String(rental_id));
    const response = await fetch(`${DB_URL}/update-rental-status`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        msg.error("Ошибка при обновлении статуса!");
        setLoading(false);
        return
    }

    const result = await response.json();
    if (result.success) {
        msg.success("Бронирование успешно подтверждено!");
        setLoading(false);
        mutate()
        return
    }
    msg.error("Ошибка при обновлении статуса!");
    setLoading(false);
    return
}