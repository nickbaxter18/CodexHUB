FROM node:18-alpine

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY requirements.txt requirements-dev.txt ./

RUN pnpm install --frozen-lockfile

COPY . .

CMD ["node", "src/index.js"]
