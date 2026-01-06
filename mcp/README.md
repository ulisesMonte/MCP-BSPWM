# BSPWM Config MCP

Servidor MCP en Python para trabajar de forma interactiva con tus archivos de configuración bajo el directorio `BSPWM/` de este repositorio.

La idea es doble:

- Desde un **cliente MCP** (Claude Desktop / Inspector MCP, etc.) puedes inspeccionar y editar opciones concretas de tus configs.
- Con el script `client_ai.py` puedes escribir en español cosas como *"pon el borde a 3 píxeles"* y la IA las traduce a llamadas a tools MCP que modifican los archivos reales.

Todos los cambios se aplican directamente sobre los archivos dentro de `BSPWM/`, así que tienes **persistencia** automática.

---

## 1. Requisitos

- Python 3.10 o superior
- Dependencia MCP Python SDK: `mcp[cli]`

Puedes instalarla de dos formas:

### a) Con `uv` (recomendado)

Desde la carpeta `bspwm-mcp/`:

```bash
uv sync
```

Esto instalará las dependencias definidas en `pyproject.toml`.

### b) Con `pip` estándar

Desde la carpeta `bspwm-mcp/`:

```bash
python -m venv .venv
# En Windows
.venv\\Scripts\\activate
# En Linux
source .venv/bin/activate

pip install "mcp[cli]"
```

---

## 2. Estructura esperada

Este servidor asume que la estructura de carpetas es:

- `BSPWM/` (con tus configs reales)
- `bspwm-mcp/` (este proyecto MCP)

Es decir, `BSPWM/` y `bspwm-mcp/` son **carpetas hermanas** en el mismo nivel.

Dentro de `BSPWM/` se espera algo como:

- `bspwm/bspwmrc`
- `polybar/config`, `polybar/colors*.ini`, `polybar/current.ini`
- `sxhkd/sxhkdrc`
- `picom/picom.conf`
- `kitty/kitty.conf`, `kitty/color.ini`
- `nvim/init.lua`

Si cambias esta estructura, sólo tendrías que adaptar la lista de archivos en la función `list_bspwm_files` de `server.py`.

---

## 3. Cómo ejecutar el servidor MCP

### Modo desarrollo (Inspector MCP, etc.)

Desde la carpeta `bspwm-mcp/`:

```bash
mcp dev server.py
```

Si usas `uv` (recomendado):

```bash
uv run --with mcp mcp dev server.py
```

Esto levanta el servidor en modo desarrollo para usarlo con el MCP Inspector o clientes compatibles.

### Ejecución directa

También puedes ejecutarlo como un script normal de Python:

```bash
python server.py
```

En ese caso, `FastMCP` usará su configuración de transporte por defecto.

---

## 4. Cómo ejecutar el cliente IA (modo "asistente en español")

El archivo `client_ai.py` actúa como un pequeño cliente que:

- Llama a la API de OpenAI (modelo por defecto `gpt-4.1-mini`).
- Traduce tus peticiones en español a un **plan JSON** con cambios de configuración.
- Aplica ese plan llamando a las tools MCP del servidor (`set_bspc_config`, `set_polybar_key`, etc.).

### 4.1. Requisitos extra

- Tener la variable de entorno `OPENAI_API_KEY` configurada.
- Tener el paquete `openai` instalado (ya viene en `pyproject.toml`).

### 4.2. Ejecución

Desde `bspwm-mcp/`:

```bash
uv run client_ai.py
```

Al arrancar verás algo como:

- Listado de archivos que el MCP puede editar (`list_bspwm_files`).
- Ejemplos de peticiones en español.

Después puedes escribir frases como:

- "Pon el borde de las ventanas a 3 píxeles".
- "Reduce el gap entre ventanas a 5".
- "Cambia el color de fondo de la barra a #222".

El cliente mostrará el **plan JSON** que genera la IA y luego aplicará los cambios usando el servidor MCP.

---

## 5. Herramientas expuestas por el servidor

El archivo principal es `server.py`. Define un servidor FastMCP y varias **tools** que el modelo o el cliente IA pueden llamar.

### 5.1. `list_bspwm_files()`

- Devuelve un diccionario con listas de rutas relevantes dentro de `BSPWM/`.
- Ejemplo de resultado:

```json
{
  "bspwm": ["bspwm/bspwmrc"],
  "polybar": ["polybar/config", "polybar/colors.ini", ...],
  "sxhkd": ["sxhkd/sxhkdrc"],
  ...
}
```

El modelo o tú (desde Inspector) podéis usar esto para saber qué archivos se pueden leer o editar.

### 5.2. `read_config(relative_path: str) -> str`

- Lee el contenido de un archivo de configuración **dentro de `BSPWM/`**.
- `relative_path` es la ruta relativa, por ejemplo:
  - `"bspwm/bspwmrc"`
  - `"polybar/config"`
- Sirve para que la IA o tú veáis el estado actual de una configuración antes de modificarla.

### 5.3. `replace_in_file(relative_path, search, replace, count=None)`

- Reemplazo de texto genérico en un archivo.
- Parámetros:
  - `relative_path`: ruta relativa en `BSPWM/`.
  - `search`: texto a buscar.
  - `replace`: texto nuevo.
  - `count`: número máximo de reemplazos (None = todos).
- Devuelve un resumen con cuántos reemplazos se han hecho.

Útil para cambios simples tipo: cambiar una fuente, un nombre de monitor, etc.

### 5.4. `set_bspc_config(option: str, value: str)`

- Especializada para `BSPWM/bspwm/bspwmrc`.
- Busca líneas del estilo:

```bash
bspc config <option> <valor>
```

- Si encuentra una línea con esa `option`, actualiza el valor.
- Si no existe, añade una nueva línea al final del archivo.
- Respeta líneas comentadas que empiezan por `#`.

Ejemplos de uso (a nivel lógico, desde la IA):

- "Pon el border_width de BSPWM a 3 píxeles" →
  - Llamada esperada: `set_bspc_config(option="border_width", value="3")`
- "Cambia el gap entre ventanas a 8" →
  - `set_bspc_config(option="window_gap", value="8")`

### 5.5. `get_bspwm_options()`

- Devuelve un resumen de **todas las opciones `bspc config`** definidas en `bspwm/bspwmrc`.
- Resultado aproximado:

```json
{
  "path": "bspwm/bspwmrc",
  "options": {
    "border_width": {"value": "2", "line": 10, "raw": "bspc config border_width 2"},
    "window_gap": {"value": "8", "line": 11, "raw": "bspc config window_gap 8"}
  }
}
```

Útil para ver de un vistazo cómo tienes configurado BSPWM antes de cambiar nada.

### 5.6. `set_polybar_key(relative_path: str, key: str, value: str)`

- Pensada para archivos estilo INI de Polybar.
- Busca líneas de la forma `key = value` (ignorando espacios y comentarios).
- Si encuentra la clave, actualiza el valor.
- Si no existe, añade `key = value` al final del archivo.

Ejemplos lógicos de uso:

- "Pon el background de Polybar a #222" →
  - `set_polybar_key("polybar/colors.ini", "background", "#222")`
- "Cambia el color de texto a #FFFFFF" →
  - `set_polybar_key("polybar/colors.ini", "foreground", "#FFFFFF")`

### 5.7. `list_editable_items(relative_path: str)`

- Dado un archivo de configuración, devuelve una lista de **items editables** detectados:
  - En `bspwm/bspwmrc`: todas las líneas `bspc config <opcion> <valor>`.
  - En archivos tipo INI (Polybar, kitty, picom…): todas las líneas `clave = valor`.
- Cada item incluye:
  - `kind` (`"bspc_config"` o `"key_value"`).
  - `option`/`key`, `value` actual.
  - `line` y `raw` (texto completo de la línea).

Es ideal para usar con Inspector MCP: eliges un archivo de `list_bspwm_files`, llamas a `list_editable_items` y ves qué parámetros concretos puedes tocar.

### 5.8. `get_ini_options(relative_path: str)`

- Similar a `list_editable_items`, pero agrupa los parámetros de archivos tipo INI por **secciones**.
- Útil para `polybar/colors.ini`, `polybar/config`, `kitty/kitty.conf`, `picom/picom.conf`, etc.
- Resultado aproximado:

```json
{
  "path": "polybar/colors.ini",
  "sections": {
    "global": {
      "background": {"value": "#000000", "line": 5, "raw": "background = #000000"},
      "foreground": {"value": "#ffffff", "line": 6, "raw": "foreground = #ffffff"}
    },
    "bar/main": {
      "width": {"value": "100%", "line": 20, "raw": "width = 100%"}
    }
  }
}
```

Con esto puedes construir una UI que deje elegir sección, clave y nuevo valor de forma cómoda.

---

## 6. Persistencia de datos

La persistencia está resuelta escribiendo **directamente en los archivos reales** dentro de `BSPWM/`:

- Cada tool que modifica algo (`replace_in_file`, `set_bspc_config`, `set_polybar_key`) escribe el archivo de vuelta a disco.
- No hay base de datos aparte: tus configs siguen siendo los mismos archivos de siempre.
- Puedes abrir `BSPWM/bspwm/bspwmrc`, `BSPWM/polybar/config`, etc., y ver los cambios inmediatamente.

---

## 7. Flujo de uso típico (interactivo con un cliente MCP)

1. Desde tu cliente MCP (por ejemplo, Claude con este servidor instalado), haces una petición en lenguaje natural, por ejemplo:
   - "Cambia el border_width de BSPWM a 2 píxeles y aumenta el gap de ventanas a 8. Muéstrame el diff resultante."
2. El modelo:
   - Llama a `read_config("bspwm/bspwmrc")` para ver el estado actual.
   - Llama a `set_bspc_config("border_width", "2")`.
   - Llama a `set_bspc_config("window_gap", "8")`.
   - Opcionalmente vuelve a llamar a `read_config` para comparar y generarte un diff textual.
3. El resultado es que tu archivo `BSPWM/bspwm/bspwmrc` queda modificado en disco.

Otro ejemplo con Polybar:

1. "Oscurece el tema de Polybar cambiando el background a #111 y el foreground a #eee en colors.ini".
2. El modelo puede:
   - Llamar a `set_polybar_key("polybar/colors.ini", "background", "#111")`.
   - Llamar a `set_polybar_key("polybar/colors.ini", "foreground", "#eee")`.

---

## 8. Flujo de uso típico (con el cliente IA `client_ai.py`)

1. Arrancas el servidor MCP (por ejemplo con `uv run --with mcp mcp dev server.py`).
2. En otra terminal, ejecutas el cliente IA:
  - `uv run client_ai.py`
3. El cliente se conecta al servidor MCP y te mostrará:
  - Los archivos disponibles (`list_bspwm_files`).
  - Ejemplos de peticiones en español.
4. Escribes cosas como:
  - "Pon el borde de las ventanas a 3 píxeles".
  - "Reduce el gap a 5".
  - "Oscurece la barra cambiando el background a #111".
5. El cliente IA:
  - Llama al modelo de OpenAI (usando un prompt que le explica cómo generar un **plan JSON**).
  - Imprime el plan por pantalla para que lo veas.
  - Aplica el plan llamando a las tools MCP necesarias (`set_bspc_config`, `set_polybar_key`, etc.).
6. Los cambios quedan guardados en tus archivos de `BSPWM/`.

---

## 9. Seguridad y límites

- Todas las rutas se resuelven **dentro de la carpeta `BSPWM/`**.
- Si alguien intenta pasar una ruta tipo `../../etc/passwd`, el servidor lanza un error.
- Esto mantiene el alcance del servidor MCP limitado sólo a los archivos de configuración de tu entorno BSPWM dentro del repo.

---

## 10. Cómo extender la lógica

Si quieres añadir más herramientas específicas, por ejemplo:

- Cambiar valores concretos en `picom/picom.conf`.
- Modificar atajos en `sxhkd/sxhkdrc`.
- Ajustar opciones de `kitty.conf`.

Puedes seguir los mismos patrones usados en `set_bspc_config` y `set_polybar_key`:

- Leer el archivo con `_resolve_config_path`.
- Parsear líneas según el formato del archivo.
- Modificar sólo lo necesario.
- Escribir el archivo de vuelta con `write_text`.

Esto mantiene la edición **determinista y segura**, y deja al modelo el trabajo de decidir **qué herramienta llamar** según lo que tú pidas en lenguaje natural.

---

## 11. Resumen rápido

- Este proyecto es un **servidor MCP en Python** para tus configs de BSPWM.
- Expone herramientas para **listar, leer y modificar** archivos dentro de `BSPWM/`.
- Los cambios se guardan directamente en los archivos → **persistencia automática**.
- Pensado para trabajar de forma **interactiva**: tú describes el cambio, el modelo (o el cliente IA) llama a las tools adecuadas.

Con esto, este MCP se convierte en una especie de **panel de control inteligente** para tu entorno BSPWM + Polybar + kitty + picom, accesible tanto desde clientes MCP como desde el asistente en español de `client_ai.py`.

Si quieres, el siguiente paso puede ser añadir herramientas más específicas (por ejemplo, toggles para opacidad de picom, atajos concretos de sxhkd, etc.) y las implementamos también aquí.
