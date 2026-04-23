#!/bin/sh
set -eu

: "${github_repo:?Missing required env var: github_repo}"
: "${github_token:?Missing required env var: github_token}"

mkdir -p /workspace/app/.local/pregrade

python /workspace/app/github_folder_sync.py /workspace/app/.local/pregrade "$github_repo" --token "$github_token" &

exec python /workspace/app/app.py
