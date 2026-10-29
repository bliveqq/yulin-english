#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  echo '请先复制 .env.example 为 .env，并填写服务器域名和资料路径。'
  exit 1
fi
if [ ! -f site/status.json ]; then
  echo '请先使用 Python 3.11 或以上版本运行 prepare.py --library 资料目录。'
  exit 1
fi
docker compose config --quiet
docker compose run --rm --no-deps yulin caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose up -d
printf '%s\n' '服务已启动。请检查公开 HTTPS 下载地址，启动成功不代表域名已生效。'
