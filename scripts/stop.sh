#!/bin/bash
echo "Stopping Fluxline..."
docker compose --env-file .env.docker down
echo "All services stopped."
