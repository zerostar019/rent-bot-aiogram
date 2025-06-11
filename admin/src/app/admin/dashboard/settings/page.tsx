/* eslint @typescript-eslint/no-explicit-any: ["off"] */
"use client";
import {Button, Card, Form, Input} from "antd";
import styles from "./styles.module.scss";
import useSWR, {KeyedMutator} from "swr";
import {DB_URL} from "@/app/constants";
import {fetcher} from "@/app/utils/fetcher";
import {Dispatch, SetStateAction, useEffect, useState} from "react";
import {InfoCircleOutlined} from "@ant-design/icons";

const Page = () => {
    const {data: textData, mutate} = useSWR(`${DB_URL}/get-field-text?field_name=payment_text`, fetcher);
    const [form] = Form.useForm();
    const [loading, setLoading] = useState<boolean>(false);

    useEffect(() => {
        if (textData && textData.success) {
            form.setFieldValue("payment_text", textData.data.text);
        }
    }, [textData, form])

    return (
        <Card
            style={{
                maxHeight: "100%",
                overflow: "hidden",
            }}
            styles={{
                body: {
                    height: "100%",
                    overflow: "hidden",
                    padding: 0,
                },
            }}
        >
            <div
                className={styles['page-layout']}
            >
            <span
                className={styles['header-text']}
            >
                Настройки бота
            </span>
                <Form
                    onFinish={(values) => onFinish(mutate, values, setLoading)}
                    form={form}
                    layout="vertical"
                >
                    <Form.Item
                        label="Ответное сообщение на бронь"
                        name="payment_text"
                        rules={[{required: true, message: "Введите текст для показа"}]}
                    >
                        <Input.TextArea
                            autoSize
                            disabled={loading}
                            placeholder="Введите текст для оплаты..."
                        />
                    </Form.Item>
                    <div>
                    <span
                        className={styles['remark-text']}
                    >
                        <InfoCircleOutlined/>
                        {" "}
                        <i>
                            Сумма к оплате автоматически добавится в конце текста
                        </i>
                    </span>
                        <br/>
                        <br/>
                        <span>
                            <i>Информация про форматирование текста:</i><br/>
                            \n - перенос строки<br/>
                            {"<i>текст</i>"} - курсив<br/>
                            {"<b>текст</b>"} - жирный<br/>
                            {"<pre>текст</pre>"} - позволяет копировать при нажатии<br/>
                            <b>ВАЖНО - не ставить кавычки (только такие «»)</b>
                    </span>
                    </div>
                    <Form.Item
                        style={{
                            marginTop: "1rem"
                        }}
                    >
                        <Button
                            loading={loading}
                            type={"primary"}
                            htmlType={"submit"}
                            variant={"solid"}
                        >
                            Сохранить
                        </Button>
                    </Form.Item>
                </Form>
            </div>
        </Card>
    )
}

export default Page;


const onFinish = async (
    mutate: KeyedMutator<unknown>,
    values: any,
    setLoading: Dispatch<SetStateAction<boolean>>
) => {
    setLoading(true);
    const fieldName = Object.keys(values)[0];
    const fieldText = values[fieldName];
    const formData = new FormData();
    formData.append("field_name", fieldName);
    formData.append("field_text", fieldText);
    const r = await fetch(`${DB_URL}/set-field-text`, {
        method: "POST",
        body: formData
    })
    if (r.ok) {
        const result = await r.json();
        if (result.success) {
            await mutate();
        }
    }
    setLoading(false);
}