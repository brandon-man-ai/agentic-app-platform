#!/bin/bash
set -e

echo "Starting backend..."
cd /app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting frontend..."
cd /app/frontend
PORT=3000 HOSTNAME=0.0.0.0 NODE_ENV=production NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 node server.js &
FRONTEND_PID=$!

echo "Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  echo "Waiting for backend... ($i/30)"
  sleep 1
done

echo "Waiting for frontend to be ready..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:3000/ > /dev/null 2>&1; then
    echo "Frontend is ready!"
    break
  fi
  echo "Waiting for frontend... ($i/30)"
  sleep 1
done

echo "Starting nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

echo "All services started!"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
