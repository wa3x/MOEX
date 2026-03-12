#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/wa3x/MOEX.git"
APP_DIR="${HOME}/MOEX"
VENV_DIR="${APP_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
  printf "\n[%s] %s\n" "$(date '+%H:%M:%S')" "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Ошибка: не найдена команда '$1'."
    exit 1
  fi
}

install_system_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    log "Устанавливаю системные зависимости через apt"
    sudo apt-get update
    sudo apt-get install -y \
      git \
      python3 \
      python3-venv \
      python3-pip \
      libegl1 \
      libgl1 \
      libxkbcommon-x11-0 \
      libdbus-1-3 \
      libxcb-cursor0 \
      libxcomposite1 \
      libxdamage1 \
      libxrandr2 \
      libxfixes3 \
      libxi6 \
      libxtst6 \
      libfontconfig1
    return
  fi

  if command -v dnf >/dev/null 2>&1; then
    log "Устанавливаю системные зависимости через dnf"
    sudo dnf install -y \
      git \
      python3 \
      python3-pip \
      python3-virtualenv \
      mesa-libEGL \
      mesa-libGL \
      libxkbcommon-x11 \
      dbus-libs \
      libXcursor \
      libXcomposite \
      libXdamage \
      libXrandr \
      libXfixes \
      libXi \
      libXtst \
      fontconfig
    return
  fi

  if command -v pacman >/dev/null 2>&1; then
    log "Устанавливаю системные зависимости через pacman"
    sudo pacman -Sy --noconfirm \
      git \
      python \
      python-pip \
      python-virtualenv \
      libegl \
      mesa \
      libxkbcommon-x11 \
      dbus \
      libxcursor \
      libxcomposite \
      libxdamage \
      libxrandr \
      libxfixes \
      libxi \
      libxtst \
      fontconfig
    return
  fi

  log "Пакетный менеджер не распознан. Пропускаю установку системных библиотек."
  log "Если PyQt6 не запустится, их нужно будет поставить вручную."
}

clone_or_update_repo() {
  if [[ -d "${APP_DIR}/.git" ]]; then
    log "Репозиторий уже есть, обновляю"
    git -C "${APP_DIR}" pull --ff-only
  else
    log "Клонирую репозиторий в ${APP_DIR}"
    git clone "${REPO_URL}" "${APP_DIR}"
  fi
}

create_venv() {
  log "Создаю виртуальное окружение"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
}

install_python_deps() {
  log "Устанавливаю Python-зависимости"
  "${VENV_DIR}/bin/pip" install --upgrade pip wheel setuptools
  "${VENV_DIR}/bin/pip" install \
    PyQt6 \
    pyqtgraph \
    requests
}

create_launcher() {
  local launcher="${HOME}/.local/bin/moex-widget"

  log "Создаю команду запуска ${launcher}"
  mkdir -p "${HOME}/.local/bin"

  cat > "${launcher}" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
cd "${APP_DIR}"
exec "${VENV_DIR}/bin/python" "${APP_DIR}/main.py"
EOF

  chmod +x "${launcher}"

  case ":$PATH:" in
    *":${HOME}/.local/bin:"*) ;;
    *)
      log "Добавь ~/.local/bin в PATH, если команда moex-widget не находится"
      ;;
  esac
}

create_desktop_file() {
  local desktop_dir="${HOME}/.local/share/applications"
  local desktop_file="${desktop_dir}/moex-widget.desktop"

  log "Создаю desktop launcher ${desktop_file}"
  mkdir -p "${desktop_dir}"

  cat > "${desktop_file}" <<EOF
[Desktop Entry]
Type=Application
Name=MOEX Widget
Comment=Виджет акций MOEX для Linux/KDE
Exec=${HOME}/.local/bin/moex-widget
Terminal=false
Categories=Office;Finance;
StartupNotify=true
EOF
}

print_finish_message() {
  cat <<EOF

Готово.

Запуск:
  ${HOME}/.local/bin/moex-widget

Если ~/.local/bin уже в PATH, можно просто:
  moex-widget

Desktop launcher:
  ${HOME}/.local/share/applications/moex-widget.desktop
EOF
}

main() {
  require_cmd git
  require_cmd "${PYTHON_BIN}"

  install_system_packages
  clone_or_update_repo
  create_venv
  install_python_deps
  create_launcher
  create_desktop_file
  print_finish_message
}

main "$@"