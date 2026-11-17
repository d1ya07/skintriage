import axios from "axios";

const TOKEN_KEY = "skintriage_token";
export const AUTH_LOGOUT_EVENT = "auth:logout";

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api",
});

api.interceptors.request.use((config) => {
  const token = tokenStorage.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Expired or invalid token: wipe it and tell the app to log out.
    if (axios.isAxiosError(error) && error.response?.status === 401 && tokenStorage.get()) {
      tokenStorage.clear();
      window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
    }
    return Promise.reject(error);
  },
);
