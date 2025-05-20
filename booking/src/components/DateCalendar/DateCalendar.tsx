import {Calendar, ConfigProvider, Modal, Spin} from "antd";
import {Dayjs} from "dayjs";
import React, {Dispatch, SetStateAction, useEffect, useState} from "react";
import locale from "antd/locale/ru_RU";
import dayjs from "dayjs";
import "dayjs/locale/ru";
import {DatePickerInterface} from "../../types";
import {BACKEND_URL} from "../../constants";
import useSWR from "swr";
import {fetcher} from "../../utils/utils.tsx";

dayjs.locale("ru");

const DateCalendar = ({
                          setDate,
                          setOpen,
                          open,
                          selectedDate,
                      }: {
    setDate: Dispatch<SetStateAction<DatePickerInterface>>;
    setOpen: Dispatch<SetStateAction<boolean>>;
    open: boolean;
    selectedDate: DatePickerInterface;
}) => {
    const [loading, setLoading] = useState<boolean>(true);
    const [disabledDates, setDisabledDates] = useState<Dayjs[]>([]);
    const [fetchDate, setFetchDate] = useState<Dayjs>(dayjs());

    const {data: fetchedDays} = useSWR(
        selectedDate.date_start && !selectedDate.date_end ? `${BACKEND_URL}/get-busy?datetime_start=
        ${dayjs(selectedDate.date_start).startOf("date").startOf("day").unix()}
        &isSecondInterval=True`
            :
            `${BACKEND_URL}/get-busy?datetime_start=
        ${dayjs(fetchDate).startOf("date").startOf("day").unix()}
        `
        , fetcher);

    useEffect(() => {
        setLoading(true);
        if (open && !selectedDate.date_start && fetchedDays) {
            setFetchedBusyDates(setDisabledDates, setLoading, fetchedDays.data);
        }

        if (open && selectedDate.date_start && fetchedDays) {
            setFetchedBusyDates(setDisabledDates, setLoading, fetchedDays.data);
        }
    }, [open, fetchedDays, fetchDate, selectedDate.date_start]);

    return (
        <Modal
            centered
            open={open}
            onCancel={() => handleCloseModal(setDate, setOpen)}
            closeIcon={null}
            okText={"Выбрать"}
            cancelText={"Отмена"}
            okButtonProps={{
                disabled:
                    (selectedDate.date_start && !selectedDate.date_end)
                    ||
                    (!selectedDate.date_start && !selectedDate.date_end)
            }}
            onOk={() => setOpen(false)}
            onClose={() => handleCloseModal(setDate, setOpen)}
            loading={loading}
        >
            {loading && (
                <div
                    style={{
                        display: "grid",
                        placeItems: "center center",
                    }}
                >
                    <Spin size="default"/>
                </div>
            )}
            {!loading && (
                <ConfigProvider locale={locale}>
                    <Calendar
                        showWeek={false}
                        mode="month"
                        disabledDate={(date) => handleDisablingDates(date, disabledDates)}
                        fullscreen={false}
                        onSelect={(date, selectInfo) => {
                            if (selectInfo.source === "date")
                                handleChangeDate(setDate, date, selectedDate);
                        }}
                        fullCellRender={(date) => handleRenderCell(date, selectedDate)}
                        onPanelChange={(date, mode) => {
                            if (mode === "month") {
                                setFetchDate(date.startOf("month").startOf("day"));
                            }
                        }}
                    />
                </ConfigProvider>
            )}
        </Modal>
    );
};

export default DateCalendar;

const handleChangeDate = (
    setDate: Dispatch<SetStateAction<DatePickerInterface>>,
    date: Dayjs,
    selectedDate: DatePickerInterface,
) => {
    const {date_start, date_end} = selectedDate;
    if (!date_start && !date_end) {
        setDate({date_start: date, date_end: undefined});
    } else if (date_start && !date_end) {
        if (date_start.isSame(date, 'date')) return;
        if (date_start.isAfter(date, 'date')) {
            setDate({date_start: date, date_end: undefined});
            return
        }
        if (date_start.isSame(date, 'date')) {
            setDate({date_start: undefined, date_end: undefined});
            return
        }
        setDate({
            ...selectedDate,
            date_end: date
        });
    } else if (date_end && !date_start) {
        if (date_end.isSame(date, 'date')) return;
        if (date_end.isSame(date_start, 'date')) return;
        setDate({date_start: date, date_end: undefined});
    } else {
        setDate({date_start: date, date_end: undefined});
    }
};

const handleRenderCell = (date: Dayjs, selectedDate: DatePickerInterface) => {
    return (
        <div
            style={
                (selectedDate.date_start && date.isSame(selectedDate.date_start, 'date')
                    ||
                    selectedDate.date_end && date.isSame(selectedDate.date_end, 'date'))
                    ?
                    {
                        ...BookedDaysStyle,
                        borderTopLeftRadius: date.isSame(selectedDate.date_start, 'date')
                            ? "0.625rem"
                            : undefined,
                        borderBottomLeftRadius: date.isSame(selectedDate.date_start, 'date')
                            ? "0.625rem"
                            : undefined,
                        borderTopRightRadius: date.isSame(selectedDate.date_end, 'date')
                            ? "0.625rem"
                            : undefined,
                        borderBottomRightRadius: date.isSame(selectedDate.date_end, 'date')
                            ? "0.625rem"
                            : undefined,
                    }
                    : {
                        padding: "0.625rem",
                    }
            }
        >
            {date.get("D")}
        </div>
    );
};

const handleCloseModal = (
    setDate: Dispatch<SetStateAction<DatePickerInterface>>,
    setOpen: Dispatch<SetStateAction<boolean>>
) => {
    setDate({
        date_end: undefined,
        date_start: undefined,
    });
    setOpen(false);
};

const setFetchedBusyDates = async (
        setBusyDates: Dispatch<SetStateAction<Dayjs[]>>,
        setLoading: Dispatch<SetStateAction<boolean>>,
        dates: string[],
    ) => {
        const busyDates: Dayjs[] = [];
        dates.forEach((busyDate: string) => {
            busyDates.push(dayjs(busyDate, "DD.MM.YYYY"));
        });
        setBusyDates(busyDates);

        setLoading(false);
    }
;

const BookedDaysStyle: React.CSSProperties = {
    background: "rgb(140, 100, 255)",
    color: "#fff",
    padding: "0.625rem",
};

const handleDisablingDates = (date: Dayjs, disabledDates: Dayjs[]) => {
    const isDisabled = disabledDates.some((dd) => date.isSame(dd, "date"));
    const isPast = date.isBefore(dayjs(), "date");
    return isDisabled || isPast;
};
