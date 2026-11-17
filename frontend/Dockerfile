# syntax=docker/dockerfile:1

# ---------- build stage ----------
FROM node:24-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
# npm ci installs the locked versions; the second command adds any Linux-only native
# packages (Tailwind/Vite bindings) that a lockfile made on macOS can be missing.
RUN npm ci && npm install --no-save --no-audit --no-fund
COPY . .
# The browser talks to the API through nginx on the same origin
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---------- runtime stage: nginx running as a non-root user on port 8080 ----------
FROM nginxinc/nginx-unprivileged:stable-alpine
ENV NGINX_ENTRYPOINT_QUIET_LOGS=1
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD wget -qO /dev/null http://127.0.0.1:8080/ || exit 1
