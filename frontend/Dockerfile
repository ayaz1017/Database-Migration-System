# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for caching
COPY package.json package-lock.json* \
    yarn.lock* pnpm-lock.yaml* ./

# Install dependencies
RUN npm ci --frozen-lockfile || npm install

# Copy source code
COPY . .

# Build args
ARG VITE_API_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Build production bundle
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist \
    /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s \
    --timeout=5s \
    --retries=3 \
    CMD wget -q --spider \
    http://localhost:80/health \
    || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
