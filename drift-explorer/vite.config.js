import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Deployed at the root of a dedicated subdomain: https://drift-explorer.getbarkley.com/
export default defineConfig({
  plugins: [react()],
  base: "/",
});
