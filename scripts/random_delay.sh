#!/bin/bash
# Random delay between 60-600 seconds to humanize cron timing
DELAY=$(( RANDOM % 540 + 60 ))
echo "Sleeping $DELAY seconds..."
sleep "$DELAY"
