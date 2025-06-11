import {MenuItems} from "@/app/types/SideBarTypes";
import {MessageFilled, PieChartFilled, SettingFilled} from '@ant-design/icons';


export const SideMenuItems: MenuItems[] = [
    {
        id: 0,
        title: "Бронирования",
        icon: <PieChartFilled/>,
        link: "/admin/dashboard/bookings"
    },
    {
        id: 1,
        title: "Чаты",
        icon: <MessageFilled/>,
        link: "/admin/dashboard/chat"
    },
    {
        id: 2,
        title: "Настройки",
        icon: <SettingFilled/>,
        link: "/admin/dashboard/settings"
    }
]