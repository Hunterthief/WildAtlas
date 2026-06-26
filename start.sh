#!/bin/bash
# WildAtlas startup script with auto-restart.
# Starts the Next.js dev server and keeps it alive (auto-restarts on crash).
# Also pre-warms all routes so the Turbopack dev server doesn't crash
# on browser navigation.

cd /home/z/my-project

# Kill any existing instances
pkill -f "next dev" 2>/dev/null
pkill -f "dev-keepalive" 2>/dev/null
sleep 2

# Start the auto-restart wrapper
nohup bash dev-keepalive.sh > keepalive.log 2>&1 &

# Wait for server to be ready
echo "Starting Next.js dev server (with auto-restart)..."
for i in $(seq 1 15); do
  if curl -s -m 2 -o /dev/null "http://localhost:3000/" 2>/dev/null; then
    echo "Server is up."
    break
  fi
  sleep 1
done

# Pre-warm all routes (compiles them so browser navigation doesn't crash)
echo "Pre-warming routes..."
curl -s -m 15 "http://localhost:3000/" > /dev/null 2>&1
curl -s -m 15 "http://localhost:3000/animals-data.json" > /dev/null 2>&1
curl -s -m 15 "http://localhost:3000/api/search?q=test" > /dev/null 2>&1
curl -s -m 15 "http://localhost:3000/?name=Tiger&featured=1" > /dev/null 2>&1
curl -s -m 15 "http://localhost:3000/?name=Lion" > /dev/null 2>&1
curl -s -m 15 "http://localhost:3000/?compare=1" > /dev/null 2>&1
sleep 2

echo "Server ready and routes pre-warmed."
echo "  Home:    http://localhost:3000/"
echo "  Detail:  http://localhost:3000/?name=Tiger&featured=1"
echo "  Compare: http://localhost:3000/?compare=1"
echo "Cache: $(ls data/cache/wikipedia/ 2>/dev/null | wc -l) animals cached"
echo "Auto-restart: ENABLED (server will restart if it crashes)"
