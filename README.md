# Experimental Android IP Rotator (ADB)

**Idioma / Language:** [Español](#espanol) | [English](#english)

---

## Español

### Contenido
- [Descripcion general](#descripcion-general)
- [Objetivo del experimento](#objetivo-del-experimento)
- [Entorno de pruebas real](#entorno-de-pruebas-real)
- [Funcionamiento del script](#funcionamiento-del-script)
- [Modos de prueba implementados](#modos-de-prueba-implementados)
- [Resultados observados (IP publica)](#resultados-observados-ip-publica)
- [Captura y analisis de logs](#captura-y-analisis-de-logs)
- [Hallazgos clave en los logs](#hallazgos-clave-en-los-logs)
- [Resultados resumidos](#resultados-resumidos)
- [Nota sobre ADB y modo avion](#nota-sobre-adb-y-modo-avion)
- [Reproducibilidad](#reproducibilidad)
- [Conclusion principal](#conclusion-principal)
- [Lineas de investigacion futura](#lineas-de-investigacion-futura)
- [Notas importantes](#notas-importantes)
- [Creditos](#creditos)
- [Licencia](#licencia)

---

### Descripcion general

Este repositorio documenta una **investigacion tecnica real y reproducible** cuyo objetivo es analizar si es posible forzar la **rotacion de una direccion IPv4 publica** utilizando un telefono Android conectado a un computador mediante **USB tethering**, controlando el estado de red **exclusivamente desde el PC usando ADB**, sin acceso root y sin aplicaciones firmadas como sistema.

Este proyecto **no es una herramienta de rotacion de IP**.  
Es un experimento para documentar **los limites reales del sistema Android, del modem y del operador movil (CGNAT)**.

El valor del repositorio esta en la **honestidad tecnica**: mostrar que funciona, que no, y por que.

---

### Objetivo del experimento

La hipotesis inicial fue:

> Si se corta completamente la conexion movil y se vuelve a levantar, el operador deberia asignar una nueva IP publica.

El objetivo fue comprobar si ese ciclo puede forzarse **unicamente desde ADB**, sin interaccion manual una vez iniciada la prueba, y validar el resultado mediante **mediciones externas (IP publica)** y **logs internos del sistema**.

---

### Entorno de pruebas real

- **Dispositivo:** Redmi Note 13 Pro Plus
- **Sistema operativo:** HyperOS (Xiaomi / MIUI-based)
- **Opciones de desarrollador:**
  - USB Debugging habilitado
  - **USB Debugging (Security settings) habilitado**
- **Conectividad:** USB tethering
- **Operador movil:** IPv4 bajo CGNAT
- **Sistema operativo del PC:** Windows
- **Herramientas:** ADB + Python 3.x
- **Restricciones del experimento:**
  - Sin root
  - Sin VPN / proxies
  - Sin apps de sistema
  - Sin cambios de APN
  - Sin interaccion manual durante la ejecucion automatica

---

### Funcionamiento del script

El script (`check_ip_data.py`) sigue un flujo controlado y medible:

1. Obtener la IP publica actual desde el PC
2. Ejecutar cambios de estado de red en el telefono via ADB
3. Esperar la reconexion
4. Obtener nuevamente la IP publica
5. Comparar resultados

El **criterio de exito** es exclusivamente el **cambio observable de la IP publica**.

---

### Modos de prueba implementados

#### Modo A — Modo avion via ADB

```
airplane_mode ON -> esperar -> airplane_mode OFF
```

#### Modo B — Modo avion + datos moviles via ADB

```
airplane_mode ON -> datos OFF -> esperar -> airplane_mode OFF -> datos ON
```

Ambos modos se ejecutan sin tocar el telefono una vez iniciado el script.

---

### Resultados observados (IP publica)

> Nota: Los valores de IP mostrados aqui son ejemplos observados durante pruebas. Si prefieres, puedes enmascararlos (ej. `190.130.xxx.xxx`) para publicar el repo.

#### Toggle manual (UI del sistema)

```
IP BEFORE: 190.130.101.73
IP AFTER : 190.130.99.67
```

#### Toggle via ADB (console)

```
IP BEFORE: 190.130.99.67
IP AFTER : 190.130.99.67
```

---

### Captura y analisis de logs

Para analizar el comportamiento interno del sistema se utilizaron logs del buffer `radio` de Android.

#### Comandos usados (Windows)

**Limpiar buffer antes de cada prueba:**
```
adb logcat -b radio -c
```

**Capturar log del toggle manual (UI):**
```
adb logcat -b radio -v time | findstr /i "ServiceState RIL RADIO airplane" > radio_test_MANUAL.log
```

**Capturar log del toggle via ADB:**
```
adb logcat -b radio -c
adb logcat -b radio -v time | findstr /i "ServiceState RIL RADIO airplane" > radio_test_CONSOLE.log
```

**Tiempos de espera** entre activacion y desactivacion del modo avion: **40 a 60 segundos**.

> Nota importante: `logcat` usa buffers circulares/persistentes; limpiar antes de cada iteracion fue critico para evitar analizar eventos antiguos.

---

### Hallazgos clave en los logs

#### Toggle manual (UI)

Indicadores de renegociacion real del estado de radio:

- Cambios en `mChannelNumber`
- Cambios en `mCellBandwidths`
- Variaciones en carrier aggregation
- Tear down completo de data bearers
- Nuevo attach a la red movil

<details>
  <summary>Ejemplo de lineas relevantes (UI)</summary>

  ```
  [ServiceState] mChannelNumber=675
  [ServiceState] mCellBandwidths=
  [DataNetworkController] Tear down all data networks (AIRPLANE_MODE)
  ```
</details>

#### Toggle via ADB

Observado de forma consistente:

- Cambio del flag `airplane_mode_on`
- Reconexion rapida
- Ausencia de renegociacion fisica
- Sin cambios de canal/banda

Resultado:

- El modem no se desancla completamente de la celda
- El operador mantiene el mismo contexto de red
- La IP publica permanece sin cambios bajo CGNAT

---

### Resultados resumidos

| Metodo | Iteraciones | Tiempo de espera | ¿Cambia IP publica? |
|---|---:|---:|---|
| Manual (UI) | multiples | 40–60 s | Si |
| ADB (console) | multiples | 40–60 s | No |

---

### Nota sobre ADB y modo avion

Existe la creencia comun de que ejecutar:

```
settings put global airplane_mode_on 1
```

equivale al toggle manual del modo avion.

Las pruebas y los logs muestran que esto no es necesariamente cierto.

Este comando modifica el estado logico del sistema, pero no garantiza la ejecucion del flujo completo de apagado/encendido del radio, el cual depende de eventos del framework y del RIL protegidos por permisos de sistema y puede variar segun el OEM y la version de Android.

---

### Reproducibilidad

- Pruebas ejecutadas multiples veces
- Tiempos de espera controlados (40–60 segundos)
- Dos metodos comparados (manual vs ADB)
- Dos logs independientes generados por metodo
- Buffer de logcat limpiado antes de cada iteracion
- Criterio de exito claramente definido (cambio de IP publica)

---

### Conclusion principal

Este no es un problema de scripting.

Es una limitacion arquitectonica intencional:

- ADB puede modificar estados logicos del sistema
- No tiene permisos para ejecutar el flujo completo de apagado/encendido del modem
- El toggle manual dispara eventos del framework y del RIL que ADB no replica
- Bajo CGNAT, la IP publica depende del estado fisico del attach a la red

ADB no puede garantizar una rotacion de IP sin acceso a permisos de sistema.

---

### Lineas de investigacion futura

- Correlacion entre cambios de IP y cambios de puerto remoto
- Emision de broadcasts adicionales relacionados con airplane mode
- Uso de APIs ocultas de Telephony
- Shizuku para elevacion controlada de permisos
- Hooks de framework (LSPosed / Xposed)
- Analisis directo del RIL del fabricante
- Diferencias entre OEMs y versiones de Android
- Politicas de asignacion IP del operador movil

---

### Notas importantes

- HyperOS / MIUI agrega capas adicionales sobre el RIL estandar
- Algunos comandos ADB funcionan distinto segun el fabricante
- Este proyecto no debe usarse como herramienta de anonimato
- Los resultados dependen tanto del sistema operativo como del operador

---

### Creditos

Proyecto desarrollado por el autor del repositorio.

Herramientas de IA (ChatGPT, OpenAI) se usaron unicamente como apoyo para analisis y redaccion.  
Toda la experimentacion, validacion y conclusiones provienen de pruebas reales sobre hardware y red.

---

### Licencia

Uso libre con fines educativos y de investigacion.

---

## English

### Contents
- [Overview](#overview)
- [Experiment goal](#experiment-goal)
- [Real test environment](#real-test-environment)
- [Script flow](#script-flow)
- [Implemented test modes](#implemented-test-modes)
- [Observed results (Public IP)](#observed-results-public-ip)
- [Log capture and analysis](#log-capture-and-analysis)
- [Key findings](#key-findings)
- [Summary table](#summary-table)
- [Note on ADB and airplane mode](#note-on-adb-and-airplane-mode)
- [Reproducibility](#reproducibility-1)
- [Main conclusion](#main-conclusion)
- [Future research directions](#future-research-directions)
- [Important notes](#important-notes)
- [Credits](#credits)
- [License](#license)

---

### Overview

This repository documents a **real, reproducible technical investigation** aimed at evaluating whether it is possible to force **public IPv4 rotation** using an Android phone connected to a computer via **USB tethering**, controlling network state **strictly from the PC using ADB**, with no root access and no system-signed apps.

This project **is not an IP rotation tool**.  
It is an experiment to document **real-world limitations** imposed by Android, the modem, and the mobile carrier (CGNAT).

The value of this repository is **technical honesty**: showing what works, what does not, and why.

---

### Experiment goal

Initial hypothesis:

> If the mobile connection is fully dropped and brought back, the carrier should assign a new public IP.

Goal: verify whether that cycle can be forced **only via ADB**, with no manual interaction once the test starts, and validate results using **external measurements (public IP)** and **internal system logs**.

---

### Real test environment

- **Device:** Redmi Note 13 Pro Plus
- **OS:** HyperOS (Xiaomi / MIUI-based)
- **Developer options:**
  - USB Debugging enabled
  - **USB Debugging (Security settings) enabled**
- **Connectivity:** USB tethering
- **Carrier:** IPv4 under CGNAT
- **PC OS:** Windows
- **Tools:** ADB + Python 3.x
- **Constraints:**
  - No root
  - No VPN / proxies
  - No system apps
  - No APN changes
  - No manual interaction during automated execution

---

### Script flow

The script (`check_ip_data.py`) follows a measurable flow:

1. Read current public IP from the PC
2. Trigger network state changes on the phone via ADB
3. Wait for reconnection
4. Read public IP again
5. Compare results

**Success criteria:** **public IP must change**.

---

### Implemented test modes

#### Mode A — Airplane mode via ADB

```
airplane_mode ON -> wait -> airplane_mode OFF
```

#### Mode B — Airplane mode + Mobile data via ADB

```
airplane_mode ON -> data OFF -> wait -> airplane_mode OFF -> data ON
```

Both modes run without touching the phone after the script starts.

---

### Observed results (Public IP)

> Note: IP values below are examples from real tests. Consider masking them (e.g., `190.130.xxx.xxx`) before publishing.

#### Manual toggle (System UI)

```
IP BEFORE: 190.130.101.73
IP AFTER : 190.130.99.67
```

#### ADB-only toggle (Console)

```
IP BEFORE: 190.130.99.67
IP AFTER : 190.130.99.67
```

---

### Log capture and analysis

To analyze internal behavior, `logcat` **radio** buffer logs were collected.

#### Commands used (Windows)

**Clear buffer before each run:**
```
adb logcat -b radio -c
```

**Capture manual UI toggle log:**
```
adb logcat -b radio -v time | findstr /i "ServiceState RIL RADIO airplane" > radio_test_MANUAL.log
```

**Capture ADB toggle log:**
```
adb logcat -b radio -c
adb logcat -b radio -v time | findstr /i "ServiceState RIL RADIO airplane" > radio_test_CONSOLE.log
```

**Wait time** between enabling/disabling airplane mode: **40 to 60 seconds**.

> Important: `logcat` buffers are persistent/circular; clearing before each iteration prevents mixing old events into the analysis.

---

### Key findings

#### Manual toggle (UI)

Indicators of real radio renegotiation:

- `mChannelNumber` changes
- `mCellBandwidths` changes
- Carrier aggregation state variations
- Full teardown of data bearers
- New attach to the mobile network

<details>
  <summary>Example relevant lines (UI)</summary>

  ```
  [ServiceState] mChannelNumber=675
  [ServiceState] mCellBandwidths=
  [DataNetworkController] Tear down all data networks (AIRPLANE_MODE)
  ```
</details>

#### ADB toggle

Consistent observations:

- `airplane_mode_on` flag changes
- Fast “reconnect”
- No physical renegotiation signals
- No channel/band changes

Result:

- The modem does not fully detach from the cell
- The carrier keeps the same network context
- Public IP remains unchanged under CGNAT

---

### Summary table

| Method | Iterations | Wait time | Public IP changes? |
|---|---:|---:|---|
| Manual (UI) | multiple | 40–60 s | Yes |
| ADB (console) | multiple | 40–60 s | No |

---

### Note on ADB and airplane mode

A common belief is that:

```
settings put global airplane_mode_on 1
```

is equivalent to the manual UI airplane mode toggle.

Tests and logs show that this is not necessarily true.

This command changes a logical system state, but does not guarantee the full radio shutdown/startup flow, which depends on framework/RIL events gated by system permissions and may vary across OEMs and Android versions.

---

### Reproducibility

- Multiple runs performed
- Controlled wait time (40–60 seconds)
- Two methods compared (manual vs ADB)
- Two independent logs generated per method
- `logcat` buffer cleared before each iteration
- Clear success criteria (public IP must change)

---

### Main conclusion

This is not a scripting problem.

It is an intentional architectural limitation:

- ADB can modify logical system states
- It lacks privileges to execute a full modem shutdown/startup flow
- Manual toggles trigger framework/RIL events ADB does not replicate
- Under CGNAT, public IP depends on the physical attach context

ADB cannot guarantee IP rotation without system-level privileges.

---

### Future research directions

- Correlate public IP changes vs remote port changes
- Emit additional airplane-mode-related broadcasts
- Hidden Telephony APIs
- Shizuku-based controlled privilege elevation
- Framework hooks (LSPosed / Xposed)
- Vendor RIL analysis
- OEM / Android version differences
- Carrier IP allocation policy research

---

### Important notes

- HyperOS / MIUI adds layers on top of standard RIL behavior
- Some ADB commands behave differently across OEMs
- This project must not be used as an anonymity tool
- Results depend on both OS and carrier behavior

---

### Credits

Developed by the repository author.

AI tools (ChatGPT, OpenAI) were used only as support for analysis and writing.  
All experimentation, validation, and conclusions come from real hardware/network testing.

---

### License

Free to use for educational and research purposes.
