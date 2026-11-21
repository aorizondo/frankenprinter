#!/usr/bin/env bash
# Reconstruye repos/ con los clones de referencia (shallow).
# Estos repos NO se versionan en este proyecto (ver .gitignore).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p repos && cd repos

clone() {  # clone <url> <dir>
  if [ -d "$2/.git" ]; then
    echo "== $2 ya existe, omito"
  else
    echo "== Clonando $2"
    git clone --depth 1 "$1" "$2"
  fi
}

# Núcleo Klipper
clone https://github.com/Klipper3d/klipper.git            klipper
clone https://github.com/Arksine/moonraker.git            moonraker
clone https://github.com/dw-0/kiauh.git                   kiauh

# Referencias del proyecto
clone https://github.com/gwisp2/klipper-drawbot.git       klipper-drawbot   # Uno + CNC Shield V3
clone https://github.com/schmttc/ECF-Marlin.git           ECF-Marlin        # Marlin EasyThreed
clone https://github.com/armandioan/EasyThreeD-K9-STM32.git EasyThreeD-K9-STM32

# Repos hermanos (desarrollo propio: clon completo, no shallow)
full() {  # full <url> <dir>
  if [ -d "$2/.git" ]; then echo "== $2 ya existe, omito"; else echo "== Clonando $2"; git clone "$1" "$2"; fi
}
full git@github.com:aorizondo/EasyThreed-K9-K10.git       EasyThreed-K9-K10   # K9/K10 de serie
full git@github.com:aorizondo/OctoPrint-BoostKit.git      OctoPrint-BoostKit
full git@github.com:aorizondo/OctoPrint-ZPreload.git      OctoPrint-ZPreload

echo "Hecho. Repos de referencia en: $ROOT/repos"
