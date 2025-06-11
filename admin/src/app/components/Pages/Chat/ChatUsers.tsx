"use client";
import classNames from "classnames";
import styles from "./styles.module.scss";
import {Dispatch, SetStateAction, useEffect, useMemo, useState} from "react";
import {DB_URL} from "@/app/constants";
import {ChatUsersInterface} from "@/app/types/Users";
import {Avatar, Badge, Input, message, Result, Spin} from "antd";
import {UserOutlined} from "@ant-design/icons";
import {debounce} from "lodash";
import {scrollDown} from "@/app/utils/utils";
import useSWR from "swr";
import {fetcher} from "@/app/utils/fetcher";

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
    } = useSWR(DB_URL + "/chat-users", fetcher, {
        refreshInterval: 30000,
    });
    const [messageApi, contextHolder] = message.useMessage();
    const [loading, setLoading] = useState<boolean>(true);
    const [searchFilter, setSearchFilter] = useState<string>("");
    const [filteredUsers, setFilteredUsers] = useState<ChatUsersInterface[]>([]);

    useEffect(() => {
        if (usersData && !isLoading) {
            // const sortedUsers = sortUsersByUnreadDesc(usersData.data);
            setUsers(usersData.data);
            setFilteredUsers(usersData.data);
            setLoading(false);
        }
        if (error) {
            messageApi.error("Ошибка загрузки пользователей!");
            setLoading(false);
            return;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [usersData, error, messageApi]);

    useMemo(() => {
        if (Array.isArray(users)) {
            if (searchFilter !== "") {
                const newUsers = users.filter((user) =>
                    user?.user_id?.toString().includes(searchFilter)
                );
                const sortedUsers = sortUsersByUnreadDesc(newUsers);
                setFilteredUsers(sortedUsers);
            } else {
                // const sortedUsers = sortUsersByUnreadDesc(users);
                setFilteredUsers(users);
            }
        } else {
            // const sortedUsers = sortUsersByUnreadDesc(users);
            setFilteredUsers(users);
        }
    }, [users, searchFilter]);

    useEffect(() => {
        setTimeout(() => scrollDown(), 500);
        if (users && users.length > 0) {
            const newUsers = users.map((user) => {
                if (user.user_id === selectedUser?.user_id) {
                    return {
                        ...user,
                        unread_count: 0,
                    };
                }
                return {...user};
            });
            // const sortedUsers = sortUsersByUnreadDesc(newUsers);
            setUsers(newUsers);
            setFilteredUsers(newUsers);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedUser, setSelectedUser]);

    return (
        <div className={classNames(className)}>
            {contextHolder}
            <div>
                <Input
                    onChange={debounce((e) => setSearchFilter(e.target.value), 500)}
                    placeholder="Поиск..."
                />
            </div>
            {filteredUsers &&
                filteredUsers.length > 0 &&
                !loading &&
                filteredUsers.map((user: ChatUsersInterface | undefined) => (
                    <div
                        key={user?.user_id}
                        onClick={() => setSelectedUser(user)}
                        className={classNames(styles["user-card"], {
                            [styles["user-card-selected"]]:
                                selectedUser?.user_id === user?.user_id,
                        })}
                    >
                        <div>
                            <Avatar icon={<UserOutlined/>} shape="square"/> {user?.user_id}
                        </div>
                        <span>
              <Badge count={user?.unread_count}/>
            </span>
                    </div>
                ))}
            {loading && (
                <div className={styles["loader-layout"]}>
                    <div className={styles["loader-info"]}>
                        <Spin/>
                        <span>Загрузка пользователей...</span>
                    </div>
                </div>
            )}
            {!loading && filteredUsers && filteredUsers.length === 0 && (
                <div className={styles["loader-layout"]}>
                    <div className={styles["loader-info"]}>
                        <Result subTitle="Пользователи не найдены"/>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatUsers;

export function sortUsersByUnreadDesc(
    users: ChatUsersInterface[]
): ChatUsersInterface[] {
    return [...users].sort((a, b) => {
        const countA = a.unread_count ?? 0;
        const countB = b.unread_count ?? 0;
        return countB - countA;
    });
}
