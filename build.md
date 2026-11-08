# Build – Robotszimulátor (MineScript IDE)

## Platform és eszközök

| | Verzió |
| --- | --- |
| Operációs rendszer | Windows 11 Home (10.0.26200), x64 |
| Python | 3.15.0 |
| PyInstaller | 6.22.3 (pyinstaller-hooks-contrib 2026.9) |
| Node.js | 24.13.1 |
| pnpm | 12.16.1 |

Python-csomagok: lásd `requirements.txt` (Flask 3.1.3, pywebview 6.2.1, PyQt6 6.12.0 + PyQt6-WebEngine 6.140.0 stb.).
Frontend: React 19, Vite 8, Tailwind CSS 4 (lásd `frontend/package.json` és `frontend/pnpm-lock.yaml`).

## Felépítés

- `core/` – a MineScript nyelv motorja Pythonban: beolvasás, parser, interpreter, térkép.
- `server.py` – a belépési pont. Flask API a core körül; grafikus módban a felületet
  pywebview-val, a Python-alkalmazáson belüli beágyazott webnézetben jeleníti meg
  (külső böngészőt nem indít). `-q` kapcsolóval csendes módban fut.
- `frontend/` – a felület (React). A buildelt változat (`frontend/dist`) bekerül az exe-be.

## Build lépései (PowerShell, a projekt gyökerében)

1. Frontend:

   ```powershell
   cd frontend
   pnpm install --frozen-lockfile
   pnpm build
   cd ..
   ```

2. Python-környezet:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt pyinstaller==6.22.3
   ```

3. Exe készítése:

   ```powershell
   pyinstaller --noconfirm --clean --onedir --name robot --contents-directory robot_lib `
     --distpath build/dist --workpath build/work `
     --add-data "frontend/dist;frontend/dist" server.py
   ```

   (Ugyanezt rögzíti a `robot.spec` is: `pyinstaller --noconfirm --clean robot.spec`.)

4. Az eredmény áthelyezése a projekt gyökerébe:

   ```powershell
   Move-Item build\dist\robot\robot.exe .
   Move-Item build\dist\robot\robot_lib .
   ```

A `robot.exe` mellett mindig ott kell lennie a `robot_lib` mappának.

## Futtatás

```
robot.exe input_001.txt output_001.txt        (grafikus felület)
robot.exe -q input_001.txt output_001.txt     (csendes mód)
run_all.bat [bemeneti mappa] [kimeneti mappa] (minden input_XXX.txt -> output_XXX.txt)
```

Pythonból, build nélkül: `python server.py [-q] input.txt output.txt`.

## Megjegyzések

- **Mappás (onedir) build.** Egyfájlos (`--onefile`) exe-nél minden indításkor ki kell
  csomagolni a ~210 MB-ot (a Qt WebEngine miatt), ez indításonként ~8,5 s volt. A mappás
  változat ~0,4 s alatt indul; 210 bemenet `run_all.bat`-tal ~90 s alatt fut le.
- **Grafikus motor.** Ha a gépen van Microsoft Edge WebView2 Runtime (Windows 11-en
  alapból van), a pywebview EdgeChromium motort használ. Ha nincs, a beépített Qt
  (PyQt6 WebEngine) motorra vált. A Qt a `ROBOT_GUI=qt` környezeti változóval kényszeríthető.
- **Szabad port.** A beágyazott szerver az operációs rendszertől kér szabad portot
  (`127.0.0.1`), így nem ütközik más programmal.
