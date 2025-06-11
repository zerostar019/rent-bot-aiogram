import { GetProp, UploadProps } from "antd";
import { Dispatch, SetStateAction } from "react";

export const scrollDown = () => {
  const elem: HTMLElement | null = document.getElementById("chat-body");
  if (elem) {
    const scrollTo = elem.scrollHeight + 1000000;
    elem.scrollTo({
      top: scrollTo,
      behavior: "smooth",
    });
  }
};

export const scrollButton = (setButton: Dispatch<SetStateAction<boolean>>) => {
  const elem: HTMLElement | null = document.getElementById("chat-body");
  if (elem) {
    const scrollTo = elem.scrollHeight - elem.scrollTop - elem.clientHeight;
    if (scrollTo > 30) {
      setButton(true);
    } else {
      setButton(false);
    }
  }
};

export type FileType = Parameters<GetProp<UploadProps, "beforeUpload">>[0];

export const getBase64 = (file: FileType): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });
