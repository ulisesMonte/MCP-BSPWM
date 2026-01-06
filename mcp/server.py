from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


# Nombre visible del servidor en el cliente MCP
mcp = FastMCP(
    name="BSPWM Config MCP",
    instructions=(
        "Servidor MCP que te permite leer y modificar archivos de "
        "configuración bajo el directorio BSPWM/ de este repositorio. "
        "Úsalo pidiéndole a la IA que cambie opciones de bspwm, polybar, etc., "
        "y ésta llamará a las herramientas expuestas aquí."
    ),
)


# Carpeta raíz donde están tus configs de BSPWM (carpeta hermana de bspwm-mcp)
CONFIG_ROOT = (Path(__file__).resolve().parents[1] / "BSPWM").resolve()


def _resolve_config_path(relative_path: str) -> Path:

    candidate = (CONFIG_ROOT / relative_path).resolve()

    # Evita irse con rutas tipo ../../etc/passwd
    if not str(candidate).startswith(str(CONFIG_ROOT)):
        raise ValueError("La ruta solicitada está fuera del directorio BSPWM/")

    if not candidate.exists():
        raise FileNotFoundError(f"No existe el archivo: {relative_path}")

    return candidate

#Lista las rutas de los archivos del bspwm
@mcp.tool()
def list_bspwm_files() -> dict[str, list[str]]:


    return {
        "bspwm": [
            "bspwm/bspwmrc",
        ],
        "polybar": [
            "polybar/config",
            "polybar/colors.ini",
            "polybar/colors_dark.ini",
            "polybar/colors_light.ini",
            "polybar/current.ini",
        ],
        "sxhkd": [
            "sxhkd/sxhkdrc",
        ],
        "picom": [
            "picom/picom.conf",
        ],
        "kitty": [
            "kitty/kitty.conf",
            "kitty/color.ini",
        ],
        "nvim": [
            "nvim/init.lua",
        ],
    }


#devuelve contenido de los archivos del bspwm
@mcp.tool()
def read_config(relative_path: str) -> str:

    path = _resolve_config_path(relative_path)
    return path.read_text(encoding="utf-8", errors="ignore")



#devuelve un resumen de opciones de bspwm confguradas
@mcp.tool()
def get_bspwm_options() -> dict[str, Any]:
   

    relative = "bspwm/bspwmrc"
    path = _resolve_config_path(relative)
    text = path.read_text(encoding="utf-8", errors="ignore")

    options: dict[str, Any] = {}
    lines = text.splitlines()

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("bspc config "):
            parts = stripped.split(maxsplit=3)
            # bspc config <opcion> <valor...>
            if len(parts) >= 3:
                option = parts[2]
                value = parts[3] if len(parts) >= 4 else ""
                options[option] = {
                    "value": value,
                    "line": idx,
                    "raw": line,
                }

    return {
        "path": relative,
        "options": options,
    }



#Devuelve un parametros de editables de un archivo INI como ficheros como los de Polybar, kitty, picom, etc
@mcp.tool()
def get_ini_options(relative_path: str) -> dict[str, Any]:
    

        path = _resolve_config_path(relative_path)
        text = path.read_text(encoding="utf-8", errors="ignore")

        sections: dict[str, dict[str, Any]] = {}
        current_section = "global"
        sections[current_section] = {}

        for idx, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()

                if not stripped or stripped.startswith("#") or stripped.startswith(";"):
                        continue

                # Secciones tipo [section]
                if stripped.startswith("[") and stripped.endswith("]"):
                        current_section = stripped[1:-1].strip() or "global"
                        if current_section not in sections:
                                sections[current_section] = {}
                        continue

                if "=" not in stripped:
                        continue

                key, value = stripped.split("=", 1)
                key = key.strip()
                value = value.strip()

                if not key:
                        continue

                sections.setdefault(current_section, {})[key] = {
                        "value": value,
                        "line": idx,
                        "raw": line,
                }

        return {
                "path": relative_path,
                "sections": sections,
        }



#Lista los items editables que detecta dentro del archivo
# Reglas sencillas:
#    - Para BSPWM (bspwm/bspwmrc):
#      * Se consideran editables las líneas tipo: `bspc config <opcion> <valor>`.
#    - Para Polybar, kitty, picom, etc. (archivos estilo INI):
#      * Se consideran editables las líneas `clave = valor` (ignorando comentarios y líneas vacías).
@mcp.tool()
def list_editable_items(relative_path: str) -> dict[str, Any]:

    path = _resolve_config_path(relative_path)
    text = path.read_text(encoding="utf-8", errors="ignore")

    items: list[dict[str, Any]] = []

    lines = text.splitlines()
    is_bspwmrc = relative_path.replace("\\", "/").endswith("bspwm/bspwmrc")

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Ignorar comentarios y líneas vacías
        if not stripped or stripped.startswith("#"):
            continue

        if is_bspwmrc and stripped.startswith("bspc config "):
            # bspc config <option> <value...>
            parts = stripped.split(maxsplit=3)
            # parts[0] = bspc, parts[1] = config, parts[2] = option, parts[3] = value
            if len(parts) >= 3:
                option = parts[2]
                value = parts[3] if len(parts) >= 4 else ""
                items.append(
                    {
                        "kind": "bspc_config",
                        "option": option,
                        "value": value,
                        "line": idx,
                        "raw": line,
                    }
                )
            continue

        # Genérico: líneas tipo key = value
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            items.append(
                {
                    "kind": "key_value",
                    "key": key.strip(),
                    "value": value.strip(),
                    "line": idx,
                    "raw": line,
                }
            )

    return {
        "path": relative_path,
        "items": items,
    }

#Reemplaza el texto en un archivo de configuracion bajo bspwm
@mcp.tool()
def replace_in_file(
    relative_path: str,
    search: str,
    replace: str,
    count: int | None = None,
) -> dict[str, Any]:


    path = _resolve_config_path(relative_path)
    original = path.read_text(encoding="utf-8", errors="ignore")

    if count is None:
        new = original.replace(search, replace)
        replacements = original.count(search)
    else:
        new = original.replace(search, replace, count)
        # Estimación simple del número de reemplazos
        before = original.count(search)
        replacements = min(before, count)

    if new == original:
        return {
            "status": "no-op",
            "replacements": 0,
            "path": relative_path,
        }

    path.write_text(new, encoding="utf-8")

    return {
        "status": "ok",
        "replacements": replacements,
        "path": relative_path,
    }

#Establece un valor a una opcion de bspwm
@mcp.tool()
def set_bspc_config(option: str, value: str) -> dict[str, str]:
 
    relative = "bspwm/bspwmrc"
    path = _resolve_config_path(relative)

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    prefix = f"bspc config {option} "
    changed = False
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Respeta comentarios que empiezan con #
        if stripped.startswith("#"):
            new_lines.append(line)
            continue

        if stripped.startswith(prefix):
            new_lines.append(f"{prefix}{value}")
            changed = True
        else:
            new_lines.append(line)

    if not changed:
        # Añadimos una línea nueva al final
        new_lines.append(f"{prefix}{value}")

    # Aseguramos newline final
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {
        "status": "updated" if changed else "added",
        "option": option,
        "value": value,
        "path": relative,
    }

#Modifica la polybar
@mcp.tool()
def set_polybar_key(
    relative_path: str,
    key: str,
    value: str,
) -> dict[str, str]:


    path = _resolve_config_path(relative_path)
    text = path.read_text(encoding="utf-8", errors="ignore")

    lines = text.splitlines()
    changed = False
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#") or not stripped:
            new_lines.append(line)
            continue

        if stripped.startswith(f"{key} =") or stripped.startswith(f"{key}="):
            new_lines.append(f"{key} = {value}")
            changed = True
        else:
            new_lines.append(line)

    if not changed:
        new_lines.append(f"{key} = {value}")

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {
        "status": "updated" if changed else "added",
        "key": key,
        "value": value,
        "path": relative_path,
    }


def main() -> None:


    mcp.run()


if __name__ == "__main__":
    main()
