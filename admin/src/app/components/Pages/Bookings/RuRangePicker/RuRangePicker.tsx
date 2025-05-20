import {DB_URL} from "@/app/constants";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import {fetcher} from "@/app/utils/fetcher";
import {ConfigProvider, DatePicker} from "antd";
import {FormInstance} from "antd/lib";
import locale from "antd/locale/ru_RU";
import dayjs, {Dayjs} from "dayjs";
import "dayjs/locale/ru";
import {useEffect, useState} from "react";
import useSWR from "swr";

dayjs.locale("ru");

const RuRangePicker = ({
                           form,
                           isBooking,
                           isEdit,
                           time_interval,
                       }: {
    form: FormInstance;
    isBooking?: boolean;
    isEdit?: boolean;
    time_interval?: string;
}) => {
    const [busyDates, setBusyDates] = useState<Dayjs[]>([]);
    const [leftPanelDate, setLeftPanelDate] = useState<Dayjs>(dayjs());
    const isMobile = useMediaQuery("(max-width: 1024px)");
    const [open, setOpen] = useState<boolean>(false);
    const [rightPanelDate, setRightPanelDate] = useState<Dayjs>(
        dayjs().add(1, "month")
    );
    const {data: leftDates} = useSWR(
        isBooking || leftPanelDate || isEdit
            ? `${DB_URL}/get-busy?datetime_start=${leftPanelDate
                .startOf("month")
                .startOf("day")
                .unix()}`
            : null,
        fetcher
    );
    const {data: rightDates} = useSWR(
        isBooking || leftPanelDate || isEdit
            ? `${DB_URL}/get-busy?datetime_start=${rightPanelDate
                .startOf("month")
                .startOf("day")
                .unix()}`
            : null,
        fetcher
    );
    const [value, setValue] =
        useState<
            [start: Dayjs | null | undefined, end: Dayjs | null | undefined]
        >();

    useEffect(() => {
        if (form.getFieldValue("time_interval")) {
            const time_interval = String(form.getFieldValue("time_interval")).split(
                ","
            );
            const start = dayjs(time_interval[0]);
            const end = dayjs(time_interval[1]);
            setValue([start, end]);
        }

        if (time_interval && isEdit) {
            const t_interval = time_interval.split(",");
            const start = dayjs(t_interval[0]);
            const end = dayjs(t_interval[1]);
            form.setFieldValue("time_interval", [start, end]);
            setValue([start, end]);
        }
    }, [form, isEdit, time_interval]);

    useEffect(() => {
        if (
            rightDates &&
            rightDates.data &&
            (isBooking || isEdit) &&
            leftDates &&
            leftDates.data
        ) {
            const result = [...leftDates.data, ...rightDates.data];
            const bDates: Dayjs[] = [];
            result.forEach((busyDate: string) => {
                bDates.push(dayjs(busyDate, "DD.MM.YYYY"));
            });
            setBusyDates(bDates);
        }
    }, [rightDates, leftDates, isBooking, isEdit]);

    useEffect(() => {
        if (isMobile && open) {
            document.body.style.overflow = "hidden";
            const pickerModal: HTMLElement | null =
                document.querySelector(".ant-modal");
            const editForm: HTMLDivElement | null = document.querySelector("#edit-booking-form");
            const pickerPanels: NodeListOf<HTMLDivElement> =
                document.querySelectorAll(".ant-picker-date-panel");
            const pickerBody: NodeListOf<HTMLDivElement> =
                document.querySelectorAll(".ant-picker-body");
            const pickerHeader: NodeListOf<HTMLDivElement> =
                document.querySelectorAll(".ant-picker-header");

            if (pickerPanels.length > 0 && editForm) {
                const width: number = (editForm.clientWidth - 20) / 2;
                console.log(width);
                pickerPanels.forEach((panel) => {
                    panel.style.width = `${width}px`;
                });
            }

            if (pickerPanels.length > 0 && pickerModal) {
                const width: number = (pickerModal.clientWidth - 20) / 2;
                pickerPanels.forEach((panel) => {
                    panel.style.width = `${width}px`;
                });
            }
            if (pickerBody.length > 0) {
                pickerBody.forEach((panel) => {
                    panel.style.padding = `2px 5px`;
                });
            }
            if (pickerHeader.length > 0) {
                pickerHeader.forEach((panel) => {
                    panel.style.padding = `0px`;
                });
            }
        }
        if (!open && isMobile) {
            document.body.style.overflow = "unset";
        }
    }, [isMobile, open]);

    return (
        <ConfigProvider locale={locale}>
            <DatePicker.RangePicker
                id="datepicker-range"
                inputReadOnly
                getPopupContainer={
                    isMobile
                        ? () => document.getElementById("booking-form") ?? document.body
                        : undefined
                }
                onOpenChange={(open) => setOpen(open)}
                mode={["date", "date"]}
                onPanelChange={(date) => {
                    setLeftPanelDate(
                        date[0]?.startOf("month").startOf("day") ?? leftPanelDate
                    );
                    setRightPanelDate(
                        date[1]?.startOf("month").startOf("day") ??
                        leftPanelDate.add(1, "month")
                    );
                }}
                onChange={(_, datesString) =>
                    form.setFieldValue("time_interval", datesString)
                }
                placeholder={["От", "До"]}
                value={isBooking && !isEdit ? undefined : value ?? undefined}
                disabledDate={
                    isBooking || isEdit
                        ? (date) => handleDisablingDates(date, busyDates)
                        : undefined
                }
                style={{
                    width: "100%",
                }}
            />
        </ConfigProvider>
    );
};

export default RuRangePicker;

const handleDisablingDates = (date: Dayjs, disabledDates: Dayjs[]) => {
    const isDisabled = disabledDates.some((dd) => date.isSame(dd, "day"));
    const isPast = date.isBefore(dayjs(), "day");
    return isDisabled || isPast;
};
