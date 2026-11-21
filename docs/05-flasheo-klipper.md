# 05 — Flasheo de Klipper en los dos MCU

Cada MCU necesita el firmware de Klipper compilado **para su chip**. Se compila en la Pi
(`~/klipper`) con `make menuconfig` + `make`, y se flashea por su vía. El proceso host (que hace la
cinemática) es común; lo que cambia es el binario de cada MCU.

---

## A. Arduino Uno (ATmega328P) — el CNC

### menuconfig
```bash
cd ~/klipper
make clean
make menuconfig
```
Opciones:
```
[*] Enable extra low-level configuration options
    Micro-controller Architecture: Atmega AVR
    Processor model: atmega328p
    Processor speed: 16 MHz
    Communication interface: Serial (UART)
    Baud rate for serial port: 250000
```
> Flash de 32 KB justa: **desactiva** lo que no uses para que el binario quepa. Si `make` se queja de
> tamaño, quita features opcionales.

### Compilar y flashear
```bash
make
# El Uno ya trae bootloader Arduino/Optiboot -> NO necesitas ISP externo:
avrdude -c arduino -p atmega328p -P /dev/ttyACM0 -b 115200 -D \
        -U flash:w:out/klipper.elf.hex:i
```
- Puerto: `/dev/ttyACM0` (Uno genuino) o `/dev/ttyUSB0` (clon CH340). Mejor usa el `by-id`.
- Baud bootloader: **115200** (Optiboot moderno). Clones viejos: prueba **57600** si da "out of sync".
- `-D` = no borrar todo (necesario con bootloader).
- Alternativa: `make flash FLASH_DEVICE=/dev/serial/by-id/usb-...`.
- Vía KIAUH: `[Advanced] → [Build + Flash]`.

> Solo necesitas un ISP externo si quisieras **regrabar el bootloader**, no para Klipper.

---

## B. Placa K10 (GD32F303)

Flasheo de la K10 (SD con `p10_printer.bin` o SWD, menuconfig, salvaguarda del firmware de
fábrica): **[repo K9/K10 → klipper/docs/05](https://github.com/aorizondo/EasyThreed-K9-K10/blob/main/klipper/docs/05-flasheo-klipper.md)**.

---

## Verificación tras flashear

```bash
ls /dev/serial/by-id/*          # cada MCU debe aparecer
```
En `printer.cfg` pon esos `by-id` en `[mcu]` (CNC) y `[mcu k10]`. Luego en Mainsail: `FIRMWARE_RESTART`.
Si conecta, en la consola verás la versión de Klipper de cada MCU. Comprueba que **las versiones host y
MCU coinciden** (si no, recompila/reflashea).

---

## Errores típicos
| Síntoma | Causa probable | Solución |
|---|---|---|
| `avrdude: stk500_recv(): programmer is not responding` | baud bootloader o puerto | prueba 57600; revisa /dev correcto; sin el monitor serie abierto |
| `Unable to connect` (k10) | TX/RX cruzados, baud, 3.3V | intercambia TX/RX; mismo baud host/MCU; GND común |
| GD32 no arranca tras SWD | falta "Disable SWD at startup" u offset | activa esa opción; revisa offset/cristal |
| Versiones host/MCU distintas | recompilaste host pero no MCU (o al revés) | reflashea con el mismo commit |

Fuentes: <https://www.klipper3d.org/Installation.html> · <https://www.klipper3d.org/Bootloaders.html> ·
GD32F303: <https://klipper.discourse.group/t/installing-klipper-on-ender-3-4-2-2-board-and-gd32f303-chip/8165>
