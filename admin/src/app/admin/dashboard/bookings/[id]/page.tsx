import BookingForm from "@/app/components/Pages/Bookings/BookingForm/BookingForm";
import styles from "./styles.module.scss";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { Button } from "antd";
import Link from "next/link";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Page = async ({ params }: { params: any }) => {
  const { id } = await params;
  return (
    <div className={styles["page-layout"]}
    >
      <div className={styles["page-header"]}>
        <Link href="/admin/dashboard/bookings">
          <Button
            variant="solid"
            icon={<ArrowLeftOutlined />}
            color="primary"
          />
        </Link>
        <span className={styles["page-title"]}>
          Редактирование бронирования
        </span>
      </div>
      <div className={styles["edit-form-layout"]}
      id={"edit-booking-form"}
      >
        <BookingForm isEdit editId={id} />
      </div>
    </div>
  );
};

export default Page;
