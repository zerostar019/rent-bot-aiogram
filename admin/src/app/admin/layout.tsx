import { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
    "title": "Панель администратора"
}

export default function Layout({ children }: { children: React.ReactNode }) {
    return children
}