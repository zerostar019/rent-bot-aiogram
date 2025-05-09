"use client";
import SideBar from '@/app/components/Layout/SideBar/SideBar';
import styles from './styles.module.scss';

export default function Layout({ children }: { children: React.ReactNode }) {
    return (
        <div
            className={styles['dashboard-layout']}
        >
            <SideBar
                className={styles['sidebar-position']}
            />
            {children}
        </div>
    )
}