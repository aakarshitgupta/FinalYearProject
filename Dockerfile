FROM node:20-bookworm

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
  && rm -rf /var/lib/apt/lists/*

COPY package.json pyproject.toml requirements.txt ./
COPY src ./src
COPY scripts ./scripts
COPY backend ./backend
COPY data ./data
COPY artifacts ./artifacts

RUN python3 -m venv /app/.venv
RUN /app/.venv/bin/pip install --upgrade pip
RUN /app/.venv/bin/pip install -r requirements.txt
RUN /app/.venv/bin/pip install -e .

RUN npm --prefix backend ci

EXPOSE 5050

CMD ["npm", "--prefix", "backend", "start"]
