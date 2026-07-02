# Dockerfile Template — HPU SaaS Frontend (Next.js 15 standalone)
# File: ~/hpu-dev/_shared/docker-templates/Dockerfile.nextjs

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build (next.config.ts must have output: 'standalone')
RUN corepack enable && pnpm build

# Stage 3: Runner (lightweight production)
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Copy standalone output (chỉ những file cần thiết)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

# Standalone output có server.js sẵn
CMD ["node", "server.js"]
