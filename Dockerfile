FROM node:18-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache python3 py3-pip build-base \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY requirements.txt requirements-dev.txt ./

RUN pnpm install --frozen-lockfile
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 4000

CMD ["node", "src/index.js"]
