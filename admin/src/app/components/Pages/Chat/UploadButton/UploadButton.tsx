import { ChatUsersInterface } from "@/app/types/Users";
import { PlusCircleFilled } from "@ant-design/icons";
import { Button, Upload, UploadFile } from "antd";
import { MessageInstance } from "antd/es/message/interface";
import { Dispatch, SetStateAction } from "react";

const UploadButton = ({
  messageApi,
  setFiles,
  fileList,
  selectedUser,
}: {
  messageApi: MessageInstance;
  fileList: UploadFile[];
  setFiles: Dispatch<SetStateAction<UploadFile[]>>;
  selectedUser: ChatUsersInterface | undefined;
}) => {
  return (
    <Upload
      beforeUpload={(file) => beforeUpload(file, messageApi)}
      showUploadList={false}
      maxCount={5}
      fileList={fileList}
      onChange={(info) => {
        setFiles(info.fileList);
        if (info.file.status === "done") {
          messageApi.success(`Файл ${info.file.name} загружен`);
        } else if (info.file.status === "error") {
          messageApi.error(`Ошибка загрузки ${info.file.name}`);
        }
      }}
    >
      <Button
        type="link"
        icon={<PlusCircleFilled />}
        disabled={!selectedUser?.user_id}
      />
    </Upload>
  );
};

export default UploadButton;

const beforeUpload = (file: File, messageApi: MessageInstance) => {
  const isLt2M = file.size / 1024 / 1024 < 10;
  if (!isLt2M) {
    messageApi.error("Файл должен быть меньше 10MB!");
  }
  return isLt2M;
};
