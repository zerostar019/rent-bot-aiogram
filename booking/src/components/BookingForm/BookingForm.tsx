import styles from "./styles.module.css";
import {Button, ConfigProvider, Form, Input, message} from "antd";
import DateCalendar from "../DateCalendar/DateCalendar";
import {DatePickerInterface, UserDataInterface} from "../../types";
import {useCallback, useEffect, useRef, useState} from "react";
import {BACKEND_URL} from "../../constants";
import {MessageInstance} from "antd/es/message/interface";

const BookingForm = ({userData}: { userData: UserDataInterface }) => {
    const [selectedDate, setDate] = useState<DatePickerInterface>({
        date_start: undefined,
        date_end: undefined,
    });
    const [calendar, setCalendar] = useState<boolean>(false);
    const [messageApi, contextHolder] = message.useMessage({
        top: 100,
    });

    const userDataRef = useRef(userData);
    const selectedDateRef = useRef(selectedDate);

    useEffect(() => {
        userDataRef.current = userData;
    }, [userData]);

    useEffect(() => {
        selectedDateRef.current = selectedDate;
    }, [selectedDate]);

    const handleBookingClick = useCallback(() => {
        const currentSelectedDate = selectedDateRef.current;
        const currentUserData = userDataRef.current;
        handleBooking(currentSelectedDate, currentUserData, messageApi);
    }, [messageApi]);

    useEffect(() => {
        Telegram.WebApp.onEvent("mainButtonClicked", handleBookingClick);

        return () => {
            Telegram.WebApp.offEvent("mainButtonClicked", handleBookingClick);
        };
    }, [handleBookingClick]);

    useEffect(() => {
        if (selectedDate.date_end && selectedDate.date_start) {
            Telegram.WebApp.MainButton.enable();
            Telegram.WebApp.MainButton.color = "rgb(140, 100, 255)";
            Telegram.WebApp.MainButton.text = "Забронировать";
            Telegram.WebApp.MainButton.hasShineEffect = true;
            return;
        }
        Telegram.WebApp.MainButton.disable();
        Telegram.WebApp.MainButton.color = "#dcdcdc";
        Telegram.WebApp.MainButton.text = "Выберите даты";
        Telegram.WebApp.MainButton.hasShineEffect = false;
    }, [selectedDate, setDate]);

    return (
        <>
            {contextHolder}
            <DateCalendar
                selectedDate={selectedDate}
                setDate={setDate}
                open={calendar}
                setOpen={setCalendar}
            />
            <ConfigProvider
                theme={{
                    components: {
                        Input: {
                            colorText: "#fff",
                            colorTextDisabled: "#fff",
                        },
                    },
                }}
            >
                <Form
                    style={{
                        width: "100%",
                    }}
                    layout="vertical"
                >
                    <Form.Item
                        label={<span className={styles["label"]}>Даты проживания</span>}
                    >
                        <ConfigProvider
                            theme={{
                                components: {
                                    Button: {
                                        colorBgContainer: "rgb(108, 0, 162)",
                                        colorText: "#fff",
                                        colorBorder: "rgb(108, 0, 162)",
                                        algorithm: true,
                                    },
                                },
                            }}
                        >
                            <Button
                                size="large"
                                style={{
                                    width: "100%",
                                }}
                                onClick={() => setCalendar(true)}
                            >
                                Выбрать даты проживания
                            </Button>
                        </ConfigProvider>
                    </Form.Item>
                    {selectedDate.date_end && selectedDate.date_start && (
                        <>
                            <Form.Item
                                label={<span className={styles["label"]}>Дата заселения</span>}
                            >
                                <Input
                                    size="large"
                                    disabled
                                    value={`${selectedDate.date_start?.format(
                                        "DD.MM.YYYY"
                                    )} г. 14:00`}
                                />
                            </Form.Item>
                            <Form.Item
                                label={<span className={styles["label"]}>Дата выезда</span>}
                            >
                                <Input
                                    size="large"
                                    variant="filled"
                                    disabled
                                    value={`${selectedDate.date_end?.format(
                                        "DD.MM.YYYY"
                                    )} г. 12:00`}
                                />
                            </Form.Item>
                            <Form.Item
                                label={<span className={styles["label"]}>Итоговая сумма</span>}
                            >
                                <Input
                                    disabled
                                    value={`${selectedDate.date_end.diff(
                                        selectedDate.date_start,
                                        "days"
                                    )}0 000 рублей`}
                                    size="large"
                                />
                            </Form.Item>
                        </>
                    )}
                </Form>
            </ConfigProvider>
        </>
    );
};

export default BookingForm;

const handleBooking = async (
    selectedDate: DatePickerInterface,
    userData: UserDataInterface,
    messageApi: MessageInstance
) => {
    Telegram.WebApp.MainButton.disable();
    const formData = new FormData();
    if (selectedDate.date_end && selectedDate.date_start) {
        const amount: number =
            selectedDate.date_end.diff(selectedDate.date_start, "days") * 10000;
        formData.append(
            "datetime_start",
            selectedDate.date_start
                .set("hour", 14)
                .set("minute", 0)
                .set("second", 0)
                .set("millisecond", 0)
                .unix()
                .toString()
        );
        formData.append(
            "datetime_end",
            selectedDate.date_end
                .set("hour", 13)
                .set("minute", 0)
                .set("second", 0)
                .set("millisecond", 0)
                .unix()
                .toString()
        );
        formData.append("user_id", userData.userId!.toString());
        formData.append("query_id", userData.queryId!);
        formData.append("amount", amount.toString());
        const request = await fetch(`${BACKEND_URL}/booking`, {
            method: "POST",
            body: formData,
        });
        if (request.ok) {
            const result = await request.json();
            if (result.success) {
                messageApi.success("Успешно забронировано!");
                setTimeout(() => {
                    Telegram.WebApp.close();
                }, 1000);
                return;
            }
        }
        messageApi.error("Ошибка бронирования!");
        Telegram.WebApp.MainButton.enable();
        return;
    }
    messageApi.error("Ошибка бронирования!");
    Telegram.WebApp.MainButton.enable();
};
