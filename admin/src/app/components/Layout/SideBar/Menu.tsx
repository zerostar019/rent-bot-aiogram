import { MenuItems } from "@/app/types/SideBarTypes";
import { CloseCircleFilled, FilterFilled, MessageFilled, PieChartFilled } from '@ant-design/icons';


export const SideMenuItems: MenuItems[] = [
    {
        id: 0,
        title: "Бронирования",
        icon: <PieChartFilled />,
        link: "/admin/dashboard/bookings"
    },
    {
        id: 1,
        title: "Чаты",
        icon: <MessageFilled />,
        link: "/admin/dashboard/chat"
    },
    {
        id: 2,
        title: "Отчеты",
        icon: <FilterFilled />
    },
    {
        id: 3,
        title: "Выход",
        icon: <CloseCircleFilled />
    }
]