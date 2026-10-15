# syntax=docker/dockerfile:1
# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Optional build-time environment arguments for frontend bundling
ARG VITE_API_BASE_URL
ARG VITE_WS_URL

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

COPY app/ ./app/
COPY public/ ./public/
COPY tsconfig.json vite.config.ts react-router.config.ts ./

RUN npm run build

# ── Stage 2: Production Runner ────────────────────────────────────────────────
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Install only production dependencies
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy compiled artifacts from builder
COPY --from=builder /app/build ./build
COPY --from=builder /app/public ./public
COPY --from=builder /app/react-router.config.ts ./

EXPOSE 3000

CMD ["npm", "run", "start"]
