# Pong 

Juego de Pong para dos personas, desarrollado con Python y Pygame. El jugador
rojo juega a la izquierda y el azul a la derecha. Gana quien llegue primero a
cinco puntos.

## Requisitos

- Python 3.10 o posterior.
- `pip`, incluido normalmente con Python.
- Windows, macOS o Linux.

No necesitas instalar un reproductor de audio ni un conversor adicional: el
juego incluye las pistas y los efectos en formatos que Pygame puede reproducir.

## Instalación y ejecución en Windows

1. Instala Python desde [python.org](https://www.python.org/downloads/) si aún
   no lo tienes. Durante la instalación, activa **Add Python to PATH**.
2. Abre PowerShell o la terminal de VS Code en la carpeta del proyecto (la que
   contiene `pong.py` y `requirements.txt`).
3. Comprueba que Python esté disponible:

   ```powershell
   python --version
   ```

4. Crea un entorno virtual e instala las dependencias:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

5. Inicia el juego:

   ```powershell
   .\.venv\Scripts\python.exe pong.py
   ```

Para abrirlo más adelante, vuelve a la carpeta del proyecto y ejecuta el último
comando. No es necesario activar el entorno virtual por separado.

### macOS y Linux

Desde una terminal abierta en la carpeta del proyecto, ejecuta:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python pong.py
```

## Cómo jugar

- **Menú:** selecciona **Jugar**, **Instrucciones** o **Salir** con el mouse.
  También puedes pulsar `Enter` para jugar, `I` para abrir las instrucciones o
  `Esc` para salir.
- **Jugador rojo (izquierda):** `W` sube y `S` baja.
- **Jugador azul (derecha):** las flechas `↑` y `↓` mueven la paleta.
- **Pausa:** durante la partida, pulsa `Esc` o haz clic en **Pausa**. El menú
  de pausa permite continuar, abrir las instrucciones o regresar al menú.
- **Pantalla completa:** pulsa `F11` en cualquier momento o usa el botón del
  menú principal. Pulsa `F11` otra vez para volver al modo ventana.
- **Instrucciones:** `Enter`, `Esc` o el botón `ESC` devuelve a la pantalla
  anterior.

Antes del saque se muestra el objetivo de la partida. La pelota rebota contra
las paredes y las paletas; los sprites cambian brevemente al chocar. Al llegar
a cinco puntos, se anuncia si ganó el lado rojo o el azul y después el juego
regresa automáticamente al menú principal.

La música de Tron acompaña el menú y la de Daft Punk la partida. También hay
efectos de sonido para los rebotes y los goles.

## Estructura del proyecto

```text
pong.py                 Código del juego
requirements.txt        Dependencias de Python
README.md               Estas instrucciones
assets/
  images/               Fondos, paletas, pelota e imágenes de instrucciones
  audio/                Música y efectos usados por el juego
```

No cambies los nombres ni muevas los archivos dentro de `assets`: el juego
utiliza esas rutas para cargar las imágenes y el audio.

## Solución de problemas

- **`python` no se reconoce:** instala Python y vuelve a abrir la terminal.
  En Windows también puedes probar `py` en lugar de `python`.
- **`No module named pygame`:** instala las dependencias en el mismo Python
  desde el que ejecutas el juego:

  ```powershell
  python -m pip install -r requirements.txt
  ```

- **No se encuentra una imagen o una pista:** ejecuta `pong.py` desde la
  carpeta del proyecto y comprueba que las carpetas `assets/images` y
  `assets/audio` estén completas.
- **No se escucha el audio:** comprueba el volumen del sistema y que haya una
  salida de audio disponible.
