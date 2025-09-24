FROM node:20-slim AS node-deps

WORKDIR /app

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN corepack enable \
    && pnpm install --frozen-lockfile \
    && pnpm prune --prod

FROM python:3.11-slim AS python-wheels

WORKDIR /deps

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheelhouse -r requirements.txt

FROM node:20-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-wheels /wheelhouse /tmp/wheels
COPY requirements.txt ./requirements.txt

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-index --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --from=node-deps /app/node_modules ./node_modules
COPY . .

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD curl -f http://localhost:4000/health || exit 1

CMD ["node", "src/index.js"]
