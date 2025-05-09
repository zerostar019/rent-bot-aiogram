import classNames from "classnames";
import styles from "./styles.module.scss";
import { Card } from "antd";
import { SideMenuItems } from "./Menu";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

const SideBar = ({ className }: { className: string }) => {
    const [selected, setSelected] = useState<number>(0);
    const pathName = usePathname();

    useEffect(() => {
        const selectedItem: number = getSelectedPath(pathName);
        setSelected(selectedItem);
    }, [pathName])

    return (
        <Card
            className={classNames(styles['sidebar'], className)}
        >
            <div
                className={styles['sidebar-menu']}
            >
                {SideMenuItems.map((menuItem) => (
                    <Link
                        className={classNames(styles['sidebar-menu-item'], {
                            [styles['sidebar-menu-item-selected']]: selected === menuItem.id
                        })}
                        key={menuItem.id}
                        href={menuItem.link ?? "#"}
                    >
                        {menuItem.icon}
                        <span>
                            {menuItem.title}
                        </span>
                    </Link>
                ))}
            </div>
        </Card>
    )
}

export default SideBar;



function getSelectedPath(pathName: string): number {
    if (pathName.match("chat")) {
        return SideMenuItems.find(el => el.link ? el.link.match("chat") : 0)?.id ?? 0
    }
    else if (pathName.match("booking")) {
        return SideMenuItems.find(el => el.link ? el.link.match("booking") : 0)?.id ?? 0
    }
    return 0
}