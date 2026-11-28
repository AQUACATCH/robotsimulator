# Build – Robotszimulátor (MineScript IDE), II. forduló

## Platform és fejlesztői környezet

| | Verzió |
| --- | --- |
| Operációs rendszer | Windows 11 Home 10.0.26200, 64 bites |
| Programozási nyelv | Python 3.15.0 (core, interpreter, szerver) |
| Felület | React 19, Vite 8, Tailwind CSS 4; Node.js 24.13.1, pnpm 12.16.1 |
| Beágyazott webnézet | pywebview 6.2.1: Microsoft Edge WebView2, tartalékként Qt WebEngine (PyQt6 6.12.0) |
| Futtatható változat | PyInstaller 6.22.3 |

A Python-csomagok pontos verziói a `requirements.txt` (futáshoz) és a `requirements-build.txt`
(fordításhoz) fájlban, a JavaScript-csomagoké a `frontend/pnpm-lock.yaml` fájlban vannak.

## Tesztkonfiguráció

- ASUS TUF Gaming F15 (FX506LU) laptop: Intel Core i7-10870H, 16 GB RAM, SSD
- Windows 11 Home 10.0.26200, Microsoft Edge WebView2 Runtime 158.0.4370.45
- A felületet GPU nélküli, szoftveres megjelenítéssel is kipróbáltuk (`--disable-gpu`): egy 20×30-as
  bányán, a leggyorsabb futtatás közben is 60 fps volt, a leghosszabb képkocka 17 ms.
- A build lépéseit egy üres mappába kicsomagolt `project.zip`-ből is végigcsináltuk; a lefordított
  program a 256 I. fordulós tesztbemenetre bájtra azonos naplót ad.

## Előfeltételek egy üres gépen

1. Windows 10 vagy 11, 64 bites.
2. **Python 3.15.0** (https://www.python.org/downloads/, „Windows installer (64-bit)”).
   Telepítéskor maradjon bekapcsolva a „py launcher”, és pipáljuk be az „Add python.exe to PATH” lehetőséget.
3. **Node.js 24.13.1** (https://nodejs.org/, Windows Installer, x64).
4. **pnpm 12.16.1**, a Node.js telepítése után egy új PowerShell-ablakban:

   ```powershell
   npm install -g pnpm@12.16.1
   ```

5. Internetkapcsolat a fordításhoz (a csomagok letöltéséhez). A lefordított program internet nélkül fut.

Mást nem kell telepíteni. A Microsoft Edge WebView2 Runtime Windows 11-en a rendszer része; ha egy gépen
hiányzik, a program a beépített Qt-motorral jeleníti meg ugyanazt a felületet.

## Fordítás

PowerShellben, a kicsomagolt programkönyvtár gyökerében (ahol ez a fájl van):

1. Felület:

   ```powershell
   cd frontend
   pnpm install --frozen-lockfile
   pnpm build
   cd ..
   ```

2. Python-környezet:

   ```powershell
   py -3.15 -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
   ```

3. Futtatható változat:

   ```powershell
   .venv\Scripts\pyinstaller.exe --noconfirm --clean robot.spec
   ```

Az eredmény a `dist\robot` mappa: benne a `robot.exe` és mellette a `robot_lib` mappa. A kettőt csak
együtt lehet áthelyezni.

## Indítás

```powershell
dist\robot\robot.exe
```

(vagy dupla kattintás a `robot.exe`-n). A program üresen indul: a „Bemenet megnyitása…” gombbal kell
kiválasztani a bemeneti fájlt. A napló alapértelmezés szerint a bemenet mellé kerül `output.txt` néven;
a „Napló helye…” gombbal bármikor máshová tehető.

Elhagyható paraméterek (teszteléshez):

- `robot.exe bemenet.txt naplo.txt`: induláskor betölti a bemenetet.
- `robot.exe -q bemenet.txt naplo.txt`: csendes mód ablak nélkül, az I. fordulós tesztekhez.
- `run_all.bat mappa`: a mappa összes `input_XXX.txt` fájlját csendes módban futtatja.

Fejlesztés közben fordítás nélkül is indítható (előtte a felületet buildelni kell):
`.venv\Scripts\python.exe server.py`.

## Megjegyzések

- **Mappás build.** Egyfájlos exe-nél minden indításkor ki kellene csomagolni a kb. 210 MB-os
  Qt WebEngine-t, ami indításonként 8–9 másodperc volt. A mappás változat ablaka kb. 2,5 s alatt megjelenik.
- **Méret.** Fordítás után a programkönyvtár kb. 1,2 GB: ebből a `.venv` 0,6 GB, a `dist` 0,5 GB,
  a `frontend\node_modules` 0,1 GB.
- **Beágyazott felület.** A felület a Python-programon belül, beágyazott webnézetben jelenik meg, külön
  böngészőt nem indít. A fájlválasztók is a program saját ablakai.
- **Szabad port.** A beágyazott szerver az operációs rendszertől kér szabad portot a `127.0.0.1`
  címen, így nem ütközik más programmal.
