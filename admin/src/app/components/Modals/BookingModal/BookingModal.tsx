"use client";
import { Modal } from "antd";
import React, { Dispatch, SetStateAction } from "react";
import BookingForm from "../../Pages/Bookings/BookingForm/BookingForm";
import useMediaQuery from "@/app/hooks/useMediaQuery";

const BookingModal = ({
  setModal,
  modal,
}: {
  setModal: Dispatch<SetStateAction<boolean>>;
  modal: boolean;
}) => {
  const isMobile = useMediaQuery("(max-width: 1024px)");
  return (
    <Modal
      centered
      title="Создание бронирования"
      open={modal}
      onClose={() => setModal(false)}
      onCancel={() => setModal(false)}
      footer={() => null}
      styles={
        isMobile
          ? {
              content: {
                padding: 10,
              },
            }
          : undefined
      }
    >
      <BookingForm setModal={setModal} />
    </Modal>
  );
};

export default BookingModal;
