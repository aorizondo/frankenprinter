# 13 — Manual de uso de la MK4 (Klipper)

> Manual de uso diario. El **porqué** de cada decisión y la instalación desde cero están en
> [12 — MK4: migración Marlin → Klipper](12-mk4-klipper.md). Config: `klipper-config/mk4/`.

---

## 0. La máquina en una tabla

| Parte | Qué es |
|---|---|
| Placa | MKS Robin Lite (de la K9) con **Klipper**, 4 drivers A4988 |
| Ordenador | Raspberry Pi 4 (`mk4`): Klipper + Moonraker + **Mainsail** (interfaz web) |
| Ejes | X e Y mueven el cabezal, Z mueve la cama. Y y Z llevan 2 motores en un solo driver |
| Volumen útil | X −40…310, Y −60…320, Z 0…110 (origen = esquina del plato 190×240) |
| Homing X/Y | **Sin finales de carrera**: detecta el choque del carro con el marco con el acelerómetro |
| Homing Z | Sonda de brazo **manual** (la bajas y subes tú cuando lo pide) |
| Acelerómetro | ADXL345 en el cabezal, por I2C a la Pi + cable INT1 |
| Cama | Sin calentar |

---

## 1. Red: conectar la impresora

### 1.1 Wi-Fi (desde la microSD de la Pi)

La Pi lee su configuración de red de un archivo de texto en la microSD **en cada arranque**.

1. Apaga la impresora y saca la microSD **de la Raspberry Pi** (no la de la placa).
2. Métela en cualquier PC. Abre la partición **`bootfs`** (FAT, se ve en Windows/Mac/Linux).
3. Edita **`mk4-red.txt`**:
   ```ini
   [mk4]
   pais = ES

   [Redmi A2+]
   clave = la-contraseña
   prioridad = 10

   [WiFi de casa]
   clave = otra-contraseña
   prioridad = 5
   ```
   - Una sección `[...]` por red, con el **nombre exacto** (mayúsculas y espacios incluidos).
   - `clave`: 8–63 caracteres; vacía = red abierta. `prioridad`: con varias redes a la vista
     gana la más alta.
   - Las redes que borres del archivo se olvidan en el siguiente arranque.
   - **`pais` = `ES`, no `CU`**: con `CU` el chip Wi-Fi de la Pi solo ve los canales 1–11 y un
     hotspot en el canal 12–13 no aparece. Si cambias `pais`, la Pi reinicia sola una vez.
4. Expulsa la tarjeta, vuélvela a poner en la Pi y enciende. En 1–2 min está en la red.

### 1.2 Cable Ethernet

Funciona sin configurar nada:
- **A un router**: coge IP por DHCP.
- **Directo al PC**: en el PC, conexión de cable en modo "compartida" (NetworkManager:
  *Compartida con otros equipos*). La Pi coge una `10.42.0.x`.
- **Sin DHCP** (cable directo sin compartir): la Pi se pone una `169.254.x.x` sola.

Si el enlace va a 10 Mbps o se cae cada pocos segundos, el cable está mal (ya pasó una vez).

### 1.3 Entrar

| Para | Dirección |
|---|---|
| Interfaz web **Mainsail** | **http://mk4.local** |
| Interfaz web **Fluidd** (alternativa, misma impresora) | **http://mk4.local:81** |
| **BoostKit** (tablero visual: jog con teclado numérico, babystep, temperaturas, offsets…) | **http://mk4.local:82** (también en el menú de Mainsail) |
| Terminal | `ssh antonio@mk4.local` |

Usa siempre `mk4.local`: la IP cambia cuando el hotspot cambia de subred. Si `mk4.local` no
resuelve, mira la IP de `mk4` en la lista de dispositivos del router/hotspot.

Mainsail, Fluidd y BoostKit funcionan a la vez sobre la misma configuración: usa la que prefieras.
BoostKit se instala con `deploy/install.sh` de [Klipper-BoostKit](https://github.com/aorizondo/Klipper-BoostKit)
(pendiente en la MK4). Las dos
se actualizan desde *Máquina → Actualizaciones*. Para quitar la que sobre, dímelo (o en la Pi:
`sudo rm /etc/nginx/sites-enabled/fluidd && sudo systemctl reload nginx`).

**La consola** (para escribir comandos, como el terminal de OctoPrint):
- **Tab** completa el comando.
- `HELP` lista todos los comandos con su descripción.
- En Mainsail, el icono **"?"** de la consola abre esa lista con buscador: es lo más parecido
  al plugin de documentación de comandos de OctoPrint.
- `AYUDA_MARLIN` imprime la tabla de equivalencias de §5.4.

---

## 2. Encender y comprobar

1. Enciende la impresora (Pi y placa a la vez). Espera ~1 min.
2. Abre Mainsail. Arriba debe poner **Ready**. En *Máquina → Sistema* aparecen dos MCU:
   `mcu` (la placa) y `rpi` (la Pi, para el acelerómetro).
3. Si sale un error en rojo, lee el mensaje: casi siempre dice qué falta (ver §9).

Tras un `FIRMWARE_RESTART`, un `SAVE_CONFIG` o reiniciar Klipper **se pierde el homing**:
vuelve a hacer `G28` antes de mover.

---

## 3. Homing (`G28`)

`G28` (botón **Home** de Mainsail) hace, por este orden:

1. **Baja la cama 5 mm** para separar boquilla y plato.
2. **X**: el cabezal se separa 5 mm, va a 15 mm/s hacia el marco de X mínimo y **se para al
   tocarlo** (lo detecta el acelerómetro). Retrocede 3 mm.
3. **Y**: igual hacia el marco de Y mínimo.
4. **Z**: aparece un diálogo **"Baja el brazo de la sonda y pulsa Listo"**.
   - Baja el brazo y pulsa **Listo** (o escribe `SONDA_LISTA`). La cama sube hasta que la sonda
     toca y se fija Z.
   - Al terminar sale **"Sondeo terminado. SUBE el brazo"**: súbelo y pulsa **Recogida**
     (`SONDA_GUARDADA`).

Otras formas:
- `G28 X`, `G28 Y`, `G28 X Y`: solo esos ejes (sin sonda).
- `G28 Z`: solo Z (exige X e Y ya homeados).

> ⚠️ **No uses `G28.1 X` / `G28.1 Y`**: es el homing antiguo de Klipper y busca los finales de
> carrera, que ya no están. El motor empujaría contra el marco.
>
> ⚠️ Los primeros homings tras tocar algo, **vigílalos**: si el acelerómetro no detecta el
> choque (cable INT1 suelto), el motor sigue empujando contra el marco hasta acabar el
> recorrido. Si oyes rascar más de 1 s, corta la corriente. Si el que falla es el I2C del
> acelerómetro, el homing da error **antes** de moverse hacia el marco.

---

## 4. Antes de imprimir: calibraciones

Se hacen una vez (y se repiten tras cambios mecánicos). `SAVE_CONFIG` las guarda al final de
`printer.cfg` y reinicia Klipper (hay que volver a hacer `G28`).

| Calibración | Comando | Estado |
|---|---|---|
| Altura de la sonda | `G28` → `SONDA_LISTA` → `PROBE_CALIBRATE` (prueba del papel con `TESTZ Z=-0.1`… → `ACCEPT`) → `SAVE_CONFIG` | **pendiente** (hoy `z_offset: 0.70` heredado de Marlin) |
| Precisión de la sonda | `PROBE_ACCURACY` (con el brazo bajado) | pendiente |
| PID del hotend | `PID_CALIBRATE HEATER=extruder TARGET=210` → `SAVE_CONFIG` | pendiente (PID de Marlin) |
| Extrusor | A 200 °C: marca 120 mm de filamento, `M83`, `G1 E100 F60`, mide lo que queda y corrige `rotation_distance` (`nuevo = actual × extruido_real / 100`) | pendiente |
| Tramado (4 tornillos M3) | §4.1 — **antes** de la malla | pendiente (faltan las coordenadas de los tornillos) |
| Malla de la cama | `BED_MESH_CALIBRATE` (pide la sonda) → `BED_MESH_PROFILE SAVE=default` → `SAVE_CONFIG` | pendiente |
| Input shaper | §6.3 | **hecho** 2026-11-20 |
| Homing por choque | §7 | **hecho** 2026-11-21 |

`BED_MESH_CALIBRATE` usa el mismo diálogo de la sonda que `G28`.

### 4.1 Tramado de la cama (4 tornillos M3)

Deja la cama paralela al recorrido de la boquilla girando sus 4 tornillos. Hazlo **antes** de
la malla: la malla solo corrige lo que queda. Config: `klipper-config/mk4/tramado.cfg`.

> Hasta medir las posiciones reales de los tornillos, los dos comandos responden
> *Tramado sin configurar* (las coordenadas de `tramado.cfg` son provisionales).

**Con la sonda (recomendado)**: `SCREWS_TILT_CALCULATE` (o `G35`, como en Marlin).
1. `G28`.
2. `SCREWS_TILT_CALCULATE`. Con la sonda manual sale el diálogo de bajar el brazo, como en la
   malla. Mide junto a cada tornillo y responde, tomando como referencia el delantero izquierdo:
   ```
   delante-der : x=…, y=…, z=… : adjust CW 00:15
   ```
   `CW 00:15` = gira **en sentido horario un cuarto de vuelta** (00:15 son 15 minutos de reloj;
   01:00 = una vuelta = 0.5 mm con M3). `CCW` = antihorario. En el tornillo de referencia no se toca.
3. Gira cada tornillo lo indicado y repite el paso 2 hasta que todos den `00:00`–`00:03`
   (no hace falta `G28` entre pasadas, el de referencia no se mueve).
4. Sentido comprobado en la MK4: **horario (CW) acerca la cama a la boquilla** =
   `screw_thread: CW-M3`. Si algún día cambias tornillos o tuercas y el error crece al girar
   como indica, pasa a `CCW-M3` en los dos `probe_*.cfg`.
5. Al terminar: `PROBE_CALIBRATE` si cambió mucho la altura, y luego la malla.

Mainsail y Fluidd muestran el resultado también en un cuadro.

**Sin sonda (prueba del papel)**: `BED_SCREWS_ADJUST` (el *Level corners* de Marlin). Con la
sonda manual, el brazo **subido** (`SONDA_GUARDADA`). La boquilla va a Z=0 sobre cada tornillo:
ajusta hasta que el papel roce y responde `ACCEPT` (estaba bien) o `ADJUSTED` (lo has tocado). Si
alguno fue `ADJUSTED`, vuelve a empezar la ronda sola. `ABORT` para salir.

---

## 5. Imprimir

### 5.1 Slicer (Cura u otro)

G-code de inicio y fin de la máquina en el slicer:

```
; Start G-code
PRINT_START EXTRUDER={material_print_temperature_layer_0}

; End G-code
PRINT_END
```

- `PRINT_START` **no hace homing** (como con Marlin): haz `G28` antes de lanzar la impresión.
  Se niega a empezar si falta homing o si la sonda sigue bajada. Carga la malla `default` si
  existe, calienta, purga una línea en el borde y empieza.
- `PRINT_END` retrae, baja la cama 10 mm, aparca el cabezal en la esquina, apaga el hotend, el
  ventilador y los motores.

### 5.2 Lanzar

1. `G28` (con la sonda) — §3.
2. Mainsail → *Archivos G-code* → subir el `.gcode` → *Imprimir*.
3. Durante la impresión: *Pausa / Reanudar / Cancelar*, ajuste de velocidad y flujo, y
   **cancelar un objeto** concreto (`[exclude_object]`; el G-code debe traer las etiquetas de
   objeto: en Moonraker, `enable_object_processing: True` en `[file_manager]`).

### 5.3 Corriente de los motores (`M907`)

Igual que en Marlin, en mA (tope 1500):
```
M907              ; solo informa
M907 X850         ; X e Y comparten canal: X o Y cambian los dos
M907 Z1200 E800
```
Valores de referencia: XY 850, Z 1200, E 800. No se guarda: vuelve al valor de `printer.cfg`
al reiniciar.

### 5.4 Comandos de Marlin en Klipper

Puedes seguir escribiendo los comandos de Marlin que conoces. Los básicos los entiende Klipper
tal cual. Los demás están en `marlin_compat.cfg`: hacen lo equivalente y te dicen en la consola
el comando de Klipper (`Klipper: ...`), para que lo vayas aprendiendo. En la consola,
`AYUDA_MARLIN` muestra esta tabla.

**Iguales que en Marlin:** `G0/G1`, `G4`, `G28`, `G90/G91`, `G92`, `M82/M83`, `M84`,
`M104/M109/M105`, `M106/M107`, `M112`, `M114`, `M115`, `M117`, `M119`, `M204`, `M220/M221`,
`M400`, `M907`.

| Marlin | Qué hace en la MK4 | Comando de Klipper |
|---|---|---|
| `M500` | Explica cómo se guarda | `SAVE_CONFIG` (solo calibraciones; reinicia Klipper). Lo demás se edita en `printer.cfg` |
| `M501` / `M502` | Explica | `FIRMWARE_RESTART` descarta cambios en vivo; no hay "valores de fábrica" aparte |
| `M503` | Resumen de ajustes (pasos, velocidades, PID, PA, sonda, malla, shaper, corrientes) | — (Máquina → `printer.cfg`) |
| `M92 E…` | Aplica E en vivo; X/Y/Z dice qué poner | `SET_EXTRUDER_ROTATION_DISTANCE` / `rotation_distance` |
| `M201` / `M203` | Aceleración / velocidad máxima | `SET_VELOCITY_LIMIT ACCEL=` / `VELOCITY=` |
| `M205` | Lo más parecido al jerk | `SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=` |
| `M17` | Activa los motores | `SET_STEPPER_ENABLE STEPPER=… ENABLE=1` |
| `G29` | Malla (con el diálogo de la sonda) | `BED_MESH_CALIBRATE` |
| `G35` | Tramado: cuánto girar cada tornillo (§4.1) | `SCREWS_TILT_CALCULATE` |
| *Level corners* (pantalla) | Tramado con papel (§4.1) | `BED_SCREWS_ADJUST` |
| `M420 S1` / `S0` / `V` | Carga / quita / muestra la malla | `BED_MESH_PROFILE LOAD=default` / `BED_MESH_CLEAR` / `BED_MESH_OUTPUT` |
| `M851` | Muestra el offset de la sonda | `PROBE_CALIBRATE` (+ `SAVE_CONFIG`) |
| `G30` / `M48` | Un sondeo / repetibilidad (brazo bajado) | `PROBE` / `PROBE_ACCURACY` |
| `M290 Z…` | Babystep | `SET_GCODE_OFFSET Z_ADJUST=… MOVE=1` |
| `M303 S…` | PID del hotend | `PID_CALIBRATE HEATER=extruder TARGET=…` (+ `SAVE_CONFIG`) |
| `M301` | Muestra el PID | — |
| `M900 K…` | Pressure advance (= linear advance) | `SET_PRESSURE_ADVANCE ADVANCE=…` |
| `M600` | Pausa con diálogo para cambiar filamento | `PAUSE` … `RESUME` |
| `M108` | Continúa: la sonda si espera, o la pausa | `SONDA_LISTA` / `RESUME` |

Solo de Klipper y útiles: `HELP`, `STATUS`, `GET_POSITION`, `QUERY_PROBE`, `FIRMWARE_RESTART`
(tras un error o un `M112`), `SHAPER_CALIBRATE`, `HOME_ACCEL`. Referencia completa:
[G-codes de Klipper](https://www.klipper3d.org/G-Codes.html).

---

## 6. Acelerómetro (ADXL345)

### 6.1 Cableado (a la cabecera de 40 pines de la Pi)

| Módulo | Pin de la Pi | Para qué |
|---|---|---|
| `VCC`/`Vin` (5 V) | **2** | alimentación (el módulo tiene su regulador a 3.3 V) |
| `GND` | **6** | masa |
| `SDA` | **3** | datos I2C |
| `SCL` | **5** | reloj I2C |
| `INT1` | **11** (GPIO17) | aviso de choque para el homing X/Y |
| `CS`, `SDO`, `VS`, `INT2`, `3V3` | — | sin conectar |

- Si cambias de módulo y lo alimentas por 5 V: **antes de conectar SDA/SCL**, mide SDA–GND en
  el módulo: debe dar ≈ 3.3 V. Si da 5 V, no lo conectes (dañaría la Pi).
- Fijación rígida al cabezal, sin cinta ni bridas, y que no toque metal.
- Orientación actual: montado **invertido en Z**, con X de la impresora = −X del chip →
  `axes_map: -x, y, -z` en `sensors.cfg`. Si lo montas de otra forma, hay que rehacer §6.2.

> Ojo con los módulos: de los dos primeros, uno era **defectuoso** (respondía pero los tres
> ejes daban siempre el mismo valor) y ninguno funcionaba por SPI. Por eso va por I2C con un
> extra propio (`extras/adxl345_i2c.py`), leído a ~790 muestras/s.

### 6.2 Comprobar que mide

En la consola de Mainsail:

1. **`ACCELEROMETER_QUERY`** con el cabezal quieto → algo como `(-1000, 500, 8900)` mm/s²: la
   gravedad (≈ 9800) cae casi entera en Z. Si los tres ejes dan siempre el mismo número, o
   todos ≈ ±150000, el sensor no mide (módulo roto).
2. **`MEASURE_AXES_NOISE`** → decenas de mm/s² por eje (hoy 33/44/82). Cientos = algo suelto.
3. **Orientación** (esta versión de Klipper no tiene `AXES_MAP_CALIBRATION`). Con X/Y homeados:
   ```
   ACCELEROMETER_MEASURE
   G91
   G1 X30 F6000
   G90
   ACCELEROMETER_MEASURE NAME=ejex
   ```
   El CSV queda en la Pi en `/tmp/adxl345_i2c-cabezal-ejex.csv`. Al arrancar el movimiento
   hacia +X, la aceleración debe subir en la columna **x** con signo **+**. Lo mismo con
   `G1 Y30` → columna **y** positiva. Si sale en otra columna o con otro signo, corrige
   `axes_map` en `sensors.cfg`.

### 6.3 Input shaper (calidad de impresión)

Compensa las vibraciones del cabezal y permite acelerar más sin "fantasmas" en la pieza.

1. `G28`, cama despejada, mano en el interruptor (el cabezal vibra fuerte ~2 min).
2. **`SHAPER_CALIBRATE`** → recomienda un filtro y frecuencia por eje.
3. **`SAVE_CONFIG`** (los guarda y reinicia).
4. Ajusta `max_accel` en `[printer]` de `printer.cfg` por debajo del máximo que sugiere para el
   eje más débil.

Resultado actual (2026-11-20):

| Eje | Filtro | Frecuencia | `max_accel` sugerido |
|---|---|---|---|
| X | `3hump_ei` | 116.4 Hz | ≤ 8900 |
| Y | `2hump_ei` | 52.0 Hz | ≤ 2900 |

→ `max_accel: 2500`. Gráficas en `docs/img/mk4-shaper-*-20261120.png`. Y es el eje débil
(picos a ~25, 43 y 56 Hz): tras tensar correas o reforzar el carro Y, repite la calibración.

Para generar las gráficas, en la Pi: `~/klipper/scripts/calibrate_shaper.py
/tmp/calibration_data_x_*.csv -o /tmp/shaper_x.png` (y lo mismo con `y`).

---

## 7. Homing X/Y por choque: funcionamiento y calibración

### 7.1 Cómo funciona

El ADXL vigila **un eje cada vez** a 3200 muestras/s. Cuando la aceleración supera un umbral
(el frenazo del carro contra el marco), pone **INT1** a 3.3 V. Ese pin entra en la Pi (GPIO17),
que Klipper usa como final de carrera, así que los motores se paran igual que con un
interruptor. La detección se activa **0.1 s después** de arrancar el movimiento, para que el
tirón del arranque no cuente como choque. El punto del choque es `position_endstop` del eje
(X −40, Y −60).

Parámetros en `[accel_endstop]` de `sensors.cfg`:

| Parámetro | Valor | Qué hace |
|---|---|---|
| `threshold_x` | 3.0 g | umbral del choque en X |
| `threshold_y` | 1.5 g | umbral en Y (el choque en Y es más blando) |
| `speed` | 15 mm/s | velocidad hacia el marco (los umbrales se calibraron a esta) |
| `blank_time` | 0.1 s | tiempo sin vigilar tras arrancar |
| `backoff` | 5 mm | se separa antes de buscar el marco |
| `retract` | 3 mm | retrocede tras el choque |
| `overtravel` | 6 mm | en las pruebas, cuánto puede pasarse antes de dar error |

### 7.2 Comandos

| Comando | Para qué |
|---|---|
| `HOME_ACCEL [AXIS=X\|Y\|XY]` | homing por choque (lo usa `G28`) |
| `ACCEL_NOISE_TEST AXIS=X START=75 END=195 [SPEED=15] [THRESHOLDS=1.5,2,3,4,6,8]` | recorre el eje **sin chocar** con cada umbral: el más bajo que sale `clean` es el mínimo usable |
| `ACCEL_CRASH_TEST AXIS=X [SAMPLES=5] [THRESHOLD=3]` | hace `HOME_ACCEL` y luego choca N veces desde 15 mm: mide la repetibilidad |

`ACCEL_NOISE_TEST` necesita el eje homeado. Si aún no lo está: `M84`, mueve a mano el cabezal
al centro del eje y `SET_KINEMATIC_POSITION X=135` (o `Y=130`). `START`/`END` deben quedar
lejos de los dos extremos.

### 7.3 Recalibrar los umbrales

Hazlo si cambias: correas, velocidad de homing, el montaje o el módulo del acelerómetro, o
si el homing falla.

1. **Ruido sin choque**: `ACCEL_NOISE_TEST` del eje. Apunta el umbral más bajo que salga
   `clean` (hoy X: 2 g; Y: 1.25 g o menos).
2. **Choque**: `ACCEL_CRASH_TEST AXIS=<eje> SAMPLES=5 THRESHOLD=<umbral>` empezando un poco
   por encima del mínimo del paso 1.
3. **Lectura del resultado**:
   - Las 5 en el mismo valor, cerca de 0 (±1 paso = 0.013 mm): **bien**.
   - Valores **negativos que crecen** en cada repetición (−0.8, −1.7, −3.4…): el choque no
     llega al umbral a tiempo y el motor pierde pasos. **Baja el umbral**, o revisa la mecánica
     (en Y: las dos correas deben ir igual de tensas).
   - Valores **positivos** o un `HOME_ACCEL` que se para a mitad de recorrido: falso disparo.
     **Sube el umbral**.
4. Pon el umbral bueno en `threshold_x`/`threshold_y` de `sensors.cfg` y `FIRMWARE_RESTART`.
5. Tras `ACCEL_CRASH_TEST`, haz `G28` antes de imprimir.

Resultados de referencia (2026-11-21, 15 mm/s):

| Eje | Sin choque | Choque (5 veces) |
|---|---|---|
| X | 1.5 g salta, 2 g no | 3 g: todas a +0.013 mm |
| Y | 1.25 g no salta | 1.5 g: todas a 0.000 mm · 2–3 g: detecta 0.8–5 mm tarde |

### 7.4 Si quitas el acelerómetro

- El **input shaper** sigue funcionando: sus valores están guardados en `printer.cfg`.
- El **homing X/Y deja de funcionar**. Para volver a interruptores: monta los finales de
  carrera (X en `PC13`, Y en `PC0`, ajustados para activarse al tocar el marco) y en
  `macros.cfg` cambia en la macro `G28` la línea `HOME_ACCEL AXIS=…` por
  `G28.1 {"X" if hx else ""} {"Y" if hy else ""}`.
- Con la sonda de boquilla (§7.5) activa, **Z tampoco**: vuelve a `probe_manual.cfg`.

### 7.5 Sonda Z por toque de boquilla (EXPERIMENTAL, sin probar en la máquina)

La **boquilla hace de sonda**: la cama sube hasta tocarla y el ADXL nota el toque (eje Z del
chip → INT1, el mismo pin del homing X/Y). Sin brazo que bajar: `G28` y la malla van solos, y
mide justo debajo de la boquilla (sin offset X/Y). Código: `extras/accel_probe.py`; config:
`probe_accel.cfg`. Probado solo en simulación (`klipper-config/mk4/test/smoke.sh`).

**Antes de nada:**
- **Boquilla limpia**: una gota de plástico falsea la medida. Sondea con el hotend a ~150 °C
  (el plástico se ablanda sin gotear) o en frío tras limpiarla.
- **Mano en el interruptor** en todas las pruebas: si no detecta el toque, la cama empuja la
  boquilla. En `probe_accel.cfg` el recorrido de más está limitado (`position_min: -0.5`) y
  puedes bajar la corriente de Z al sondear (`z_current`).
- Si en el bloque `#*# SAVE_CONFIG` del final de `printer.cfg` hay un `#*# [probe]` (de un
  `PROBE_CALIBRATE` con la sonda manual), Klipper dirá *Printer object 'probe' already created*:
  cámbialo a `#*# [accel_probe]` a mano esa única vez, o bórralo.

**Activar** (en `printer.cfg`, sección *Sonda Z*): comenta `[include probe_manual.cfg]`, quita
el `#` de `[include probe_accel.cfg]` y `FIRMWARE_RESTART`. Para volver, al revés.

**Puesta a punto, en este orden:**

1. **Ruido de la cama sin tocar nada.** Con la boquilla bien separada de la cama (varios cm):
   ```
   G28 X Y
   SET_KINEMATIC_POSITION Z=0
   G1 Z15 F300
   ACCEL_NOISE_TEST AXIS=Z START=15 END=3
   ```
   `SET_KINEMATIC_POSITION Z=0` toma la altura actual como 0; la prueba sube y baja la cama
   entre 15 y 3 mm *por debajo* de ahí, sin llegar a la boquilla. Prueba 0.125 / 0.25 / 0.5 /
   1 / 2 g. El umbral mínimo sin falsos disparos es el suelo: pon `threshold` en
   `probe_accel.cfg` a **el doble** de ese valor.
2. **Primer toque, con el recorrido acotado.** `SET_KINEMATIC_POSITION Z=50` (altura ficticia
   para poder subir la cama) y súbela a pasos (`G91`, `G1 Z-1 F300` varias veces, `G90`, o los
   botones de Mainsail) hasta dejar ~3 mm entre boquilla y cama. Entonces:
   ```
   SET_KINEMATIC_POSITION Z=3
   PROBE
   ```
   Como mucho sube 3.5 mm. Debe pararse al tocar y responder `Result: … contact at z=…`
   (≈ 0 si los 3 mm eran exactos). Si toca y sigue empujando: corta la corriente y baja el
   umbral. Si se para antes de tocar: falso disparo, sube el umbral. Para probar umbrales sin
   editar: `PROBE TAP_THRESHOLD=0.3`.
3. **Repetibilidad:** `PROBE_ACCURACY SAMPLES=10` (sigue con el Z provisional). Bien si el
   rango es **< 0.02 mm**; compáralo con el de la sonda manual (`M48` / `PROBE_ACCURACY` con
   `probe_manual.cfg`).
4. **Homing:** `G28` completo (ya hace Z con la boquilla en el centro del plato).
5. **Altura:** `PROBE_CALIBRATE` (prueba del papel: `TESTZ Z=-0.05`… hasta que roce, `ACCEPT`) y
   `SAVE_CONFIG`. El `z_offset` se guarda en `[accel_probe]`, aparte del de la sonda manual.
6. **Malla:** `BED_MESH_CALIBRATE` → `BED_MESH_PROFILE SAVE=default` → `SAVE_CONFIG`.

| Opción (`probe_accel.cfg`) | Valor | Qué hace |
|---|---|---|
| `threshold` | 0.5 g | umbral del toque (calibrar en el paso 1) |
| `blank_time` | 0.15 s | no vigila al empezar a subir la cama |
| `settle_time` | 0.3 s | espera antes de cada toque para que se calme el cabezal |
| `z_current` | (apagado) | amperios en Z al sondear; menos fuerza si no detecta (normal: 1.2) |
| `speed` | 3 mm/s | velocidad de subida al tocar (más rápido = toque más fuerte) |
| `[stepper_z] position_min` | −0.5 | cuánto puede pasarse por debajo de 0 |

---

## 8. Mantenimiento: qué repetir tras cada cambio

| Cambias… | Repite |
|---|---|
| Correas, poleas, carro | §7.3 (umbrales), §6.3 (shaper) |
| Montaje o módulo del ADXL | §6.2 (comprobar y orientación), §7.3, §6.3 |
| Boquilla, sonda, cama | tramado (§4.1), `PROBE_CALIBRATE`, malla |
| Hotend, termistor | `PID_CALIBRATE` |
| Extrusor | `rotation_distance` del extrusor |
| Velocidad de homing (`speed`) | §7.3 (los umbrales dependen de ella) |

---

## 9. Problemas frecuentes

| Síntoma | Causa / solución |
|---|---|
| La Pi no aparece en la Wi-Fi | Nombre/clave en `mk4-red.txt` (§1.1); `pais = ES`; hotspot en canal 12–13 con país mal. Prueba por cable (§1.2) |
| `mk4.local` no responde | mDNS falla a ratos con el hotspot: usa la IP del router o el cable directo |
| `mcu 'rpi': Unable to connect` | En la Pi: `sudo systemctl restart klipper-mcu` y luego `FIRMWARE_RESTART` |
| `ADXL345 I2C read failed` / `Remote I/O error` | Cable SDA/SCL/alimentación del acelerómetro suelto. Reasienta los Dupont |
| `ACCELEROMETER_QUERY` da siempre lo mismo o ±150000 | Módulo roto (§6.1) |
| `HOME_ACCEL` se para antes del marco | Falso disparo: sube `threshold_<eje>` (§7.3) |
| `No trigger on accel_endstop after full movement` o el motor rasca contra el marco | No detecta el choque: cable INT1 (pin 11) suelto, umbral demasiado alto o correas desiguales (§7.3) |
| `Sin homing: haz G28…` al imprimir | `PRINT_START` exige `G28` completo (X, Y y Z) |
| `Sonda desplegada…` al imprimir | Sube el brazo y `SONDA_GUARDADA` |
| Tras `SAVE_CONFIG` no se mueve | Se perdió el homing: `G28` |
| Error al cargar con `G28_ACCEL` u otro nombre | Klipper no admite nombres de comando con letra+número al principio (`G28_…`): por eso es `HOME_ACCEL` |

---

## 10. Dónde está cada cosa

| Archivo | Qué |
|---|---|
| `klipper-config/mk4/printer.cfg` | máquina: ejes, hotend, sonda, malla, `max_accel`, bloque `SAVE_CONFIG` |
| `klipper-config/mk4/macros.cfg` | `G28`, sonda manual, `PRINT_START`/`PRINT_END`, `M907` |
| `klipper-config/mk4/marlin_compat.cfg` | comandos de Marlin (`M500`, `M503`, `G29`, `G35`, `M851`, `M303`, `M900`, `M600`…) y `AYUDA_MARLIN` |
| `klipper-config/mk4/probe_manual.cfg` / `probe_accel.cfg` | sonda Z (una de las dos) y sus coordenadas de tramado |
| `klipper-config/mk4/tramado.cfg` | tornillos de la cama: `BED_SCREWS_ADJUST`, envoltorio de `SCREWS_TILT_CALCULATE` |
| `klipper-config/mk4/moonraker.conf` | Moonraker: actualizaciones de Mainsail, Fluidd y Klipper |
| `klipper-config/mk4/sensors.cfg` | MCU `rpi`, acelerómetro, `[resonance_tester]`, `[accel_endstop]` |
| `klipper-config/mk4/extras/` | `adxl345_i2c.py` (ADXL por I2C), `accel_endstop.py` (homing por choque), `accel_probe.py` (sonda de boquilla, §7.5), `adxl345_3w.py` (SPI 3 hilos, sin usar), `dht_iio.py` (sensor ambiente, sin cablear) |
| `klipper-config/mk4/host/` | servicio de red `mk4-red` y plantilla `mk4-red.txt` |
| En la Pi | `~/printer_data/config/` (copia de lo anterior; los `extras/` van enlazados en `~/klipper/klippy/extras/`) |

Los archivos del repo y los de la Pi deben ser iguales: si editas en Mainsail, copia el cambio
al repo.

Pendiente de hardware: acelerómetro de la cama (para diagnosticar la flexión del chasis,
`docs/12` §7) y sensor DHT de ambiente.
