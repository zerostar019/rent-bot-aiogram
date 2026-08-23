import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/booking/",
  preview: {
    allowedHosts: ["businesspochta.kazan.hlab.kz"],
    port: 8084,
    host: "0.0.0.0",
  },
  server: {
    allowedHosts: ["businesspochta.kazan.hlab.kz", "localhost"],
  },
  build: {
    target: "esnext",
    sourcemap: false,
    // terserOptions: {
    //   compress: {
    //     drop_console: true, // Remove console logs for production
    //   },
    // },
  },
});
