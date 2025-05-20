"use client";
import styles from "./styles.module.scss";
import {Button, Tooltip} from "antd";
import {Suspense, useState} from "react";
import BookingsTable from "@/app/components/Pages/Bookings/BookingsTable/BookingsTable";
import FiltersModal from "@/app/components/Modals/FiltersModal/FiltersModal";
import {FilterOutlined, PlusOutlined} from "@ant-design/icons";
import BookingModal from "@/app/components/Modals/BookingModal/BookingModal";
import useMediaQuery from "@/app/hooks/useMediaQuery";

const Page = () => {
    const [modal, setModal] = useState<boolean>(false);
    const [booking, setBooking] = useState<boolean>(false);
    const isMobile = useMediaQuery("(max-width: 1024px)");
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
                </div>
                <Button icon={<FilterOutlined/>} onClick={() => setModal(true)}>
                    {isMobile ? "" : "Показать фильтры"}
                </Button>
            </div>
            <div className={styles["table-layout"]}>
                <Suspense fallback={<div>Loading...</div>}>
                    <BookingsTable/>
                </Suspense>
            </div>
        </div>
    );
};

export default Page;
