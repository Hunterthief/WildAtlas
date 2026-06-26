#!/bin/bash
# WildAtlas auto-restart wrapper — keeps the dev server alive.
# If the server crashes, it restarts automatically within 2 seconds.
cd /home/z/my-project

while true; do
  echo "[$(date +%H:%M:%S)] Starting Next.js dev server..."
  bun node_modules/.bin/next dev -p 3000 > dev.log 2>&1
  EXIT_CODE=$?
  echo "[$(date +%H:%M:%S)] Server exited with code $EXIT_CODE. Restarting in 2s..."
  sleep 2
done
