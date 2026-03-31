#!/bin/bash
# ============================================================================
#  Krisis — System Startup Script
#  Orchestrates environment validation, Docker builds, service startup,
#  health checks, and status reporting.
#
#  Usage:
#    ./scripts/startup.sh                  # Production (default)
#    ./scripts/startup.sh --dev            # Development mode
#    ./scripts/startup.sh --monitoring     # Production + Prometheus/Grafana
#    ./scripts/startup.sh --rebuild        # Force rebuild images
#    ./scripts/startup.sh --down           # Graceful shutdown (keeps volumes)
#    ./scripts/startup.sh --down --purge   # Shutdown + delete DB volumes
# ============================================================================
set -euo pipefail

# ── Colours & Symbols ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'  # No Colour

CHECK="${GREEN}✔${NC}"
CROSS="${RED}✘${NC}"
WARN="${YELLOW}⚠${NC}"
ARROW="${CYAN}➜${NC}"

# ── Defaults ────────────────────────────────────────────────────────────────
MODE="prod"
MONITORING=false
REBUILD=false
SHUTDOWN=false
PURGE=false

# ── Parse Arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev)        MODE="dev";       shift ;;
    --prod)       MODE="prod";      shift ;;
    --monitoring) MONITORING=true;  shift ;;
    --rebuild)    REBUILD=true;     shift ;;
    --down)       SHUTDOWN=true;    shift ;;
    --purge)      PURGE=true;       shift ;;
    -h|--help)
      echo ""
      echo -e "${BOLD}Krisis System Startup${NC}"
      echo ""
      echo "Usage:  ./scripts/startup.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --dev          Development mode (hot-reload, exposed ports)"
      echo "  --prod         Production mode  (default)"
      echo "  --monitoring   Also start Prometheus + Grafana"
      echo "  --rebuild      Force Docker image rebuild"
      echo "  --down         Graceful shutdown (preserves DB volume)"
      echo "  --purge        With --down, also delete DB volumes"
      echo "  -h, --help     Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo -e "${CROSS} Unknown option: $1"
      exit 1
      ;;
  esac
done

# ── Resolve Project Root ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Banner ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║              KRISIS — System Startup                 ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${DIM}Mode:${NC}        ${BOLD}${MODE}${NC}"
echo -e "  ${DIM}Monitoring:${NC}  ${MONITORING}"
echo -e "  ${DIM}Rebuild:${NC}     ${REBUILD}"
echo -e "  ${DIM}Timestamp:${NC}   $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# ── Helper: Print a section header ──────────────────────────────────────────
section() {
  echo ""
  echo -e "${BOLD}${CYAN}── $1 ──${NC}"
}

# ── Helper: Wait for HTTP health endpoint ───────────────────────────────────
wait_for_health() {
  local url="$1"
  local name="$2"
  local max_attempts="${3:-30}"
  local attempt=1

  echo -ne "  ${ARROW} Waiting for ${BOLD}${name}${NC} "

  while [ $attempt -le $max_attempts ]; do
    if curl -sf "$url" > /dev/null 2>&1; then
      echo -e " ${CHECK} ready (${attempt}s)"
      return 0
    fi
    echo -n "."
    sleep 1
    ((attempt++))
  done

  echo -e " ${CROSS} timed out after ${max_attempts}s"
  return 1
}

# ── Shutdown Mode ───────────────────────────────────────────────────────────
if [ "$SHUTDOWN" = true ]; then
  section "Shutting down services"

  DOWN_FLAGS=""
  if [ "$PURGE" = true ]; then
    DOWN_FLAGS="-v"
    echo -e "  ${WARN} Purge mode: database volumes will be deleted"
  fi

  if [ "$MODE" = "dev" ]; then
    echo -e "  ${ARROW} Stopping dev stack..."
    docker compose down $DOWN_FLAGS
  else
    echo -e "  ${ARROW} Stopping production stack..."
    docker compose -f docker-compose.prod.yml --env-file .env.prod down $DOWN_FLAGS

    if [ "$MONITORING" = true ]; then
      echo -e "  ${ARROW} Stopping monitoring stack..."
      docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml \
        --env-file .env.prod down $DOWN_FLAGS
    fi
  fi

  echo ""
  echo -e "  ${CHECK} All services stopped."
  echo ""
  exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════
#  PREFLIGHT CHECKS
# ═══════════════════════════════════════════════════════════════════════════
section "Preflight checks"

PREFLIGHT_OK=true

# 1. Docker daemon
if docker info > /dev/null 2>&1; then
  echo -e "  ${CHECK} Docker daemon is running"
else
  echo -e "  ${CROSS} Docker daemon is not running — please start Docker Desktop"
  PREFLIGHT_OK=false
fi

# 2. Docker Compose
if docker compose version > /dev/null 2>&1; then
  COMPOSE_VER=$(docker compose version --short 2>/dev/null || docker compose version | grep -oP '\d+\.\d+\.\d+')
  echo -e "  ${CHECK} Docker Compose ${DIM}(${COMPOSE_VER})${NC}"
else
  echo -e "  ${CROSS} Docker Compose not found — install Docker Compose v2"
  PREFLIGHT_OK=false
fi

# 3. Environment file
if [ "$MODE" = "prod" ]; then
  ENV_FILE=".env.prod"
else
  ENV_FILE=".env"
fi

if [ -f "$ENV_FILE" ]; then
  echo -e "  ${CHECK} Environment file ${DIM}(${ENV_FILE})${NC}"
else
  echo -e "  ${CROSS} Missing ${ENV_FILE} — copy from .env.example and fill in values"
  PREFLIGHT_OK=false
fi

# 4. Required files
REQUIRED_FILES=("docker-compose.yml" "Dockerfile")
if [ "$MODE" = "prod" ]; then
  REQUIRED_FILES=("docker-compose.prod.yml" "Dockerfile.prod" "nginx/nginx.nossl.conf" "scripts/init_db.sh" "alembic.ini")
fi

for f in "${REQUIRED_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo -e "  ${CHECK} ${DIM}${f}${NC}"
  else
    echo -e "  ${CROSS} Missing required file: ${f}"
    PREFLIGHT_OK=false
  fi
done

# 5. Validate prod env vars
if [ "$MODE" = "prod" ] && [ -f "$ENV_FILE" ]; then
  MISSING_VARS=()
  for var in DB_USER DB_PASSWORD DB_NAME; do
    if ! grep -q "^${var}=" "$ENV_FILE" 2>/dev/null; then
      MISSING_VARS+=("$var")
    fi
  done
  if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "  ${CROSS} Missing env vars in ${ENV_FILE}: ${MISSING_VARS[*]}"
    PREFLIGHT_OK=false
  else
    echo -e "  ${CHECK} Required env vars present ${DIM}(DB_USER, DB_PASSWORD, DB_NAME)${NC}"
  fi
fi

# 6. Port availability
check_port() {
  local port=$1
  local name=$2
  if command -v ss > /dev/null 2>&1; then
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
      echo -e "  ${WARN} Port ${port} (${name}) is already in use"
    else
      echo -e "  ${CHECK} Port ${port} available ${DIM}(${name})${NC}"
    fi
  elif command -v lsof > /dev/null 2>&1; then
    if lsof -i :"$port" > /dev/null 2>&1; then
      echo -e "  ${WARN} Port ${port} (${name}) is already in use"
    else
      echo -e "  ${CHECK} Port ${port} available ${DIM}(${name})${NC}"
    fi
  fi
}

if [ "$MODE" = "dev" ]; then
  check_port 5432 "PostgreSQL"
  check_port 8000 "API"
else
  check_port 80 "Nginx/HTTP"
fi

if [ "$MONITORING" = true ]; then
  check_port 9090 "Prometheus"
  check_port 3000 "Grafana"
fi

# Abort on failure
if [ "$PREFLIGHT_OK" = false ]; then
  echo ""
  echo -e "  ${CROSS} ${RED}Preflight checks failed. Fix the issues above and re-run.${NC}"
  echo ""
  exit 1
fi

echo ""
echo -e "  ${CHECK} ${GREEN}All preflight checks passed${NC}"

# ═══════════════════════════════════════════════════════════════════════════
#  BUILD & START SERVICES
# ═══════════════════════════════════════════════════════════════════════════
section "Starting services"

BUILD_FLAG=""
if [ "$REBUILD" = true ]; then
  BUILD_FLAG="--build"
  echo -e "  ${ARROW} Forcing image rebuild..."
fi

if [ "$MODE" = "dev" ]; then
  # ── Development ──
  echo -e "  ${ARROW} Starting dev stack (db + api)..."
  docker compose up -d $BUILD_FLAG

  section "Health checks"
  wait_for_health "http://localhost:8000/health" "API" 45

else
  # ── Production ──
  echo -e "  ${ARROW} Starting production stack (db + api + nginx)..."
  docker compose -f docker-compose.prod.yml --env-file .env.prod up -d $BUILD_FLAG

  section "Health checks"
  wait_for_health "http://localhost:80/health" "Nginx → API" 60

  # ── Optional Monitoring ──
  if [ "$MONITORING" = true ]; then
    section "Starting monitoring"
    echo -e "  ${ARROW} Launching Prometheus + Grafana..."
    docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml \
      --env-file .env.prod up -d $BUILD_FLAG

    wait_for_health "http://localhost:9090/-/healthy" "Prometheus" 30
    wait_for_health "http://localhost:3000/api/health" "Grafana" 30
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════
#  STATUS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
section "Service status"
echo ""

if [ "$MODE" = "dev" ]; then
  docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
else
  docker compose -f docker-compose.prod.yml --env-file .env.prod ps \
    --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

  if [ "$MONITORING" = true ]; then
    echo ""
    docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml \
      --env-file .env.prod ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
  fi
fi

# ── Access URLs ─────────────────────────────────────────────────────────────
section "Access points"
echo ""
if [ "$MODE" = "dev" ]; then
  echo -e "  ${ARROW} API:          ${BOLD}http://localhost:8000${NC}"
  echo -e "  ${ARROW} API Docs:     ${BOLD}http://localhost:8000/docs${NC}"
  echo -e "  ${ARROW} Health:       ${BOLD}http://localhost:8000/health${NC}"
else
  echo -e "  ${ARROW} API (Nginx):  ${BOLD}http://localhost${NC}"
  echo -e "  ${ARROW} API Docs:     ${BOLD}http://localhost/docs${NC}"
  echo -e "  ${ARROW} Health:       ${BOLD}http://localhost/health${NC}"
fi

if [ "$MONITORING" = true ]; then
  echo -e "  ${ARROW} Prometheus:   ${BOLD}http://localhost:9090${NC}"
  echo -e "  ${ARROW} Grafana:      ${BOLD}http://localhost:3000${NC}  ${DIM}(admin / admin)${NC}"
fi

echo ""
echo -e "${BOLD}${CYAN}── Quick Commands ──${NC}"
echo ""
if [ "$MODE" = "dev" ]; then
  echo -e "  ${DIM}View logs:${NC}    docker compose logs -f"
  echo -e "  ${DIM}Stop:${NC}         ./scripts/startup.sh --dev --down"
  echo -e "  ${DIM}Rebuild:${NC}      ./scripts/startup.sh --dev --rebuild"
else
  echo -e "  ${DIM}View logs:${NC}    docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f"
  echo -e "  ${DIM}Stop:${NC}         ./scripts/startup.sh --down"
  echo -e "  ${DIM}Rebuild:${NC}      ./scripts/startup.sh --rebuild"
  echo -e "  ${DIM}Backup DB:${NC}    docker exec krisis-api-1 bash scripts/backup_db.sh"
fi
echo ""
echo -e "${GREEN}${BOLD}✔ Krisis is up and running!${NC}"
echo ""
