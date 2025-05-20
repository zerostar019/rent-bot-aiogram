"use client";
import {Button, Form, Input, message, Select, Switch} from "antd";
import RuRangePicker from "../RuRangePicker/RuRangePicker";
import {BookOutlined} from "@ant-design/icons";
import {FormInstance} from "antd/lib";
import dayjs from "dayjs";
import {DB_URL} from "@/app/constants";
import {Dispatch, SetStateAction, useEffect, useState} from "react";
import {MessageInstance} from "antd/es/message/interface";
import useSWR from "swr";
import {fetcher} from "@/app/utils/fetcher";

const BookingForm = ({
                         setModal,
                         isEdit,
                         editId,
                     }: {
    setModal?: Dispatch<SetStateAction<boolean>>;
    isEdit?: boolean;
    editId?: number;
}) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState<boolean>(false);
    const [messageApi, contextApi] = message.useMessage();
    const {data} = useSWR(
        isEdit ? `${DB_URL}/get-booking?booking_id=${editId}` : null,
        fetcher
    );
    const [editInterval, setEditInterval] = useState<string>("");

    useEffect(() => {
        if (isEdit && data) {
            if (data.success) {
                const bookingData = data.data;
                if ("time_interval" in bookingData) {
                    const start = dayjs(bookingData["time_interval"]["start"]).format(
                        "YYYY-MM-DD"
                    );
                    const end = dayjs(bookingData["time_interval"]["end"]).format(
                        "YYYY-MM-DD"
                    );
                    const dateRange = `${start},${end}`;
                    setEditInterval(dateRange);
                }
                if ("id_user" in bookingData) {
                    form.setFieldValue("user_id", bookingData["id_user"]);
                }
                if ("rent_type" in bookingData) {
                    form.setFieldValue("rent_type", bookingData["rent_type"]);
                }
                if ("approved" in bookingData) {
                    form.setFieldValue("approved", bookingData["approved"]);
                }
                if ("amount" in bookingData) {
                    form.setFieldValue("amount", bookingData["amount"]);
                }
            }
        }
    }, [isEdit, data, form]);

    return (
        <>
            {contextApi}
            <Form
                id="booking-form"
                initialValues={
                    isEdit ? {
                        id_rental: editId
                    } : {from_panel: true, notification: true}
                }
                disabled={loading}
                onFinish={() => finishBooking(form, setLoading, messageApi, setModal, isEdit)}
                layout="vertical"
                form={form}
            >
                <Form.Item noStyle name={"id_rental"}></Form.Item>
                {!isEdit && <Form.Item noStyle name="from_panel"></Form.Item>}
                <Form.Item
                    rules={[{required: true, message: "Выберите тип бронирования"}]}
                    name="rent_type"
                    label={isEdit ? "Тип бронирования" : "Выберите тип бронирования"}
                >
                    <Select
                        options={[
                            {
                                id: 0,
                                label: "Посуточно",
                                value: "daily",
                            },
                            {
                                id: 1,
                                label: "Почасово",
                                value: "hourly",
                                disabled: true,
                            },
                        ]}
                        placeholder="Тип бронирования"
                    />
                </Form.Item>
                <Form.Item
                    rules={[{required: false, message: "Введите Telegram ID"}]}
                    label="Telegram ID"
                    name="user_id"
                >
                    <Input placeholder="ID (необязательно)"/>
                </Form.Item>
                <Form.Item
                    rules={[{required: true, message: "Выберите интервал"}]}
                    name="time_interval"
                    label={
                        isEdit ? "Интервал бронирования" : "Выберите интервал бронирования"
                    }
                >
                    <RuRangePicker
                        form={form}
                        isEdit={isEdit}
                        isBooking={!isEdit}
                        time_interval={editInterval}
                    />
                </Form.Item>
                <Form.Item
                    rules={[{required: true, message: "Введите сумму"}]}
                    name="amount"
                    label="Сумма бронирования"
                >
                    <Input placeholder="Сумма"/>
                </Form.Item>
                <Form.Item
                    name={isEdit ? "approved" : "notification"}
                    label={
                        isEdit ? "Подтверждено" : "Отправить уведомление пользователю?"
                    }
                >
                    <Switch/>
                </Form.Item>
                <Form.Item>
                    <Button
                        htmlType="submit"
                        style={{
                            width: "100%",
                        }}
                        variant="solid"
                        color="primary"
                        icon={<BookOutlined/>}
                    >
                        {isEdit ? "Сохранить" : "Забронировать"}
                    </Button>
                </Form.Item>
            </Form>
        </>
    );
};

export default BookingForm;

const finishBooking = async (
    form: FormInstance,
    setLoading: Dispatch<SetStateAction<boolean>>,
    msg: MessageInstance,
    setModal?: Dispatch<SetStateAction<boolean>>,
    isEdit?: boolean,
) => {
    setLoading(true);
    const values = form.getFieldsValue();
    const formData = new FormData();
    formData.append(
        "datetime_start",
        dayjs(values["time_interval"][0])
            .set("hour", 14)
            .set("minute", 0)
            .set("second", 0)
            .set("millisecond", 0)
            .unix()
            .toString()
    );
    formData.append(
        "datetime_end",
        dayjs(values["time_interval"][1])
            .set("hour", 13)
            .set("minute", 0)
            .set("second", 0)
            .set("millisecond", 0)
            .unix()
            .toString()
    );

    formData.append("user_id", values["user_id"] ?? "");
    formData.append("amount", values["amount"]);
    if ("from_panel" in values) {
        formData.append("from_panel", values["from_panel"]);
    }
    if ("notification" in values) {
        formData.append("notification", values["notification"]);
    }
    if ("id_rental" in values) {
        formData.append("id_rental", values["id_rental"]);
    }

    if ("approved" in values) {
        formData.append("approved", values["approved"]);
    }

    if ("rent_type" in values) {
        formData.append("rent_type", values["rent_type"]);
    }

    const response = await fetch(isEdit ? `${DB_URL}/update-rental` : `${DB_URL}/booking`, {
        method: "POST",
        body: formData,
    });

    if (response.ok) {
        const result = await response.json();
        if (result.success) {
            if (setModal) {
                setModal(false);
            }
            setLoading(false);
            msg.open({
                type: "success",
                content: "Бронирование успешно!",
            });
            return;
        }
    }
    setLoading(false);
    msg.open({
        type: "error",
        content: "Ошибка при бронировании!",
    });
    return;
};