#!/usr/bin/env bash
set -euo pipefail

NOVNC_PORT="${NOVNC_PORT:-7900}"
VNC_PORT="${VNC_PORT:-5900}"
DISPLAY_VALUE="${DISPLAY:-:99}"
SCREEN_RESOLUTION="${SCREEN_RESOLUTION:-1920x1080x24}"
LOGS_DIR="${LOGS_DIR:-/app/logs}"
CHROME_BINARY="${CHROME_BINARY:-/usr/bin/google-chrome}"
ENABLE_VNC="${ENABLE_VNC:-true}"
APP_MODULE="${APP_MODULE:-app.main}"
export CHROME_BINARY

if [[ -z "${CHROME_VERSION_MAIN:-}" ]]; then
  if command -v "${CHROME_BINARY}" >/dev/null 2>&1; then
    version_output="$("${CHROME_BINARY}" --version 2>/dev/null || true)"
    if [[ "${version_output}" =~ ([0-9]{2,3})\.[0-9]+ ]]; then
      export CHROME_VERSION_MAIN="${BASH_REMATCH[1]}"
    fi
  fi
fi

mkdir -p "${LOGS_DIR}"

cleanup() {
  local exit_code=$?
  for pid_var in XVFB_PID FLUXBOX_PID X11VNC_PID WEBSOCKIFY_PID; do
    local pid="${!pid_var:-}"
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
    fi
  done
  exit "${exit_code}"
}

trap cleanup EXIT INT TERM

should_start_vnc=false
case "${ENABLE_VNC,,}" in
  1|true|yes|on)
    should_start_vnc=true
    ;;
esac

if [[ "${should_start_vnc}" == "true" ]]; then
  export DISPLAY="${DISPLAY_VALUE}"
  Xvfb "${DISPLAY}" -screen 0 "${SCREEN_RESOLUTION}" >>"${LOGS_DIR}/xvfb.log" 2>&1 &
  XVFB_PID=$!
  sleep 2

  fluxbox >>"${LOGS_DIR}/fluxbox.log" 2>&1 &
  FLUXBOX_PID=$!

  x11vnc \
    -display "${DISPLAY}" \
    -rfbport "${VNC_PORT}" \
    -shared \
    -forever \
    -quiet \
    -nopw \
    -o "${LOGS_DIR}/x11vnc.log" &
  X11VNC_PID=$!

  websockify \
    --web /usr/share/novnc \
    "${NOVNC_PORT}" \
    "localhost:${VNC_PORT}" >>"${LOGS_DIR}/websockify.log" 2>&1 &
  WEBSOCKIFY_PID=$!

  sleep 3
else
  echo "ENABLE_VNC=${ENABLE_VNC} -> running headless (skip Xvfb/VNC stack)." >&2
fi

exec python -m "${APP_MODULE}" "$@"
