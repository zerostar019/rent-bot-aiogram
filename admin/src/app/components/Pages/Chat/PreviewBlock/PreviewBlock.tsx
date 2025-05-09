import { Button, Image, UploadFile } from "antd";
import styles from "./styles.module.scss";
import { CloseOutlined, CopyFilled } from "@ant-design/icons";
import { Dispatch, SetStateAction } from "react";

const PreviewBlock = ({
  previewFiles,
  files,
  setFiles,
}: {
  previewFiles: UploadFile[];
  files: UploadFile[];
  setFiles: Dispatch<SetStateAction<UploadFile[]>>;
}) => {
  return (
    <div className={styles["files-layout"]}>
      {previewFiles.map((f) => (
        <div className={styles["files-layout-file"]} key={f.uid}>
          {!f.type?.startsWith("image") && (
            <div className={styles["files-layout-file-doc"]}>
              <Button
                onClick={() => removeFileFromFileList(files, setFiles, f.uid)}
                className={styles["files-layout-file-doc-button"]}
                variant="link"
                color="danger"
                icon={<CloseOutlined />}
                type="link"
              />
              <CopyFilled
                style={{
                  fontSize: "3rem",
                }}
              />
              <span>{f.name}</span>
            </div>
          )}
          {f.url ||
            ((f.preview as string) && (
              <div className={styles["files-layout-file-doc"]}>
                <Button
                  onClick={() => removeFileFromFileList(files, setFiles, f.uid)}
                  className={styles["files-layout-file-doc-button"]}
                  variant="link"
                  color="danger"
                  icon={<CloseOutlined />}
                  type="link"
                />
                <Image
                  preview={false}
                  width={100}
                  height={100}
                  src={f.url || (f.preview as string)}
                  alt={f.name}
                  style={{
                    objectFit: "cover",
                    borderRadius: "0.625rem",
                    border: "1px solid rgba(0, 0, 0, .1)",
                  }}
                />
              </div>
            ))}
        </div>
      ))}
    </div>
  );
};

export default PreviewBlock;

const removeFileFromFileList = (
  fileList: UploadFile[],
  setFiles: Dispatch<SetStateAction<UploadFile[]>>,
  uid: string
) => {
  const newFileList = fileList.filter((file) => file.uid !== uid);
  console.log(newFileList);
  setFiles(newFileList);
};
