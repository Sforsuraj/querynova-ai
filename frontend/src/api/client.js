import axios from "axios";

const rawUrl =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "http://localhost:8080" : "https://querynova-backend.vercel.app");

// Normalize origin by stripping trailing slashes and any trailing /api suffix
export const API_BASE_URL = rawUrl.trim().replace(/\/+$/, "").replace(/\/api$/i, "");

export function apiUrl(path) {
  const cleanPath = String(path).replace(/^\/+/, "");
  return `${API_BASE_URL}/${cleanPath}`;
}

export const api = axios.create({
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});
