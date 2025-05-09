import useSWR from "swr";
import { DB_URL } from "../constants";
import { fetcher } from "../utils/fetcher";

const useMessages = (user_id: number | undefined) => {
  const {
    data: userMessages,
    isLoading,
    error,
    mutate,
  } = useSWR(user_id ? `${DB_URL}/user/chat?user_id=${user_id}` : null, fetcher);
  return { userMessages, isLoading, error, mutate };
};

export default useMessages;