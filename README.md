
## Bspwm

La estructura general es la siguiente:

```text
bspwm/        configuración principal del gestor de ventanas (bspwmrc)
sxhkd/        atajos de teclado globales
polybar/      barra de estado, colores, módulos y scripts auxiliares
picom/        compositor y reglas de transparencia/sombras
kitty/        configuración del emulador de terminal
gtk-3.0/      ajustes de tema GTK
qt5ct/        ajustes de tema Qt5
qt6ct/        ajustes de tema Qt6
bin/          scripts usados por bspwm y polybar
```

Cada subdirectorio contiene un conjunto de ficheros de texto simples que se pueden versionar sin problemas.

---

## Relación con MCP

En la carpeta hermana `bspwm-mcp/` se define un **servidor MCP** (Model Context Protocol) que utiliza exactamente esta estructura de directorios como fuente predeterminada para la configuración del entorno.

Este mcp es un protocolo que permite a clientes compatible interactuar con herramientas como:

- Listar los archivos de configuración relevantes de este directorio.
- Leer el contenido de ficheros como `bspwmrc`, `polybar/config`, `picom/picom.conf`, etc.
- Analizar y extraer opciones editables (por ejemplo, líneas `bspc config` en `bspwmrc` o claves `key = value` en archivos de Polybar).
- Modificar de forma controlada determinados parámetros de configuración, escribiendo siempre dentro de este árbol `BSPWM/`.

De este modo, cualquier cliente MCP puede inspeccionar y ajustar la configuración de bspwm y de los componentes asociados sin acceso directo al sistema de archivos, sino a través de una capa intermedia que limita y documenta claramente qué se puede hacer sobre estos dotfiles.
