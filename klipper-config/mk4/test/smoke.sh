#!/bin/bash
# Prueba en batch (sin impresora) de las configs y extras de la MK4.
# Compila el MCU "Linux" de la versión de Klipper de la Pi para tener su
# diccionario, sustituye el ADXL por fake_accel.py y ejecuta accel.gcode
# (sonda de boquilla) y manual.gcode (sonda de brazo). Los pines son de
# pega (gpioN): comprueba carga de config, macros y flujo de comandos,
# no el hardware. En batch todo endstop "dispara" al final del movimiento.
# Los .gcode no deben provocar errores a propósito: el primero corta la prueba.
#   uso: klipper-config/mk4/test/smoke.sh [commit-de-klipper]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; MK4="$HERE/.."; ROOT="$HERE/../../.."
COMMIT="${1:-9cb99754}"                       # v0.13.0-800 (la de la Pi)
KL="$ROOT/repos/klipper"; WT="$ROOT/repos/_klipper-smoke"; PY="$KL/.venv-klippy/bin/python"
[ -x "$PY" ] || { python3 -m venv "$KL/.venv-klippy"; "$PY" -m pip install -q -r "$KL/scripts/klippy-requirements.txt"; }
git -C "$KL" cat-file -e "$COMMIT^{commit}" 2>/dev/null || git -C "$KL" fetch -q --depth=400 origin master
rm -rf "$WT"; git -C "$KL" worktree prune; git -C "$KL" worktree add -q --detach "$WT" "$COMMIT"
trap 'git -C "$KL" worktree remove --force "$WT"' EXIT
(cd "$WT" && printf 'CONFIG_MACH_LINUX=y\n' > .config && make -s olddefconfig >/dev/null && make -s -j8 >/dev/null)
cp "$MK4"/extras/*.py "$HERE/fake_accel.py" "$WT/klippy/extras/"
W="$WT/t"; mkdir -p "$W"; cp "$MK4"/{macros,marlin_compat,probe_accel,tramado}.cfg "$HERE"/*.gcode "$W/"
sed 's/\^PB9/^gpio22/' "$MK4/probe_manual.cfg" > "$W/probe_manual_test.cfg"
{ cat "$HERE/base.cfg"; echo "[include probe_accel.cfg]"; cat "$HERE/tail.cfg"; } > "$W/accel.cfg"
{ cat "$HERE/base.cfg"; echo "[include probe_manual_test.cfg]"; cat "$HERE/tail.cfg"; } > "$W/manual.cfg"
fail=0
for t in accel manual; do
  (cd "$W" && timeout 240 "$PY" ../klippy/klippy.py $t.cfg -i $t.gcode -o $t.serial \
     -d ../out/klipper.dict -d rpi=../out/klipper.dict -l $t.log >/dev/null 2>&1) || true
  errs=$(grep -c "Error evaluating\|Traceback\|Config error\|Internal error" "$W/$t.log" || true)
  echo "== $t: $errs errores"; [ "$errs" = 0 ] || { grep -m5 -A3 "Error\|Traceback" "$W/$t.log"; fail=1; }
  grep -E "^(HOME_ACCEL|Result:|.*adjust (CW|CCW)|.*\(base\)|!! |// Tramado|Haz G28|probe accuracy results|Mesh Bed Leveling Complete|[0-9.]+ g:)" "$W/$t.log" | cut -c1-150
done
exit $fail
