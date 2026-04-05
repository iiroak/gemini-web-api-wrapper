#!/usr/bin/env bash
set -e

# ── Configuration ──────────────────────────────────────────────
INSTALL_DIR="/opt/gemini-web"
DATA_DIR="${INSTALL_DIR}/data"
VENV_DIR="${INSTALL_DIR}/.venv"
BIN_LINK="/usr/local/bin/gemini-web"
GEMINI_API_REPO="https://github.com/HanaokaYuzu/Gemini-API.git"
WRAPPER_REPO="https://github.com/iiroak/gemini-web-api-wrapper.git"

# ── Check root ─────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

# ── Detect existing installation ───────────────────────────────
if [ -f "${BIN_LINK}" ] || [ -d "${INSTALL_DIR}/.venv" ]; then
    echo "⚠️  gemini-web is already installed."
    echo "   Install dir: ${INSTALL_DIR}"
    echo "   Binary:      ${BIN_LINK}"
    echo ""
    read -p "Reinstall from scratch? (y/N): " REPLY
    case "$REPLY" in
        [yY]|[yY][eE][sS])
            echo "==> Reinstalling (clean)..."

            # Stop service if running
            if systemctl is-active --quiet gemini-web 2>/dev/null; then
                echo "==> Stopping gemini-web service..."
                systemctl stop gemini-web
            fi
            if systemctl is-enabled --quiet gemini-web 2>/dev/null; then
                systemctl disable gemini-web 2>/dev/null || true
            fi

            # Remove service file
            rm -f /etc/systemd/system/gemini-web.service
            systemctl daemon-reload 2>/dev/null || true

            # Remove symlink
            rm -f "${BIN_LINK}"

            # Remove install directory (venv, cloned repos) but keep data
            echo "==> Removing ${INSTALL_DIR} (preserving ${DATA_DIR})..."
            # Preserve data dir if it exists
            if [ -d "${DATA_DIR}" ]; then
                TMP_DATA=$(mktemp -d)
                cp -a "${DATA_DIR}" "${TMP_DATA}/data"
                rm -rf "${INSTALL_DIR}"
                mkdir -p "${INSTALL_DIR}"
                mv "${TMP_DATA}/data" "${DATA_DIR}"
                rm -rf "${TMP_DATA}"
            else
                rm -rf "${INSTALL_DIR}"
            fi

            echo "==> Clean slate. Proceeding with fresh install..."
            ;;
        *)
            echo "Aborted."
            exit 0
            ;;
    esac
fi

# ── Parse arguments for non-interactive reinstall ──────────────
if [ "$1" = "--reinstall" ] || [ "$1" = "-r" ]; then
    echo "==> Forced reinstall..."

    if systemctl is-active --quiet gemini-web 2>/dev/null; then
        systemctl stop gemini-web
    fi
    if systemctl is-enabled --quiet gemini-web 2>/dev/null; then
        systemctl disable gemini-web 2>/dev/null || true
    fi
    rm -f /etc/systemd/system/gemini-web.service
    systemctl daemon-reload 2>/dev/null || true
    rm -f "${BIN_LINK}"

    if [ -d "${DATA_DIR}" ]; then
        TMP_DATA=$(mktemp -d)
        cp -a "${DATA_DIR}" "${TMP_DATA}/data"
        rm -rf "${INSTALL_DIR}"
        mkdir -p "${INSTALL_DIR}"
        mv "${TMP_DATA}/data" "${DATA_DIR}"
        rm -rf "${TMP_DATA}"
    else
        rm -rf "${INSTALL_DIR}"
    fi
fi

echo "==> Installing Gemini Web API Wrapper"

# ── Install system dependencies ────────────────────────────────
echo "==> Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git > /dev/null

# ── Create install directory ───────────────────────────────────
echo "==> Setting up ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
mkdir -p "${DATA_DIR}"
cd "${INSTALL_DIR}"

# ── Create virtual environment ─────────────────────────────────
echo "==> Creating virtual environment..."
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

# ── Clone and install gemini-webapi ────────────────────────────
echo "==> Cloning and installing gemini-webapi..."
if [ -d "${INSTALL_DIR}/Gemini-API" ]; then
    cd "${INSTALL_DIR}/Gemini-API"
    git pull --quiet
    cd "${INSTALL_DIR}"
else
    git clone --quiet "${GEMINI_API_REPO}" "${INSTALL_DIR}/Gemini-API"
fi
pip install --quiet "${INSTALL_DIR}/Gemini-API"

# ── Clone and install gemini-web-api-wrapper ───────────────────
echo "==> Cloning and installing gemini-web-api-wrapper..."
if [ -d "${INSTALL_DIR}/gemini-web-api-wrapper" ]; then
    cd "${INSTALL_DIR}/gemini-web-api-wrapper"
    git pull --quiet
    cd "${INSTALL_DIR}"
else
    git clone --quiet "${WRAPPER_REPO}" "${INSTALL_DIR}/gemini-web-api-wrapper"
fi
pip install --quiet "${INSTALL_DIR}/gemini-web-api-wrapper"

# ── Create system-wide symlink ─────────────────────────────────
echo "==> Creating symlink ${BIN_LINK}..."
ln -sf "${VENV_DIR}/bin/gemini-web" "${BIN_LINK}"

# ── Set GEMINI_WEB_HOME for all users ─────────────────────────
PROFILE_SNIPPET="/etc/profile.d/gemini-web.sh"
echo "==> Setting GEMINI_WEB_HOME in ${PROFILE_SNIPPET}..."
cat > "${PROFILE_SNIPPET}" <<EOF
export GEMINI_WEB_HOME="${DATA_DIR}"
EOF
chmod 644 "${PROFILE_SNIPPET}"

# ── Install systemd service ───────────────────────────────────
SERVICE_SRC="${INSTALL_DIR}/gemini-web-api-wrapper/gemini-web.service"
if [ -f "${SERVICE_SRC}" ]; then
    echo "==> Installing systemd service..."
    # Detect the user who invoked sudo (or current user if no sudo)
    REAL_USER="${SUDO_USER:-$(whoami)}"

    # Copy service file and set the correct user
    sed "s/# User=__USER__/User=${REAL_USER}/" "${SERVICE_SRC}" | \
    sed "s/# Group=__GROUP__/Group=${REAL_USER}/" > /etc/systemd/system/gemini-web.service

    # Set data dir ownership
    chown -R "${REAL_USER}:${REAL_USER}" "${DATA_DIR}"

    systemctl daemon-reload
    echo "    Service installed (runs as user: ${REAL_USER})."
    echo "    Data dir: ${DATA_DIR}"
    echo "    Use:"
    echo "      sudo systemctl enable gemini-web   # start on boot"
    echo "      sudo systemctl start gemini-web    # start now"
    echo "      sudo systemctl status gemini-web   # check status"
    echo "      sudo journalctl -u gemini-web -f   # view logs"
fi

echo ""
echo "==> Installation complete!"
echo ""
echo "  gemini-web is now available system-wide."
echo "  Config & data: ${DATA_DIR}"
echo ""
echo "  Quick start:"
echo "    export GEMINI_WEB_HOME=${DATA_DIR}"
echo "    gemini-web init          # configure cookies & token"
echo "    gemini-web serve         # start server manually"
echo "    sudo systemctl start gemini-web  # start as service"
echo ""
