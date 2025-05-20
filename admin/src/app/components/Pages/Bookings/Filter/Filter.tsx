"use client";
import { Button, Form, Input, Space, Switch } from "antd";
import RuRangePicker from "../RuRangePicker/RuRangePicker";
import { ClearOutlined, SearchOutlined } from "@ant-design/icons";
import { FormInstance } from "antd/lib";
import { useRouter } from "next/navigation";
import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { Dispatch, SetStateAction, useEffect, useState } from "react";

const Filter = ({
  setClose,
}: {
  setClose: Dispatch<SetStateAction<boolean>>;
}) => {
  const [form] = Form.useForm();
  const router = useRouter();
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const current = new URLSearchParams(window.location.search);
    if (current.get("amount_to")) {
      form.setFieldValue("amount_to", current.get("amount_to"));
    }
    if (current.get("amount_from")) {
      form.setFieldValue("amount_from", current.get("amount_from"));
    }
    if (current.get("time_interval")) {
      const time_interval = String(current.get("time_interval")).split(",");
      form.setFieldValue("time_interval", time_interval);
    }
    if (current.get("approved")) {
      form.setFieldValue("approved", current.get("approved"));
    }
  }, [form]);

  return (
    <Form
      layout="vertical"
      initialValues={{ approved: true }}
      onFinish={() => handleSetFilters(form, router, setClose, setLoading)}
      form={form}
    >
      <Form.Item label="Сумма (₽)">
        <Space.Compact>
          <Form.Item noStyle name={"amount_from"}>
            <Input
              placeholder="От"
              onChange={(val) =>
                form.setFieldValue("amount", { from: val.target.value })
              }
            />
          </Form.Item>
          <Form.Item noStyle name={"amount_to"}>
            <Input
              onChange={(val) =>
                form.setFieldValue("amount", { to: val.target.value })
              }
              placeholder="До"
            />
          </Form.Item>
        </Space.Compact>
      </Form.Item>
      <Form.Item label="Интервал бронирований" name="time_interval">
        <RuRangePicker form={form} />
      </Form.Item>
      <Form.Item label="Подтвержденные бронирования" name="approved">
        <Switch />
      </Form.Item>
      <Form.Item>
        <Button
          loading={loading}
          icon={<SearchOutlined />}
          type="primary"
          variant="solid"
          htmlType="submit"
          style={{
            width: "100%",
          }}
        >
          Поиск
        </Button>
      </Form.Item>
      <Form.Item>
        <Button
          disabled={loading}
          onClick={() =>
            form.resetFields(["amount_from", "amount_to", "time_interval"])
          }
          style={{
            width: "100%",
          }}
          icon={<ClearOutlined />}
        >
          Очистить фильтры
        </Button>
      </Form.Item>
    </Form>
  );
};

export default Filter;

const handleSetFilters = (
  form: FormInstance,
  router: AppRouterInstance,
  setClose: Dispatch<SetStateAction<boolean>>,
  setLoading: Dispatch<SetStateAction<boolean>>
) => {
  setLoading(true);
  const fieldValues = form.getFieldsValue();
  const current = new URLSearchParams(window.location.search);
  if ("amount_from" in fieldValues) {
    if (form.getFieldValue("amount_from")) {
      current.set("amount_from", form.getFieldValue("amount_from"));
    } else {
      current.delete("amount_from");
    }
  }
  if ("amount_to" in fieldValues) {
    if (form.getFieldValue("amount_to")) {
      current.set("amount_to", form.getFieldValue("amount_to"));
    } else {
      current.delete("amount_to");
    }
  }
  if ("time_interval" in fieldValues) {
    if (form.getFieldValue("time_interval")) {
      const time_interval = Array(form.getFieldValue("time_interval")).join(
        ","
      );
      current.set("time_interval", time_interval);
    } else {
      current.delete("time_interval");
    }
  }
  if ("approved" in fieldValues) {
    if (form.getFieldValue("approved")) {
      current.set("approved", form.getFieldValue("approved"));
    } else {
      current.delete("approved");
    }
  }

  setClose(false);
  router.push(`/admin/dashboard/bookings?` + current);
  setLoading(false);
};
