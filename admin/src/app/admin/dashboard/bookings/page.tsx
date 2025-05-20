"use client";
import styles from "./styles.module.scss";
import {Button, Tooltip} from "antd";
import React, {Suspense, useEffect, useState} from "react";
import BookingsTable from "@/app/components/Pages/Bookings/BookingsTable/BookingsTable";
import FiltersModal from "@/app/components/Modals/FiltersModal/FiltersModal";
import {FilterOutlined, PlusOutlined} from "@ant-design/icons";
import BookingModal from "@/app/components/Modals/BookingModal/BookingModal";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import ApprovedLabel from "@/app/components/Pages/Bookings/ApprovedLabel/ApprovedLabel";
import {init, isTMA, viewport} from "@telegram-apps/sdk";

const Page = ({searchParams}: { searchParams: never }) => {
    const [modal, setModal] = useState<boolean>(false);
    const [booking, setBooking] = useState<boolean>(false);
    const isMobile = useMediaQuery("(max-width: 1024px)");
    const [isApproved, setApproved] = useState<boolean>(false);

    const {approved} = React.use<{ approved?: boolean }>(searchParams)

    useEffect(() => {
        if (approved) {
            setApproved(true);
        } else {
            setApproved(false);
        }
    }, [approved])

    useEffect(() => {
        const initializeTelegramApp = async () => {
            if (isTMA()) {
                try {
                    init();
                    await viewport.mount();
                    if (viewport.expand.isAvailable()) {
                        viewport.expand();
                    }
                } catch (error) {
                    console.error("Ошибка инициализации Telegram Web App:", error);
                }
            } else {
                console.log("Приложение должно быть запущено внутри Telegram!");
            }
        };

        initializeTelegramApp();

        // Очистка при размонтировании
        return () => {
            viewport.unmount();
        };
    }, []);

    return (
        <div className={styles["page-layout"]}>
            <FiltersModal open={modal} setOpen={setModal}/>
            <BookingModal setModal={setBooking} modal={booking}/>
            <div className={styles["page-header"]}>
                <div className={styles["page-header-title"]}>
                    <Tooltip title="Добавить бронирование">
                        <Button
                            onClick={() => setBooking(true)}
                            color="primary"
                            variant="solid"
                            icon={<PlusOutlined/>}
                        />
                    </Tooltip>
                    <span
                        className={styles["page-title"]}
                    >
                        Бронирования
                    </span>
                    {!isMobile && <ApprovedLabel approved={isApproved} isMobile={isMobile}/>}
                </div>
                <Button icon={<FilterOutlined/>} onClick={() => setModal(true)}>
                    {isMobile ? "" : "Показать фильтры"}
                </Button>
            </div>
            <div className={styles["table-layout"]}>
                {isMobile && <ApprovedLabel approved={isApproved} isMobile={isMobile}/>}
                <Suspense fallback={<div>Loading...</div>}>
                    <BookingsTable/>
                </Suspense>
            </div>
        </div>
    );
};

export default Page;
