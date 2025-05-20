import { DB_URL } from "@/app/constants";
import useMediaQuery from "@/app/hooks/useMediaQuery";
import { fetcher } from "@/app/utils/fetcher";
import {
  CheckCircleFilled,
  CloseCircleFilled,
  EditOutlined,
} from "@ant-design/icons";
import { Button, Table, TablePaginationConfig } from "antd";
import { TableProps } from "antd/lib";
import dayjs from "dayjs";
import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

const BookingsTable = () => {
  const searchParams = useSearchParams();
  const { data: dataResponse, isLoading } = useSWR(
    searchParams
      ? `${DB_URL}/bookings?${new URLSearchParams(searchParams)}`
      : `${DB_URL}/bookings`,
    fetcher
  );
  const [tableData, setTableData] = useState<TableProps["dataSource"]>([]);
  const [pagination, setPagination] = useState<TableProps["pagination"]>();
  const router = useRouter();
  const isMobile = useMediaQuery("(max-width: 1024px)");
  useEffect(() => {
    if (dataResponse) {
      if (dataResponse.success) {
        const pagination = dataResponse.data;
        setPagination({
          total: pagination.total,
          pageSize: pagination.per_page,
          current: pagination.page,
          pageSizeOptions: [10, 15, 20, 50],
          defaultPageSize: 10,
        });
        const bookingsData = dataResponse.data.data;
        if (bookingsData.length > 0) {
          setTableData(bookingsData);
        } else {
          setTableData([]);
        }
      } else {
        setTableData([]);
      }
    }
  }, [dataResponse]);
  return (
    <Table
      loading={isLoading}
      bordered
      columns={isMobile ? DataColumnsMobile : DataColumns}
      dataSource={tableData}
      pagination={{
        ...pagination,
        showSizeChanger: true,
        pageSizeOptions: [5, 10, 15, 20, 50],
      }}
      onChange={(pag) => handleTableChange(pag, router)}
    />
  );
};

export default BookingsTable;

const DataColumnsMobile: TableProps["columns"] = [
  {
    key: "id_user",
    title: "Telegram ID",
    dataIndex: "id_user",
  },
  {
    key: "time_interval",
    title: "Даты бронирования",
    dataIndex: "time_interval",
    render: (interval: string) => {
      const newInterval = interval.replace("[", "").replace(")", "").split(",");
      return (
        <span>
          {dayjs(newInterval[0]).format("DD.MM.YYYY HH:mm")} -{" "}
          {dayjs(newInterval[1].replace(" ", "")).format("DD.MM.YYYY HH:mm")}
        </span>
      );
    },
  },
  {
    key: "actions",
    render: (data) => (
      <Link href={`/admin/dashboard/bookings/${data.id}`}>
        <Button icon={<EditOutlined />} />
      </Link>
    ),
  },
];

const handleTableChange = (
  pagination: TablePaginationConfig,
  router: AppRouterInstance
) => {
  const current = new URLSearchParams(window.location.search);
  current.set(
    "per_page",
    pagination.pageSize ? pagination.pageSize.toString() : "10"
  );
  current.set("page", pagination.current ? pagination.current.toString() : "1");
  router.push(`/admin/dashboard/bookings?${current}`);
};

const DataColumns: TableProps["columns"] = [
  {
    key: "id",
    title: "#",
    dataIndex: "id",
  },
  {
    key: "id_user",
    title: "Telegram ID",
    dataIndex: "id_user",
  },
  {
    key: "time_interval",
    title: "Даты бронирования",
    dataIndex: "time_interval",
    render: (interval: string) => {
      const newInterval = interval.replace("[", "").replace(")", "").split(",");
      return (
        <span>
          {dayjs(newInterval[0]).format("DD.MM.YYYY HH:mm")} -{" "}
          {dayjs(newInterval[1].replace(" ", "")).format("DD.MM.YYYY HH:mm")}
        </span>
      );
    },
  },
  {
    key: "rent_type",
    title: "Тип бронирования",
    dataIndex: "rent_type",
    render: (rentType) =>
      rentType === "daily" ? <span>Суточное</span> : <span>Почасовое</span>,
  },
  {
    key: "amount",
    title: "Сумма",
    dataIndex: "amount",
  },
  {
    key: "approved",
    title: "Подтверждено",
    dataIndex: "approved",
    align: "center",
    render: (approved) =>
      approved ? (
        <CheckCircleFilled
          style={{
            color: "#039487",
          }}
        />
      ) : (
        <CloseCircleFilled
          style={{
            color: "#1890ff",
          }}
        />
      ),
  },
  {
    key: "created_at",
    title: "Создано",
    dataIndex: "created_at",
    render: (createdAt) => (
      <span>{dayjs(createdAt).format("DD.MM.YYYY HH:mm:ss")}</span>
    ),
  },
  {
    key: "actions",
    render: (data) => (
      <Link href={`/admin/dashboard/bookings/${data.id}`}>
        <Button icon={<EditOutlined />} />
      </Link>
    ),
  },
];
