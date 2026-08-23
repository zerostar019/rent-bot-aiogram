import {ChatUsersInterface} from "@/app/types/Users";
import {PlusCircleFilled} from "@ant-design/icons";
import {Button, Upload, UploadFile} from "antd";
import {MessageInstance} from "antd/es/message/interface";
import {Dispatch, SetStateAction} from "react";

const UploadButton = ({
                          messageApi,
                          setFiles,
                          fileList,
                          selectedUser,
                          sendLoading
                      }: {
    messageApi: MessageInstance;
    fileList: UploadFile[];
    setFiles: Dispatch<SetStateAction<UploadFile[]>>;
    selectedUser: ChatUsersInterface | undefined;
    sendLoading: boolean
}) => {
    return (
        <Upload
            disabled={sendLoading}
            showUploadList={false}
            maxCount={5}
            fileList={fileList}
            onChange={(info) => {
                setFiles(info.fileList);
                if (info.file.status === "done") {
                    messageApi.success(`Файл ${info.file.name} загружен`);
                } else if (info.file.status === "error") {
                    messageApi.error(`Ошибка загрузки ${info.file.name}`);
                    setFiles(fileList.filter((f) => f.uid !== info.file.uid));
                }
            }}
        >
            <Button

                type="link"
                icon={<PlusCircleFilled/>}
                disabled={!selectedUser?.user_id || sendLoading}
            />
        </Upload>
    );
};

export default UploadButton;
