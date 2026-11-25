# Frankenprinter — serie MK (impresoras a medida con piezas de la EasyThreed K9)

Máquinas construidas a medida con la **placa (MKS Robin Lite), los brazos Z y el cabezal de una
EasyThreed K9**, más mecánica propia. **No son impresoras de serie**: las configs son para estas
máquinas concretas y no funcionarán tal cual en otras. Para las K9/K10 originales (Marlin, Klipper,
hack USB de la K10) ve a **[aorizondo/EasyThreed-K9-K10](https://github.com/aorizondo/EasyThreed-K9-K10)**.

| Máquina | Firmware | Qué tiene | Dónde |
|---|---|---|---|
| **MK3** | Marlin (rama [`mk3-marlin`](https://github.com/aorizondo/frankenprinter/tree/mk3-marlin)) | X/Y por correa, Z con 2 brazos K9, sonda manual, homing a tope | rama `mk3-marlin` |
| **MK4** | **Klipper** + Raspberry Pi 4 | Lo de la MK3 + ADXL345 (input shaper y **homing X/Y por choque**), red configurable desde la SD | [docs/12](docs/12-mk4-klipper.md) (migración) · [docs/13](docs/13-manual-mk4.md) (**manual de uso**) · `klipper-config/mk4/` |
| **CNC** (función extra) | GRBL hoy / Klipper multi-MCU (plan) | CNC casero (Arduino Uno + CNC Shield, NEMA17 reciclados) y plan de fusión con el cabezal de una K10 | docs 00–11, `firmware/cnc/`, `klipper-config/` |

Plugins de OctoPrint usados con la MK3 (Marlin): [OctoPrint-BoostKit](https://github.com/aorizondo/OctoPrint-BoostKit) y
[OctoPrint-ZPreload](https://github.com/aorizondo/OctoPrint-ZPreload). Con la MK4 (Klipper):
[Klipper-BoostKit](https://github.com/aorizondo/Klipper-BoostKit), tablero visual junto a Mainsail/Fluidd.

> Estado: I+D personal. La MK4 imprime con Klipper; el CNC funciona con GRBL; la fusión
> K10+CNC está documentada pero aparcada.

## CNC + cabezal K10 (plan de fusión)

Idea: usar la **mecánica del CNC** para X/Y/Z y el **cabezal de una K10** (hotend, extrusor,
termistor, fan) con **Klipper multi-MCU** desde una Raspberry Pi:
- **MCU CNC** (Arduino Uno + CNC Shield) → ejes X/Y/Z + endstops + sonda Z.
- **MCU K10** (placa GD32F303 con el hack USB) → extrusor + calefactor + termistor + fan.

El hack de la K10 (soldadura USB/UART, flasheo, reversing del pinout) está en el repo de las
originales: [klipper/k10](https://github.com/aorizondo/EasyThreed-K9-K10/blob/main/klipper/k10/README.md). Lee [docs/00](docs/00-RESUMEN-EJECUTIVO.md)
para la matriz de decisión.

## Índice de documentación

| Doc | Contenido |
|-----|-----------|
| [00 Resumen ejecutivo](docs/00-RESUMEN-EJECUTIVO.md) | Hallazgos críticos y matriz de decisión de arquitectura |
| [01 Arquitectura](docs/01-arquitectura.md) | Modelo multi-MCU de Klipper, roles, flujo de datos |
| [02 Hardware K10](https://github.com/aorizondo/EasyThreed-K9-K10/blob/main/klipper/docs/02-hardware-k10.md) ↗ | MCU GD32F303, USB-PD, drivers HR4988, MOSFET, SWD |
| [03 Hardware CNC](docs/03-hardware-cnc.md) | Arduino Uno + CNC Shield V3, A4988/DRV8825, NEMA17, mecánica Epson |
| [04 Soldadura UART K10](https://github.com/aorizondo/EasyThreed-K9-K10/blob/main/klipper/docs/04-soldadura-uart-k10.md) ↗ | La realidad del "USB", dónde soldar, técnica SMD |
| [05 Flasheo Klipper](docs/05-flasheo-klipper.md) | Compilar/flashear en el Arduino (la K10: repo K9/K10) |
| [06 Cableado y pinout](docs/06-cableado-pines.md) | Tablas de pines, conexiones físicas |
| [07 Instalación host](docs/07-instalacion-host-pi.md) | Raspberry Pi, KIAUH, Moonraker, Mainsail |
| [08 Calibración](docs/08-calibracion.md) | rotation_distance, PID, extrusor, input shaping |
| [09 Sensores y sonda Z](docs/09-sensores-zprobe.md) | BLTouch, inductiva, microswitch, piezo; bed mesh |
| [10 Reversing pinout K10](https://github.com/aorizondo/EasyThreed-K9-K10/blob/main/klipper/docs/10-reversing-pinout-k10.md) ↗ | Metodología para mapear los pines del GD32 |
| [12 MK4 → Klipper](docs/12-mk4-klipper.md) | MK4 (Robin Lite de la K9): migración, ADXL345, input shaper, homing por choque |
| [13 Manual de uso MK4](docs/13-manual-mk4.md) | Red, homing, calibraciones, imprimir, acelerómetro y problemas frecuentes |
| [99 BOM, riesgos, troubleshooting](docs/99-bom-riesgos-troubleshooting.md) | Compras, errores comunes y soluciones |

## Estructura del repo

```
3dprinter/
├── README.md                  ← este archivo
├── docs/                      ← documentación técnica (orden de lectura por número)
├── klipper-config/            ← configs Klipper: mk4/ (MK4) y multi-MCU CNC+K10 (plan)
│   ├── printer.cfg            ← config principal (incluye los módulos)
│   ├── include/               ← módulos: MCUs, steppers, extrusor, sonda, macros
│   └── moonraker.conf         ← config de Moonraker
├── diagrams/                  ← diagramas de arquitectura y pinout (Mermaid/ASCII)
├── firmware/                  ← cnc/ (GRBL/Klipper del Arduino), mk4/ (parche del bootloader)
├── cad/                       ← piezas MK (carro, acoples, soporte ADXL) y cajas CNC/K10
├── repos/                     ← repos clonados (referencia y código)
│   ├── klipper/               ← firmware + host
│   ├── moonraker/             ← API server
│   ├── kiauh/                 ← instalador
│   ├── klipper-drawbot/       ← REFERENCIA: Klipper en Arduino Uno + CNC Shield V3
│   ├── ECF-Marlin/            ← REFERENCIA: Marlin comunitario para EasyThreed
│   ├── EasyThreeD-K9-STM32/   ← REFERENCIA: firmware K9
│   └── EasyThreed-K9-K10/     ← repo de las originales (Marlin K9 + rama mk3-marlin de origen)
└── reference/                 ← notas y fuentes externas guardadas
```

## Fuentes clave

- Klipper: <https://www.klipper3d.org/> · repo <https://github.com/Klipper3d/klipper>
- Reversing de la placa K10 (fuente técnica más completa):
  <https://palmarci.me/blog/2025-05-02-easythreed-k10-3d-printer-main-board-reversing/index.html>
- Klipper en Arduino Uno + CNC Shield (referencia directa):
  <https://github.com/gwisp2/klipper-drawbot>
- Hackaday K9 (identificación de MCU):
  <https://hackaday.com/2024/02/12/easythreed-k9-the-value-in-a-e72-aliexpress-fdm-3d-printer/>
