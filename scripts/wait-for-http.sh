#!/bin/sh
set -e

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <url> -- <command> [args...]"
  exit 1
fi

WAIT_URL="$1"
shift

if [ "$1" != "--" ]; then
  echo "Usage: $0 <url> -- <command> [args...]"
  exit 1
fi
shift

echo "Waiting for $WAIT_URL to respond..."
until curl -fsS -o /dev/null "$WAIT_URL"; do
  sleep 2
done
echo "$WAIT_URL is available."

exec "$@"
