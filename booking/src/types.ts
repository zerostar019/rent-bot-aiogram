import { Dayjs } from "dayjs";

export interface DatePickerInterface {
  date_start: Dayjs | undefined;
  date_end: Dayjs | undefined;
}

export interface UserDataInterface {
  userId: number | undefined;
  queryId: string | undefined;
}
