import { Dayjs } from "dayjs";

export interface WebSocketMessage {
  id: number;
  user_id: number;
  message: string;
  file_id?: number;
  created_at: Dayjs;
  read_at?: Dayjs;
  file?: {
    file_name: string;
    data: string;
  };
}
