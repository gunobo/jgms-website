FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
# Baked into the built JS at build time (not read at container start), so
# this must be passed as a build arg — see docker-compose.yml's build.args.
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
# `npm run build` also runs `tsc -b` (full type-check) first, which is far
# heavier than the actual bundling step and not needed to produce working
# output — type errors are already caught during development. Skip it here
# so the build doesn't crawl on resource-constrained hosts (e.g. a Pi).
RUN npx vite build

FROM node:22-slim
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
