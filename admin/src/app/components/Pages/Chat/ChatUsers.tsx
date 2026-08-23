"use client";
import classNames from "classnames";
import styles from "./styles.module.scss";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { DB_URL } from "@/app/constants";
import { ChatUsersInterface } from "@/app/types/Users";
import { Badge, Input, Skeleton } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import useSWR from "swr";
import { fetcher } from "@/app/utils/fetcher";
import { useVirtualizer } from "@tanstack/react-virtual";

const ROW_HEIGHT = 68;

/** Цвет аватара выводим из id — у каждого гостя он стабильный. */
const avatarTone = (id: number | undefined) => {
  const palette = [
    "#15665a", "#6b4c9a", "#9a5b1b", "#2f6b8f",
    "#8f2f4d", "#3f7d4e", "#7a5c2e", "#4a4f8f",
  ];
  return palette[Math.abs(Number(id ?? 0)) % palette.length];
};

const initials = (id: number | undefined) => String(id ?? "?").slice(-2);

/** Русское согласование: 1 новое, 2 новых, 5 новых. */
const unreadLabel = (count: number) => (count === 1 ? "1 новое" : `${count} новых`);

const unreadAria = (count: number) =>
  count === 1 ? "1 непрочитанное сообщение" : `${count} непрочитанных сообщений`;

const ChatUsers = ({
  className,
  selectedUser,
  setSelectedUser,
  setUsers,
  users,
}: {
  className: string;
  selectedUser: ChatUsersInterface | undefined;
  setSelectedUser: Dispatch<SetStateAction<ChatUsersInterface | undefined>>;
  users: ChatUsersInterface[];
  setUsers: Dispatch<SetStateAction<ChatUsersInterface[]>>;
}) => {
  const {
    data: usersData,
    error,
    isLoading,
  } = useSWR(DB_URL + "/chat-users", fetcher, { refreshInterval: 30000 });

  const [searchFilter, setSearchFilter] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Периодический ответ сервера раньше затирал список целиком вместе
  // со счётчиками, которые накрутил WebSocket. Теперь данные сливаются:
  // состав берём с сервера, непрочитанные — максимум из двух источников.
  useEffect(() => {
    if (!usersData?.data || isLoading) return;
    const incoming: ChatUsersInterface[] = usersData.data;
    setUsers((prev) => {
      const prevById = new Map(prev.map((u) => [u.user_id, u]));
      return incoming.map((u) => {
        const known = prevById.get(u.user_id);
        if (!known) return u;
        return {
          ...u,
          unread_count: Math.max(u.unread_count ?? 0, known.unread_count ?? 0),
        };
      });
    });
  }, [usersData, isLoading, setUsers]);

  // Открытый чат считается прочитанным.
  useEffect(() => {
    if (!selectedUser?.user_id) return;
    setUsers((prev) =>
      prev.some((u) => u.user_id === selectedUser.user_id && u.unread_count)
        ? prev.map((u) =>
            u.user_id === selectedUser.user_id ? { ...u, unread_count: 0 } : u
          )
        : prev
    );
  }, [selectedUser?.user_id, setUsers]);

  const visibleUsers = useMemo(() => {
    const list = Array.isArray(users) ? users : [];
    const query = searchFilter.trim();
    const filtered = query
      ? list.filter((u) => u?.user_id?.toString().includes(query))
      : list;
    // Непрочитанные — наверх, остальные сохраняют порядок сервера
    // (он уже отсортирован по времени последнего сообщения).
    return [...filtered].sort(
      (a, b) => (b.unread_count ?? 0) - (a.unread_count ?? 0)
    );
  }, [users, searchFilter]);

  const virtualizer = useVirtualizer({
    count: visibleUsers.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 8,
    getItemKey: (index) => visibleUsers[index]?.user_id ?? index,
  });

  const totalUnread = useMemo(
    () => visibleUsers.reduce((sum, u) => sum + (u.unread_count ?? 0), 0),
    [visibleUsers]
  );

  const onSearch = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setSearchFilter(e.target.value),
    []
  );

  const showSkeleton = isLoading && users.length === 0;

  return (
    <aside className={classNames(className, styles["users"])}>
      <header className={styles["users-head"]}>
        <div className={styles["users-title"]}>
          <h2>Чаты</h2>
          {totalUnread > 0 && (
            <span className={styles["users-title-count"]}>{totalUnread}</span>
          )}
        </div>
        <Input
          allowClear
          value={searchFilter}
          onChange={onSearch}
          prefix={<SearchOutlined />}
          placeholder="Поиск по ID гостя"
          aria-label="Поиск по ID гостя"
        />
      </header>

      <div className={styles["users-list"]} ref={scrollRef}>
        {showSkeleton && (
          <div className={styles["users-skeleton"]}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className={styles["users-skeleton-row"]}>
                <Skeleton.Avatar active shape="square" size={40} />
                <Skeleton.Input active size="small" block />
              </div>
            ))}
          </div>
        )}

        {!showSkeleton && error && (
          <p className={styles["users-empty"]}>
            Не удалось загрузить список. Проверьте соединение.
          </p>
        )}

        {!showSkeleton && !error && visibleUsers.length === 0 && (
          <p className={styles["users-empty"]}>
            {searchFilter
              ? `Ничего не найдено по запросу «${searchFilter}»`
              : "Пока нет ни одного обращения."}
          </p>
        )}

        {!showSkeleton && visibleUsers.length > 0 && (
          <div
            className={styles["users-virtual"]}
            style={{ height: virtualizer.getTotalSize() }}
          >
            {virtualizer.getVirtualItems().map((row) => {
              const user = visibleUsers[row.index];
              const active = selectedUser?.user_id === user?.user_id;
              return (
                <button
                  key={row.key}
                  type="button"
                  onClick={() => setSelectedUser(user)}
                  aria-current={active ? "true" : undefined}
                  aria-label={
                    user?.unread_count
                      ? `Гость ${user.user_id}, ${unreadAria(user.unread_count)}`
                      : `Гость ${user?.user_id}`
                  }
                  className={classNames(styles["user-card"], {
                    [styles["user-card-active"]]: active,
                  })}
                  style={{
                    height: row.size,
                    transform: `translateY(${row.start}px)`,
                  }}
                >
                  <span
                    className={styles["user-avatar"]}
                    style={{ background: avatarTone(user?.user_id) }}
                    aria-hidden="true"
                  >
                    {initials(user?.user_id)}
                  </span>
                  <span className={styles["user-meta"]}>
                    <span className={styles["user-id"]}>{user?.user_id}</span>
                    <span className={styles["user-sub"]}>
                      {user?.unread_count
                        ? unreadLabel(user.unread_count)
                        : "Прочитано"}
                    </span>
                  </span>
                  {!!user?.unread_count && (
                    <Badge
                      count={user.unread_count}
                      overflowCount={99}
                      style={{ background: "var(--accent)" }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
};

export default ChatUsers;

export function sortUsersByUnreadDesc(
  users: ChatUsersInterface[]
): ChatUsersInterface[] {
  return [...users].sort(
    (a, b) => (b.unread_count ?? 0) - (a.unread_count ?? 0)
  );
}
