#!/bin/bash

celery -A medialib_v2 worker \
    --loglevel=info \
    --concurrency="${CELERY_WORKERS:-2}" &
CELERY_PID=$!

IDLE_TIMEOUT=300
COUNTER=0
HAD_ACTIVE_TASKS=0

while kill -0 $CELERY_PID 2>/dev/null; do
    sleep 2
    
    ACTIVE_OUTPUT=$(celery -A medialib_v2 inspect active 2>/dev/null)
    INSPECT_STATUS=$?
    
    if [ "$INSPECT_STATUS" -ne 0 ]; then
        echo "Warning: failed to inspect Celery worker"
        COUNTER=0
        continue
    fi
    
    ACTIVE_TASKS=$(printf '%s\n' "$ACTIVE_OUTPUT" | grep -c "'id':" || true)
    
    if [ "$ACTIVE_TASKS" -gt 0 ]; then
        COUNTER=0
        HAD_ACTIVE_TASKS=1
    else
        COUNTER=$((COUNTER + 2))
    fi

    if [ "$COUNTER" -ge "$IDLE_TIMEOUT" ] && [ "$HAD_ACTIVE_TASKS" -eq 1 ]; then
        echo "Celery idle for ${IDLE_TIMEOUT}s. Stopping container for memory flush..."
        kill -15 $CELERY_PID
        wait $CELERY_PID
        exit 1
    elif [ "$COUNTER" -ge "$IDLE_TIMEOUT" ] && [ "$HAD_ACTIVE_TASKS" -eq 0 ]; then
        COUNTER=0
    fi
done
