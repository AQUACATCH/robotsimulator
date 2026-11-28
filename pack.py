"""A beadandó project.zip elkészítése: forráskód és dokumentáció, futtatható változat nélkül.

Használat (a programkönyvtár gyökerében):  python pack.py
"""
import subprocess
import sys
import zipfile
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "project.zip"
DOCS = ["build.md", "kiterjesztes.pdf", "megrendeloi_funkcio.pdf", "felhasznaloi_kezikonyv.pdf"]
# Ami nem a programkönyvtár része: tesztcsomagok, futási naplók, a megrendelői válaszok.
EXCLUDE = ["*.zip", "output*.txt", "out.txt", "valaszok_*.md"]
# Ha nincs git, ezeket a mappákat hagyjuk ki (a .gitignore szerint is kimaradnak).
SKIP_DIRS = {".git", ".venv", "node_modules", "build", "dist", "robot_lib", "__pycache__", "HIBAK", ".claude"}


def candidate_files():
    try:
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        return [Path(name) for name in listed]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for path in ROOT.rglob("*"):
            rel = path.relative_to(ROOT)
            if path.is_file() and not SKIP_DIRS.intersection(rel.parts) and rel.name != "robot.exe":
                files.append(rel)
        return files


def main():
    files = {rel for rel in candidate_files()
             if (ROOT / rel).is_file() and not any(fnmatch(rel.name, pattern) for pattern in EXCLUDE)}
    files.update(Path(doc) for doc in DOCS if (ROOT / doc).is_file())
    missing = [doc for doc in DOCS if not (ROOT / doc).is_file()]

    with zipfile.ZipFile(TARGET, "w", zipfile.ZIP_DEFLATED) as archive:
        for rel in sorted(files):
            archive.write(ROOT / rel, rel.as_posix())

    size = TARGET.stat().st_size / 1024
    print(f"{TARGET.name}: {len(files)} fájl, {size:.0f} KB")
    if missing:
        print("FIGYELEM, hiányzik: " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
