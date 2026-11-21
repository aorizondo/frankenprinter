# AGENTS.md — frankenprinter (serie MK + CNC)

Repo identity: I+D personal de Antonio. **La frankenprinter es la serie MK**: máquinas a medida con la
placa (MKS Robin Lite, STM32F103RC), los brazos Z y el cabezal de una **EasyThreed K9**, más mecánica
propia. MK3 = Marlin (rama `mk3-marlin`), **MK4 = Klipper** (rama `main`, `klipper-config/mk4/`).
**Función extra**: CNC casero (Arduino Uno + CNC Shield) y plan de fusión K10+CNC con Klipper multi-MCU
(docs 00–11). Repo público: `aorizondo/frankenprinter`.

Repos hermanos (no confundir):
- **`aorizondo/EasyThreed-K9-K10`** — K9/K10 **de serie**: Marlin K9 (rama `marlin`, CI → `mksLite.bin`),
  Klipper K9 y **hack USB de la K10** (rama `klipper`, CI → `p10_printer.bin`), `main` une ambas.
  Clon local: `repos/EasyThreed-K9-K10/`. Aquí NO va nada de la MK.
- **`aorizondo/OctoPrint-BoostKit`** y **`aorizondo/OctoPrint-ZPreload`** — plugins OctoPrint.
  Clones locales: `repos/OctoPrint-BoostKit/`, `repos/OctoPrint-ZPreload/`.

## Lee primero

1. `README.md` — qué es cada máquina y dónde está.
2. **MK4**: `docs/12-mk4-klipper.md` (migración, decisiones) y `docs/13-manual-mk4.md` (uso diario).
3. **CNC / fusión**: `docs/11-estado-y-handoff.md` (estado real), `docs/00-RESUMEN-EJECUTIVO.md`,
   `firmware/cnc/grbl-setup.md` (settings GRBL calibrados vigentes).

## Workspaces (no enlazados, mismo ecosistema)

| Ruta | Qué es |
|------|--------|
| `/home/antonio/Desarrollo/solverius/3dprinter/` (**este repo**) | frankenprinter. `repos/` (gitignored) tiene los repos hermanos y clones de referencia |
| `/home/antonio/Documentos/Hobby/Maker/` (no-git, assets) | `3DPrinting/` (STL/3MF, `marlin comands.txt`, perfiles Cura/Prusa heredados, fotos del cabezal), `CAD/` (SCAD/SolveSpace WIP: cooler, disipadores, antena), `CAM/toolbits/` (FreeCAD Path), `CNC/proyecto cnc/`, `Electronics/`. **No commitear** a ningún repo |
| `/home/antonio/Programas/3d_print/` (no-git, tooling) | Cura 5.13 AppImage + `cura-5.13/`, venv Poetry con OctoPrint 1.11 (`.venv`, Python 3.13), `backlash_compensator.py`, `cura_profiles/`, firmware OEM `easythreed k9/`, `lite_cfg.txt`. No tocar como código |

Validar con Antonio antes de mover cosas entre ellos (referencias cruzadas frágiles).

## Qué máquina es "la impresora"

- **MK4** (esta, Klipper, Pi `mk4.local`): la que funciona hoy. "La impresora" sin más = MK4.
- **MK3**: la misma base con Marlin (rama `mk3-marlin`), sustituida por la MK4.
- **K9 / K10 de serie**: repo `EasyThreed-K9-K10`. La placa de la K9 de Antonio está ahora en la MK4.
- **K10** en este repo: solo como cabezal del plan de fusión con el CNC.

## MK4 (Klipper) — comandos no obvios

- Host: Raspberry Pi 4 → **`ssh antonio@mk4.local`**; para trabajar en la Pi usar la sesión tmux **`mk4`**.
- Config en `klipper-config/mk4/` = copia exacta de `~/printer_data/config/` en la Pi. Tras editar:
  `scp` a la Pi y `FIRMWARE_RESTART` (o `sudo systemctl restart klipper`). Repo y Pi deben quedar iguales.
- `klipper-config/mk4/extras/*.py` van **enlazados** en `~/klipper/klippy/extras/` (y en
  `.git/info/exclude` de `~/klipper` para que Moonraker no lo marque *dirty*).
- Red de la Pi: `klipper-config/mk4/host/` (servicio `mk4-red`, archivo `/boot/firmware/mk4-red.txt`).
- Firmware de la Robin Lite: se compila **en la Pi** con el parche `firmware/mk4/robin-lite-vectors-first.patch`
  (docs/12 §5). Sin parche el bootloader rechaza Klipper ≥ v0.11.
- Gotcha Klipper: nombres de comando con letra+dígito al principio (`G28_ACCEL`, `M907_X`) son inválidos.

## MK4 — hechos de hardware (no deducibles del código)

- **Sin finales de carrera X/Y**: homing por choque con el ADXL345 (INT1 → GPIO17, `extras/accel_endstop.py`,
  `HOME_ACCEL`). Umbrales calibrados a 15 mm/s: X 3 g, Y 1.5 g. Y exige **correas Y igual de tensas**.
  `G28.1 X/Y` está prohibido (buscaría switches retirados).
- ADXL345 por **I2C de la Pi** (`extras/adxl345_i2c.py`), no SPI: los módulos que hay no van por SPI.
- Y con 2 motores en un driver; Z con 2 brazos K9 en un driver (sin Z_TILT). Sonda Z de despliegue manual.

## CNC (función extra) — comandos no obvios

GRBL (modo actual), toolchain AVR local:
```bash
cd repos/grbl && make
avrdude -c arduino -p atmega328p -P /dev/ttyACM0 -b 115200 -D -U flash:w:grbl.hex:i
```
- **GRBL calibrado**: `$100=$101=75.83`, `$102=2226`, `$3=4`, `$110=$111=10000`, `$120=$121=1200`,
  `$112=200`, `$122=8`. No editar a ciegas (`firmware/cnc/grbl-setup.md`).
- Doble motor Y por jumpers de clonado (socket A). Si se pasa a Klipper: quitarlos y `[stepper_y1]`.
- Sin endstops: homing manual. PWM spindle/láser libre en D9/D10/D11.

## CAD (OpenSCAD)

```bash
cd cad && ./build.sh           # stl/ (gitignored) + renders/ (versionados)
openscad -D 'part="body"' -o out.stl k10_enclosure.scad   # una sola pieza (body, lid, assembly)
```
Requiere `openscad` + `xvfb-run`. El script avisa si una pieza no es 2-manifold (no falla): revisa la salida.
Tornillería M3, `FIT=0.30`, PETG sin cama caliente (brim). `cad/adxl345_k9_mount.scad`: no modificar sin
pedirlo (decisión de Antonio).

## Validar una MCU desde el PC

```bash
repos/klipper/.venv-klippy/bin/python repos/klipper/klippy/console.py [-b 250000] <dev>
```
El venv `repos/klipper/.venv-klippy` (Python 3.12) es del clon de Klipper, no del proyecto.

## Repos de terceros

`repos/` gitignored. Reconstruir con `./scripts/clone-references.sh`. **No descargar copias de lo que ya
está en `repos/`**; clones nuevos van en `repos/`, nunca en `/tmp`.

## Convenciones

- Docs en español, numeradas `docs/NN-tema.md` (no reordenar 00–13). `11-estado-y-handoff.md` es el
  documento vivo del CNC/fusión; `13-manual-mk4.md` el manual de la MK4.
- Commits en español, `tipo: descripción`.
- `SAVE_CONFIG` reescribe el bloque `#*#` de `printer.cfg`: no editarlo a mano.

## Recursos externos / memoria

- Investigación temática de Antonio: `/home/antonio/Documentos/Business/Solverius/Research/3D-Printing-CAD/`
  (COMPAS, BRL-CAD, Obico, AliceVision, FullControl, Kiri:Moto). Consultar antes de proponer herramientas.
- Memoria del agente: `/home/antonio/.claude/projects/-home-antonio-Desarrollo-solverius-3dprinter/memory/`.
- Referencias externas en `reference/` (URLs, notas, fotos).

## Qué evitar

- **No regenerar `cad/stl/`** y commitearlo (gitignored a propósito).
- **No commitear** assets de `Maker/` ni nada de `Programas/3d_print/`.
- **No meter aquí nada de las K9/K10 de serie ni de los plugins**: van a sus repos.
- **No editar a mano** el bloque `#*# SAVE_CONFIG` ni desincronizar `klipper-config/mk4/` de la Pi.
- **No reiniciar OctoPrint ni Klipper** con una impresión en curso.
