from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI
from dotenv import load_dotenv



ROOT = Path(__file__).resolve().parent
SERVER_PATH = ROOT / "server.py"
PROMPT_PATH = ROOT / "prompt.txt"

load_dotenv(ROOT / ".env")


def build_instruction_prompt() -> str:

    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de prompt en: {PROMPT_PATH}\n"
            "Crea el archivo 'prompt.txt' en la carpeta bspwm-mcp con las "
            "instrucciones para la IA."
        )
    
    return PROMPT_PATH.read_text(encoding="utf-8")


async def plan_with_ai(client: OpenAI, text: str) -> Dict[str, Any]:

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": build_instruction_prompt(),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return json.loads(content)


def format_result(result: Any) -> str:
    if isinstance(result, dict):
        return json.dumps(result, indent=2, ensure_ascii=False)
    return str(result)


async def apply_plan(session: ClientSession, plan: Dict[str, Any]) -> None:

    actions = plan.get("actions") or []

    if not isinstance(actions, list):
        print(" Plan IA sin 'actions' válido, no se aplica nada.")
        return

    for idx, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            continue

        action_type = action.get("type")
        print(f"\n{'='*60}")
        print(f"Acción {idx}/{len(actions)}: {action_type}")
        print(f"{'='*60}")

        if action_type == "list_files":
            print(" Listando archivos de configuración disponibles...\n")
            result = await session.call_tool("list_bspwm_files", {})
            
            # Formateo bonito para list_files
            if isinstance(result, dict):
                for category, files in result.items():
                    print(f"  🔹 {category}:")
                    for file in files:
                        print(f"      • {file}")
            else:
                print(format_result(result))

        elif action_type == "show_bspwm_options":
            print("🔧 Mostrando opciones actuales de BSPWM...\n")
            result = await session.call_tool("get_bspwm_options", {})
            
            # Formateo para opciones bspwm
            if isinstance(result, dict) and "options" in result:
                options = result["options"]
                print(f"Archivo: {result.get('path', 'bspwm/bspwmrc')}\n")
                if options:
                    max_len = max(len(opt) for opt in options.keys())
                    for option, info in options.items():
                        value = info.get("value", "")
                        line = info.get("line", "?")
                        print(f"  {option:<{max_len}} = {value:<20} (línea {line})")
                else:
                    print("  (No hay opciones bspc config definidas)")
            else:
                print(format_result(result))

        elif action_type == "show_ini_options":
            file = action.get("file")
            if not file:
                print("Falta el parámetro 'file'")
                continue
            
            print(f" Mostrando opciones editables de: {file}\n")
            result = await session.call_tool(
                "get_ini_options",
                {"relative_path": file},
            )
            
            # Formateo bonito para archivos INI
            if isinstance(result, dict) and "sections" in result:
                sections = result["sections"]
                for section_name, keys in sections.items():
                    print(f"  [{section_name}]")
                    if keys:
                        max_len = max(len(k) for k in keys.keys())
                        for key, info in keys.items():
                            value = info.get("value", "")
                            line = info.get("line", "?")
                            print(f"    {key:<{max_len}} = {value:<30} (línea {line})")
                    else:
                        print("    (vacía)")
                    print()
            else:
                print(format_result(result))

        elif action_type == "set_bspwm_option":
            option = action.get("option")
            value = action.get("value")
            if not (option and value is not None):
                print("⚠ Faltan parámetros 'option' o 'value'")
                continue
            
            value_str = str(value)
            print(f" Cambiando BSPWM: {option} = {value_str}")
            
            result = await session.call_tool(
                "set_bspc_config",
                {"option": option, "value": value_str},
            )
            
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                if status == "updated":
                    print(f" Opción '{option}' actualizada correctamente")
                elif status == "added":
                    print(f" Opción '{option}' añadida al archivo")
                else:
                    print(f" Estado: {status}")
            else:
                print(format_result(result))

        elif action_type == "set_ini_key":
            file = action.get("file")
            key = action.get("key")
            value = action.get("value")
            if not (file and key and value is not None):
                print("Faltan parámetros 'file', 'key' o 'value'")
                continue
            
            value_str = str(value)
            print(f"  Cambiando {file}: {key} = {value_str}")
            
            result = await session.call_tool(
                "set_polybar_key",
                {"relative_path": file, "key": key, "value": value_str},
            )
            
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                if status == "updated":
                    print(f"Clave '{key}' actualizada correctamente")
                elif status == "added":
                    print(f"Clave '{key}' añadida al archivo")
                else:
                    print(f" Estado: {status}")
            else:
                print(format_result(result))

        else:
            # Acción desconocida; la ignoramos para no romper el flujo.
            print(f" Acción desconocida: {action_type!r}")


async def main_async() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            " Debes definir la variable de entorno OPENAI_API_KEY con tu "
            "API key de OpenAI."
        )

    client = OpenAI(api_key=api_key)

    server_params = StdioServerParameters(
        command=str(Path(os.sys.executable)),
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "="*60)
            print(" Cliente IA para BSPWM MCP")
            print("="*60)
            print("\n Conectado al servidor MCP. Escribe peticiones en español.\n")
            print("Ejemplos de peticiones:")
            print("  • 'lista los archivos disponibles'")
            print("  • 'mostrame las opciones de bspwm'")
            print("  • 'mostrame las opciones editables de polybar/colors.ini'")
            print("  • 'pon el borde de las ventanas a 3 píxeles'")
            print("  • 'cambia el background de polybar/colors.ini a #222222'")
            print("  • 'reduce el gap entre ventanas a 5'")
            print("\nEscribe 'salir', 'exit' o pulsa Ctrl+C para terminar.\n")

            while True:
                try:
                    text = input(" bspwm-ia> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n\n ¡Hasta luego!")
                    break

                if not text:
                    continue
                if text.lower() in {"salir", "exit", "quit"}:
                    print("\n ¡Hasta luego!")
                    break

                try:
                    print("\n Analizando tu petición con IA...")
                    plan = await plan_with_ai(client, text)
                    
                    print("\n Plan generado por la IA:")
                    print(json.dumps(plan, indent=2, ensure_ascii=False))
                    
                    await apply_plan(session, plan)
                    
                    print("\n Plan ejecutado correctamente.\n")
                    
                except Exception as exc:
                    print(f"\n Error: {exc}\n")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
