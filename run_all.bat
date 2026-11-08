@echo off
setlocal EnableDelayedExpansion

rem Hasznalat: run_all.bat [bemeneti mappa] [kimeneti mappa]
rem Minden input_XXX.txt fajlra lefuttatja a robot.exe -q modjat, az eredmeny output_XXX.txt.
rem Alapertelmezes: a bemeneti mappa az aktualis mappa, a kimenet ugyanoda kerul.

set "EXE=%~dp0robot.exe"
set "IN=%~1"
if "%IN%"=="" set "IN=."
set "OUT=%~2"
if "%OUT%"=="" set "OUT=%IN%"

if not exist "%EXE%" (
  echo HIBA: nem talalom a robot.exe-t: %EXE%
  exit /b 1
)
if not exist "%IN%\input_*.txt" (
  echo HIBA: nincs input_*.txt fajl itt: %IN%
  exit /b 1
)
if not exist "%OUT%" mkdir "%OUT%"

set /a INPUTS=0
for %%F in ("%IN%\input_*.txt") do (
  set "NAME=%%~nF"
  set "OUTFILE=%OUT%\output_!NAME:input_=!.txt"
  "%EXE%" -q "%%~fF" "!OUTFILE!"
  set /a INPUTS+=1
  echo !NAME! -^> output_!NAME:input_=!.txt
)

set /a MISSING=0
set /a EMPTY=0
for %%F in ("%IN%\input_*.txt") do (
  set "NAME=%%~nF"
  set "OUTFILE=%OUT%\output_!NAME:input_=!.txt"
  if not exist "!OUTFILE!" (
    echo HIANYZIK: !OUTFILE!
    set /a MISSING+=1
  ) else (
    for %%S in ("!OUTFILE!") do if %%~zS==0 (
      echo URES: !OUTFILE!
      set /a EMPTY+=1
    )
  )
)

echo.
echo Bemenetek: !INPUTS!  Hianyzo kimenet: !MISSING!  Ures kimenet: !EMPTY!
if !MISSING! gtr 0 exit /b 2
if !EMPTY! gtr 0 exit /b 2
exit /b 0
