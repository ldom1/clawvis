#!/usr/bin/env bash
# Count core LabOS services up on localhost.

services=(
  "Debate:http://localhost:3010/"
  "OptimizerAPI:http://localhost:8000/docs"
  "Messidor:http://localhost:8501/"
  "PoeticShield:http://localhost:8503/docs"
  "KanbanAPI:http://localhost:8090/docs"
)

up=0
total=${#services[@]}

for entry in "${services[@]}"; do
  name="${entry%%:*}"
  url="${entry#*:}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url")
  [[ "$code" =~ ^2 ]] && up=$((up+1))
done

echo "Services up: $up/$total"

