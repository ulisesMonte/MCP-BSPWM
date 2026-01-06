# BSPWM

Este directorio contiene mi configuración personal del gestor de ventanas **bspwm** y de los componentes que lo acompañan en el día a día. El objetivo es mantener un entorno minimalista, rápido y orientado al uso intensivo del teclado, sin renunciar a cierta estética y a una organización clara de los ficheros.

---

## Qué es bspwm

**bspwm** (Binary Space Partitioning Window Manager) es un gestor de ventanas en mosaico para X11. En lugar de apilar ventanas de forma libre, organiza el espacio de pantalla dividiéndolo en regiones (tiles) según reglas predecibles. El control se apoya casi por completo en atajos de teclado, lo que lo hace especialmente cómodo para trabajar con varias aplicaciones en paralelo y aprovechar bien el espacio en pantalla.

En este entorno, bspwm no funciona de forma aislada, sino que se integra con otros componentes ligeros que completan la experiencia gráfica:

- `sxhkd` para los atajos de teclado.
- `polybar` para la barra de estado.
- `picom` como compositor (sombras, transparencias, animaciones sutiles).
- `kitty` como emulador de terminal.
- Ajustes de GTK y Qt para unificar el aspecto de las aplicaciones.

El comportamiento general del sistema se define principalmente en `bspwmrc` y en los distintos archivos de configuración repartidos por este directorio.

---

## Contenido principal

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

En la carpeta hermana `bspwm-mcp/` se define un **servidor MCP** (Model Context Protocol) que utiliza exactamente esta estructura de directorios como fuente de verdad para la configuración del entorno.

MCP es un protocolo que permite a clientes compatibles (por ejemplo, asistentes o herramientas de inspección) interactuar con recursos externos a través de herramientas bien definidas. En este caso concreto, el servidor MCP expone funciones para:

- Listar los archivos de configuración relevantes de este directorio.
- Leer el contenido de ficheros como `bspwmrc`, `polybar/config`, `picom/picom.conf`, etc.
- Analizar y extraer opciones editables (por ejemplo, líneas `bspc config` en `bspwmrc` o claves `key = value` en archivos de Polybar).
- Modificar de forma controlada determinados parámetros de configuración, escribiendo siempre dentro de este árbol `BSPWM/`.

De este modo, cualquier cliente MCP puede inspeccionar y ajustar la configuración de bspwm y de los componentes asociados sin acceso directo al sistema de archivos, sino a través de una capa intermedia que limita y documenta claramente qué se puede hacer sobre estos dotfiles.
