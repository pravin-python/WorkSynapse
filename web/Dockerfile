FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Security headers in nginx config
RUN rm /etc/nginx/conf.d/default.conf.bak 2>/dev/null || true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
