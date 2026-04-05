#!/usr/bin/env bash
set -e

# ── Configuration ──────────────────────────────────────────────
INSTALL_DIR="/opt/gemini-web"
VENV_DIR="${INSTALL_DIR}/.venv"
BIN_LINK="/usr/local/bin/gemini-web"
GEMINI_API_REPO="https://github.com/HanaokaYuzu/Gemini-API.git"
WRAPPER_REPO="https://github.com/iiroak/gemini-web-api-wrapper.git"

# ── Check root ─────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "==> Installing Gemini Web API Wrapper"

# ── Install system dependencies ────────────────────────────────
echo "==> Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git > /dev/null

# ── Create install directory ───────────────────────────────────
echo "==> Setting up ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
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

# ── Install systemd service ───────────────────────────────────
SERVICE_SRC="${INSTALL_DIR}/gemini-web-api-wrapper/gemini-web.service"
if [ -f "${SERVICE_SRC}" ]; then
    echo "==> Installing systemd service..."
    cp "${SERVICE_SRC}" /etc/systemd/system/gemini-web.service
    systemctl daemon-reload
    echo "    Service installed. Use:"
    echo "      sudo systemctl enable gemini-web   # start on boot"
    echo "      sudo systemctl start gemini-web    # start now"
    echo "      sudo systemctl status gemini-web   # check status"
fi

echo ""
echo "==> Installation complete!"
echo ""
echo "  gemini-web is now available system-wide."
echo ""
echo "  Quick start:"
echo "    gemini-web init          # configure cookies & token"
echo "    gemini-web serve         # start server manually"
echo "    sudo systemctl start gemini-web  # start as service"
echo ""
