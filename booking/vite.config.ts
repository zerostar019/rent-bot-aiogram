import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/booking",
  preview: {
    allowedHosts: ["zerostar0191.fvds.ru"],
  },
  server: {
    allowedHosts: ["zerostar0191.fvds.ru", "localhost"],
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
