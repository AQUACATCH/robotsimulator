#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MineScript -q mód: pontos naplókat ellenőrző, közvetlen runScriptQ-integrációs tesztek.

Használat (a mineScriptRunner.py mellett, a core/ csomagot is tartalmazó projektben):
    python teszt_q.py
    python teszt_q.py --list
    python teszt_q.py --only 'E_BAD_ARG|isThere'
    python teszt_q.py --target /utvonal/mineScriptRunner.py --timeout 8
    python teszt_q.py --self-test       # Csak a tesztkeretrendszer próbája, NEM a roboté!

A teszt nem futtat .exe/.bat fájlt: egy külön Python-folyamatban importálja a
megadott .py modult, és az abban található runScriptQ(bemenet, kimenet) függvényt
KÖZVETLENÜL hívja. A külön folyamat szükséges a végtelen ciklusok időkorlátjához.
Minden teszt ideiglenes, szabályos bemeneti fájlt használ; az eredményt a feladat
szerinti elvárt naplóval, sorról sorra ÉS a végső újsorral együtt hasonlítja össze.

Forrás: DUSZA Árpád Országos Programozói Emlékverseny 2026/2027,
Robotszimulátor, 1-6. és 11-12. oldal (MineScript nyelv, robot API, naplózás).
"""

from __future__ import annotations

import argparse
import builtins
import difflib
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import traceback
from dataclasses import dataclass

DEFAULT_MAP = "1 1\n>"
LIMIT_MESSAGE = "INSTRUCTION_COUNT_LIMIT_EXCEEDED"


@dataclass(frozen=True)
class Case:
    name: str
    group: str
    map_text: str
    program: str
    expected: str
    require_stdout: str | None = None
    prelude: tuple[str, str] | None = None  # (térkép, program): előző futás ugyanabban a processzben


def normalize(text: str) -> str:
    """A fixture leírásának kezdő/záró újsorait eltávolítja, a behúzást megőrzi."""
    return textwrap.dedent(text).strip("\n")


def expected_lines(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def build_cases() -> list[Case]:
    result: list[Case] = []

    def add(name: str, group: str, program: str = "", expected: str = "EOR",
            map_text: str = DEFAULT_MAP, require_stdout: str | None = None,
            prelude: tuple[str, str] | None = None) -> None:
        src = normalize(program)
        exp = normalize(expected) + "\n"
        result.append(Case(name, group, normalize(map_text), src, exp, require_stdout, prelude))

    # 1. Bemenet, minimális/maximális térkép, napló-formátum, értékek.
    add("ures_program", "alap", "", "EOR")
    add("csak_szamok", "alap", "print 0\nprint 100", "1 print 0\n2 print 100\nEOR", require_stdout="100")
    add("logikai_literalok", "alap", "print true\nprint false", "1 print true\n2 print false\nEOR")
    add("ertekadas_nem_api", "alap", "set abc to 7\nprint abc\nset abc to 9\nprint abc", "1\n2 print 7\n3\n4 print 9\nEOR")
    add("valtozonev_kis_nagybetu", "alap", "set a to 5\nset A to 6\nprint a\nprint A", "1\n2\n3 print 5\n4 print 6\nEOR")
    add("egesz_es_logikai_kulonbozo_tipus", "alap", "set a to 1\nset b to true\nprint a\nprint b", "1\n2\n3 print 1\n4 print true\nEOR")
    add("szamok_tartomanyvegei", "alap", "set a to 0\nset b to 100\nprint a\nprint b", "1\n2\n3 print 0\n4 print 100\nEOR")
    add("nagy_es_negativ_kifejezeseredmeny", "alap", "set a to 100 * 100\nset b to 2 - 100\nprint a\nprint b", "1\n2\n3 print 10000\n4 print -98\nEOR")
    add("terkep_1x15", "alap", "step forward 14\nset fal to isThere 1\nprint fal", "1 step forward 14\n2 isThere 1 true\n3 print true\nEOR", "1 15\n>..............")
    rows = ["..............." for _ in range(15)]
    rows[-1] = "..............^"
    add("terkep_15x15_szelen", "alap", "step forward 14\nset fal to isThere 1\nturn by 2\nstep forward 14\nset fal to isThere 1\nprint fal", "1 step forward 14\n2 isThere 1 true\n3 turn by 2\n4 step forward 14\n5 isThere 1 true\n6 print true\nEOR", "15 15\n" + "\n".join(rows))
    add("fal_a_terkep_belsejeben", "alap", "set fal to isThere 1\nprint fal", "1 isThere 1 true\n2 print true\nEOR", "1 3\n>#.")
    add("rovid_program_utolso_soran_hiba", "alap", "print 5\nmine here", "1 print 5\n2 mine here E_NO_GOLD\nEOR")
    add("reszfeladat_peldanaplo", "alap", """\
set arany to isThere 2
set count to 0
turn by 0
print arany
if false
  print 1
else
  set x to isThere 3
print 9""", "1 isThere 2 false\n2\n3 turn by 0\n4 print false\n5\n7\n8 isThere 3 E_BAD_ARG\nEOR")

    add("ismetelt_futtatas_felulirassal", "alap", "set t to isThere 1\nprint t",
        "1 isThere 1 true\n2 print true\nEOR", "1 1\n<",
        prelude=("1 2\n>@", "step forward 1\nmine here"))

    # 2. Kifejezések és szemantika; mindegyik eredménye pontosan ellenőrzött.
    expressions = [
        ("osszeadas", "8 + 5", "13"),
        ("kivonas", "2 - 8", "-6"),
        ("szorzas", "7 * 6", "42"),
        ("kisebb_igaz", "3 < 4", "true"),
        ("kisebb_hamis", "4 < 3", "false"),
        ("kisebbegyenlo_egyenlo", "4 <= 4", "true"),
        ("kisebbegyenlo_hamis", "5 <= 4", "false"),
        ("nagyobb_igaz", "5 > 4", "true"),
        ("nagyobb_hamis", "4 > 5", "false"),
        ("nagyobbegyenlo_egyenlo", "4 >= 4", "true"),
        ("nagyobbegyenlo_hamis", "4 >= 5", "false"),
        ("egyenlo_szam_igaz", "4 = 4", "true"),
        ("egyenlo_szam_hamis", "4 = 5", "false"),
        ("nemegyenlo_szam_igaz", "4 <> 5", "true"),
        ("nemegyenlo_szam_hamis", "4 <> 4", "false"),
        ("egyenlo_bool_igaz", "true = true", "true"),
        ("egyenlo_bool_hamis", "true = false", "false"),
        ("nemegyenlo_bool_igaz", "true <> false", "true"),
        ("nemegyenlo_bool_hamis", "false <> false", "false"),
        ("and_igaz", "true and true", "true"),
        ("and_hamis", "true and false", "false"),
        ("or_igaz", "false or true", "true"),
        ("or_hamis", "false or false", "false"),
        ("not_igaz", "not false", "true"),
        ("not_hamis", "not true", "false"),
    ]
    for name, expr, val in expressions:
        add(name, "muveletek", f"set out to {expr}\nprint out", f"1\n2 print {val}\nEOR")
    add("valtozok_az_operandusok", "muveletek", "set a to 7\nset b to 8\nset c to a * b\nprint c", "1\n2\n3\n4 print 56\nEOR")
    add("ertekadas_sajat_valtozobol", "muveletek", "set a to 1\nset a to a + 1\nprint a", "1\n2\n3 print 2\nEOR")
    add("bool_valtozok_logikai_muvelettel", "muveletek", "set a to false\nset b to true\nset c to a or b\nset d to not c\nprint d", "1\n2\n3\n4\n5 print false\nEOR")

    # 3. Feltételes szerkezetek; végrehajtott sorok és kihagyott ágak.
    add("if_igaz", "vezerles", "if true\n  print 1\nprint 2", "1\n2 print 1\n3 print 2\nEOR")
    add("if_hamis", "vezerles", "if false\n  print 1\nprint 2", "1\n3 print 2\nEOR")
    add("if_else_igaz", "vezerles", "if true\n  print 1\nelse\n  print 2\nprint 3", "1\n2 print 1\n5 print 3\nEOR")
    add("if_else_hamis", "vezerles", "if false\n  print 1\nelse\n  print 2\nprint 3", "1\n3\n4 print 2\n5 print 3\nEOR")
    add("if_feltetel_valtozo", "vezerles", "set f to true\nif f\n  print 7", "1\n2\n3 print 7\nEOR")
    add("if_feltetel_erteke_modosul", "vezerles", "set f to true\nif f\n  set f to false\nif f\n  print 7\nelse\n  print 8", "1\n2\n3\n4\n6\n7 print 8\nEOR")
    add("beagyazott_if_kulso_else", "vezerles", "set a to false\nif a\n  if true\n    print 1\nelse\n  print 2\nprint 3", "1\n2\n5\n6 print 2\n7 print 3\nEOR")
    add("kulonbozo_behuzasok", "vezerles", "if true\n print 1\n if false\n     print 2\n else\n     print 3\nprint 4", "1\n2 print 1\n3\n5\n6 print 3\n7 print 4\nEOR")
    add("while_egyszer_sem", "vezerles", "while false\n  print 2\nprint 3", "1\n3 print 3\nEOR")
    add("while_haromszor", "vezerles", "set c to 0\nset go to true\nwhile go\n  set c to c + 1\n  print c\n  set go to c < 3\nprint c", "1\n2\n3\n4\n5 print 1\n6\n3\n4\n5 print 2\n6\n3\n4\n5 print 3\n6\n3\n7 print 3\nEOR")
    add("harmas_vezerles_beagyazas", "vezerles", "set go to true\nif true\n  while go\n    if go\n      print 1\n      set go to false\nprint 2", "1\n2\n3\n4\n5 print 1\n6\n3\n7 print 2\nEOR")
    add("while_belep_felteteles_agon", "vezerles", "set go to true\nwhile go\n  if false\n    print 5\n  else\n    print 6\n  set go to false\nprint 7", "1\n2\n3\n5\n6 print 6\n7\n2\n8 print 7\nEOR")

    # 4. Robot API: paraméterek, irányok, arany, fal, térképszél.
    add("isThere_ures", "robot", "set x to isThere 0\nprint x", "1 isThere 0 true\n2 print true\nEOR", "1 2\n>.")
    add("isThere_fal", "robot", "set x to isThere 1\nprint x", "1 isThere 1 true\n2 print true\nEOR", "1 2\n>#")
    add("isThere_arany", "robot", "set x to isThere 2\nprint x", "1 isThere 2 true\n2 print true\nEOR", "1 2\n>@")
    add("isThere_ures_elott_arany", "robot", "set x to isThere 0\nprint x", "1 isThere 0 false\n2 print false\nEOR", "1 2\n>@")
    add("isThere_fal_elott_ures", "robot", "set x to isThere 1\nprint x", "1 isThere 1 false\n2 print false\nEOR", "1 2\n>.")
    add("isThere_arany_elott_fal", "robot", "set x to isThere 2\nprint x", "1 isThere 2 false\n2 print false\nEOR", "1 2\n>#")
    for orientation in (">", "<", "^", "v"):
        for what in (0, 1, 2):
            add(f"terkep_szele_{orientation}_{what}", "robot",
                f"set x to isThere {what}",
                f"1 isThere {what} {'true' if what == 1 else 'false'}\nEOR",
                f"1 1\n{orientation}")
    # A négy irányban levő arany érzékelése középről.
    for orientation, dr, dc, label in ((">", 0, 1, "kelet"), ("<", 0, -1, "nyugat"),
                                         ("^", -1, 0, "eszak"), ("v", 1, 0, "del")):
        grid = [list("..."), list("..."), list("...")]
        grid[1][1] = orientation
        grid[1 + dr][1 + dc] = "@"
        add(f"arany_irany_{label}", "robot", "set x to isThere 2\nprint x",
            "1 isThere 2 true\n2 print true\nEOR", "3 3\n" + "\n".join("".join(row) for row in grid))
    add("step_nulla", "robot", "step forward 0\nset x to isThere 2\nprint x", "1 step forward 0\n2 isThere 2 true\n3 print true\nEOR", "1 2\n>@")
    add("step_egy", "robot", "step forward 1\nset x to isThere 0\nprint x", "1 step forward 1\n2 isThere 0 true\n3 print true\nEOR", "1 3\n>..")
    add("step_tobb_mezon", "robot", "step forward 3\nset x to isThere 1\nprint x", "1 step forward 3\n2 isThere 1 true\n3 print true\nEOR", "1 4\n>...")
    add("aranyat_nem_banyassza_lepessel", "robot", "step forward 2\nturn by 2\nset x to isThere 2\nprint x", "1 step forward 2\n2 turn by 2\n3 isThere 2 true\n4 print true\nEOR", "1 3\n>@.")
    add("turn_nulla", "robot", "turn by 0\nset x to isThere 2\nprint x", "1 turn by 0\n2 isThere 2 true\n3 print true\nEOR", "1 2\n>@")
    add("turn_balra_egy", "robot", "turn by 1\nset x to isThere 2\nprint x", "1 turn by 1\n2 isThere 2 true\n3 print true\nEOR", "2 2\n@.\n>.")
    add("turn_ketto", "robot", "turn by 2\nset x to isThere 2\nprint x", "1 turn by 2\n2 isThere 2 true\n3 print true\nEOR", "1 2\n@>")
    add("turn_harom", "robot", "turn by 3\nset x to isThere 2\nprint x", "1 turn by 3\n2 isThere 2 true\n3 print true\nEOR", "2 2\n>.\n@.")
    add("turn_negyteljes", "robot", "turn by 4\nset x to isThere 2", "1 turn by 4\n2 isThere 2 true\nEOR", "1 2\n>@")
    add("turn_ot", "robot", "turn by 5\nset x to isThere 2", "1 turn by 5\n2 isThere 2 true\nEOR", "2 2\n@.\n>.")
    add("turn_szaz", "robot", "turn by 100\nset x to isThere 2", "1 turn by 100\n2 isThere 2 true\nEOR", "1 2\n>@")
    add("turn_valtozo", "robot", "set n to 1\nturn by n\nset x to isThere 2", "1\n2 turn by 1\n3 isThere 2 true\nEOR", "2 2\n@.\n>.")
    add("step_valtozo", "robot", "set n to 1\nstep forward n\nset x to isThere 1", "1\n2 step forward 1\n3 isThere 1 true\nEOR", "1 2\n>.")
    add("isThere_valtozo", "robot", "set n to 2\nset x to isThere n", "1\n2 isThere 2 true\nEOR", "1 2\n>@")
    add("mine_siker", "robot", "step forward 1\nmine here\nprint 5", "1 step forward 1\n2 mine here\n3 print 5\nEOR", "1 2\n>@")
    add("mine_arany_eltunik", "robot", "step forward 1\nmine here\nstep forward 1\nturn by 2\nset empty to isThere 0\nset gold to isThere 2\nprint empty\nprint gold", "1 step forward 1\n2 mine here\n3 step forward 1\n4 turn by 2\n5 isThere 0 true\n6 isThere 2 false\n7 print true\n8 print false\nEOR", "1 3\n>@.")
    add("mine_masodszor_hiba", "robot", "step forward 1\nmine here\nmine here", "1 step forward 1\n2 mine here\n3 mine here E_NO_GOLD\nEOR", "1 2\n>@")
    add("falnak_lepes", "robot", "step forward 1", "1 step forward 1 E_BEDROCK_HIT\nEOR", "1 2\n>#")
    add("felig_mozgas_falnak", "robot", "step forward 3", "1 step forward 3 E_BEDROCK_HIT\nEOR", "1 4\n>.#.")
    add("terkeprol_lepes", "robot", "step forward 1", "1 step forward 1 E_BEDROCK_HIT\nEOR")
    add("tobb_lepes_terkeprol", "robot", "step forward 2", "1 step forward 2 E_BEDROCK_HIT\nEOR", "1 2\n>.")

    # 5. Minden előírt futásidejű hiba, API-név/paraméter és első hiba szabály.
    errors = [
        ("nem_inicializalt_print", "print nincs", "1 print E_UNINITIALIZED"),
        ("nem_inicializalt_ertekadas", "set x to nincs", "1 E_UNINITIALIZED"),
        ("nem_inicializalt_bal_operandus", "set x to nincs + 5", "1 E_UNINITIALIZED"),
        ("nem_inicializalt_jobb_operandus", "set x to 5 + nincs", "1 E_UNINITIALIZED"),
        ("nem_inicializalt_not", "set x to not nincs", "1 E_UNINITIALIZED"),
        ("nem_inicializalt_if", "if nincs\n  print 1", "1 E_UNINITIALIZED"),
        ("nem_inicializalt_while", "while nincs\n  print 1", "1 E_UNINITIALIZED"),
        ("nem_inicializalt_step", "step forward nincs", "1 step forward E_UNINITIALIZED"),
        ("nem_inicializalt_turn", "turn by nincs", "1 turn by E_UNINITIALIZED"),
        ("nem_inicializalt_isThere", "set x to isThere nincs", "1 isThere E_UNINITIALIZED"),
        ("nem_logikai_if_literal", "if 1\n  print 1", "1 E_NON_BOOL_CONDITION"),
        ("nem_logikai_while_literal", "while 1\n  print 1", "1 E_NON_BOOL_CONDITION"),
        ("tipushibas_osszeadas_bal", "set x to true + 3", "1 E_BAD_OPERAND"),
        ("tipushibas_osszeadas_jobb", "set x to 3 + true", "1 E_BAD_OPERAND"),
        ("tipushibas_kivonas", "set x to false - 3", "1 E_BAD_OPERAND"),
        ("tipushibas_szorzas", "set x to 3 * false", "1 E_BAD_OPERAND"),
        ("tipushibas_osszehasonlitas_bal", "set x to true < 3", "1 E_BAD_OPERAND"),
        ("tipushibas_osszehasonlitas_jobb", "set x to 3 >= false", "1 E_BAD_OPERAND"),
        ("tipushibas_es", "set x to 1 and true", "1 E_BAD_OPERAND"),
        ("tipushibas_vagy", "set x to true or 1", "1 E_BAD_OPERAND"),
        ("tipushibas_not", "set x to not 0", "1 E_BAD_OPERAND"),
        ("kulonbozo_tipus_egyenlo", "set x to true = 1", "1 E_BAD_OPERAND"),
        ("kulonbozo_tipus_nemegyenlo", "set x to 1 <> false", "1 E_BAD_OPERAND"),
        ("nem_rovidzart_true_or", "set x to true or nincs", "1 E_UNINITIALIZED"),
        ("nem_rovidzart_false_and", "set x to false and nincs", "1 E_UNINITIALIZED"),
        ("elso_hiba_bal_oldali_tipus", "set x to true + nincs", "1 E_BAD_OPERAND"),
        ("elso_hiba_bal_oldali_logikai_tipus", "set x to 1 and nincs", "1 E_BAD_OPERAND"),
        ("elso_hiba_jobb_oldali_nem_inicializalt", "set x to 1 = nincs", "1 E_UNINITIALIZED"),
        ("elso_hiba_egyenloseg_jobb_oldali", "set x to true = 1", "1 E_BAD_OPERAND"),
        ("param_hibas_step_bool", "step forward true", "1 step forward true E_BAD_ARG"),
        ("param_hibas_turn_bool", "turn by false", "1 turn by false E_BAD_ARG"),
        ("param_hibas_isThere_bool", "set x to isThere true", "1 isThere true E_BAD_ARG"),
        ("param_hibas_isThere_3", "set x to isThere 3", "1 isThere 3 E_BAD_ARG"),
        ("param_hibas_isThere_100", "set x to isThere 100", "1 isThere 100 E_BAD_ARG"),
        ("arany_nelkul_banyaszas", "mine here", "1 mine here E_NO_GOLD"),
    ]
    for name, prog, exp in errors:
        add(name, "hibak", prog, exp + "\nEOR")
    add("tipusvalt_as_egeszrol_boolra", "hibak", "set x to 1\nset x to true\nprint x", "1\n2 E_TYPE_MISMATCH\nEOR")
    add("tipusvalt_as_boolrol_egeszre", "hibak", "set x to true\nset x to 1", "1\n2 E_TYPE_MISMATCH\nEOR")
    add("tipusvalt_as_api_kiert_utan", "hibak", "set x to 1\nset x to isThere 0", "1\n2 isThere 0 false E_TYPE_MISMATCH\nEOR")
    add("nem_logikai_if_valtozo", "hibak", "set x to 1\nif x\n  print 0", "1\n2 E_NON_BOOL_CONDITION\nEOR")
    add("nem_logikai_while_valtozo", "hibak", "set x to 0\nwhile x\n  print 0", "1\n2 E_NON_BOOL_CONDITION\nEOR")
    add("tipushibas_operandus_valtozobol", "hibak", "set x to true\nset y to x * 2", "1\n2 E_BAD_OPERAND\nEOR")
    add("param_hibas_isThere_valtozobol", "hibak", "set n to 3\nset x to isThere n", "1\n2 isThere 3 E_BAD_ARG\nEOR")
    add("negativ_step", "hibak", "set n to 0 - 1\nstep forward n", "1\n2 step forward -1 E_BAD_ARG\nEOR")
    add("negativ_turn", "hibak", "set n to 1 - 2\nturn by n", "1\n2 turn by -1 E_BAD_ARG\nEOR")
    add("negativ_isThere", "hibak", "set n to 1 - 2\nset x to isThere n", "1\n2 isThere -1 E_BAD_ARG\nEOR")
    add("hiba_megallitja_a_futast", "hibak", "print 1\nmine here\nprint 2", "1 print 1\n2 mine here E_NO_GOLD\nEOR")
    add("hiba_elott_sikeres_utasitasok", "hibak", "set a to 1\nset b to 2\nstep forward 0\nset x to true + false\nprint 100", "1\n2\n3 step forward 0\n4 E_BAD_OPERAND\nEOR")

    # 6. Pontosan 1000 feldolgozott forrássor, utána az alternatív lezárás.
    p999 = "\n".join("set x to 0" for _ in range(999))
    p1000 = p999 + "\nset x to 0"
    p1001 = p1000 + "\nset x to 0"
    add("limit_999_sor", "limit", p999, expected_lines(*(str(i) for i in range(1, 1000)), "EOR"))
    add("limit_1000_sor", "limit", p1000, expected_lines(*(str(i) for i in range(1, 1001)), "EOR"))
    add("limit_1001_sor", "limit", p1001, expected_lines(*(str(i) for i in range(1, 1001)), LIMIT_MESSAGE))
    add("limit_vegtelen_while", "limit", "while true\n  set x to 0",
        expected_lines(*(str(1 if i % 2 == 0 else 2) for i in range(1000)), LIMIT_MESSAGE))
    add("ezredik_sorban_hiba", "limit", p999 + "\nmine here",
        expected_lines(*(str(i) for i in range(1, 1000)), "1000 mine here E_NO_GOLD", "EOR"))

    # Saját fixture-k helyességének ellenőrzése: csak szabályos bemeneteket generálunk.
    seen: set[str] = set()
    for case in result:
        if case.name in seen:
            raise AssertionError(f"Ismételt tesztnév: {case.name}")
        seen.add(case.name)
        map_lines = case.map_text.splitlines()
        dims = map_lines[0].split(" ")
        if len(dims) != 2:
            raise AssertionError(f"Hibás térképméret: {case.name}")
        r, c = map(int, dims)
        if not 1 <= r <= 15 or not 1 <= c <= 15 or len(map_lines) != r + 1:
            raise AssertionError(f"Hibás térképméret/sorszám: {case.name}")
        if any(len(line) != c or set(line) - set(".@#><^v") for line in map_lines[1:]):
            raise AssertionError(f"Hibás térkép karakter/sorhossz: {case.name}")
        if sum(ch in "><^v" for line in map_lines[1:] for ch in line) != 1:
            raise AssertionError(f"Pontosan egy robot kell: {case.name}")
        if any(not line.strip() for line in case.program.splitlines()):
            raise AssertionError(f"Üres programsor: {case.name}")
        if any("\t" in line or line.rstrip() != line for line in case.program.splitlines()):
            raise AssertionError(f"Érvénytelen behúzás/szélső whitespace: {case.name}")
        if not case.expected.endswith("\n") or "\n\n" in case.expected:
            raise AssertionError(f"Érvénytelen várt napló: {case.name}")
    return result


def worker(target: Path, in_path: Path | None, out_path: Path | None,
           probe: bool = False, previous_input: Path | None = None) -> int:
    """A tesztelt modult importálja; runScriptQ-t Python-függvényként hívja meg."""
    try:
        module_path = target.resolve(strict=True)
        sys.path.insert(0, str(module_path.parent))
        spec = importlib.util.spec_from_file_location("minescript_under_test", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Nem tölthető be a modul: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        func = getattr(module, "runScriptQ", None)
        if not callable(func):
            raise AttributeError("Nem található hívható runScriptQ(path, outPath) függvény")
        if probe:
            return 0
        assert in_path is not None and out_path is not None

        def disallow_input(*args, **kwargs):
            raise RuntimeError("A -q mód a felhasználótól próbált bemenetet kérni")

        builtins.input = disallow_input
        # Az stdin cső teljesen zárt: közvetlen sys.stdin.read() esetén is azonnal EOF.
        if previous_input is not None:
            func(str(previous_input), str(out_path))
        func(str(in_path), str(out_path))
        return 0
    except BaseException:
        traceback.print_exc()
        return 2


def invoke(target: Path, in_path: Path | None, out_path: Path | None,
           timeout: float, probe: bool = False,
           previous_input: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-B", str(Path(__file__).resolve()), "--_worker", "--target", str(target)]
    if probe:
        cmd.append("--_probe")
    else:
        assert in_path is not None and out_path is not None
        cmd.extend(["--_input", str(in_path), "--_output", str(out_path)])
        if previous_input is not None:
            cmd.extend(["--_previous_input", str(previous_input)])
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, check=False)


def run_one(case: Case, target: Path, timeout: float, save_failures: Path | None,
            require_print: bool = False) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="MineScript_q teszt_") as td:
        root = Path(td)
        in_path = root / "bemenet próba_001.txt"
        out_path = root / "kimenet próba_001.txt"
        contents = case.map_text + "\n" + (case.program + "\n" if case.program else "")
        in_path.write_text(contents, encoding="utf-8", newline="\n")
        previous_input = None
        if case.prelude is not None:
            previous_input = root / "korábbi futás bemenete.txt"
            prev_map, prev_prog = case.prelude
            previous_input.write_text(normalize(prev_map) + "\n" + normalize(prev_prog) + "\n",
                                      encoding="utf-8", newline="\n")
        # Az előző napló tartalmát kötelező teljesen felülírni.
        out_path.write_text("REGI_NAPLO_NEM_MARADHAT\n", encoding="utf-8")
        try:
            proc = invoke(target, in_path, out_path, timeout, previous_input=previous_input)
            if proc.returncode != 0:
                reason = f"A runScriptQ hibával tért vissza (exit={proc.returncode}).\n{proc.stderr}"
                return _fail(case, reason, in_path, out_path, save_failures)
        except subprocess.TimeoutExpired as e:
            reason = (f"IDŐTÚLLÉPÉS {timeout:g} másodperc után: a runScriptQ nem fejeződött be. "
                      "Lehetséges hiányzó 1000-es limit vagy EOR-kezelési hiba.")
            return _fail(case, reason, in_path, out_path, save_failures)
        if not out_path.is_file():
            return _fail(case, "Nem készült el a megadott kimeneti fájl.", in_path, out_path, save_failures)
        actual = out_path.read_text(encoding="utf-8")
        if actual != case.expected:
            diff = "".join(difflib.unified_diff(case.expected.splitlines(keepends=True),
                                                actual.splitlines(keepends=True),
                                                fromfile="ELVÁRT", tofile="TÉNYLEGES"))
            if not diff:
                diff = f"A teljes szöveg eltér: elvárt={case.expected!r}, tényleges={actual!r}"
            return _fail(case, "NAPLÓELTÉRÉS:\n" + diff, in_path, out_path, save_failures)
        if require_print and case.require_stdout and case.require_stdout not in proc.stdout:
            return _fail(case, f"A print értéke ({case.require_stdout!r}) nem látszik a konzolon.\n"
                               f"stdout: {proc.stdout!r}", in_path, out_path, save_failures)
        return True, ""


def _fail(case: Case, reason: str, in_path: Path, out_path: Path,
          save_failures: Path | None) -> tuple[bool, str]:
    if save_failures is not None:
        folder = save_failures / re.sub(r"[^a-zA-Z0-9_-]", "_", case.name)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "input.txt").write_bytes(in_path.read_bytes())
        (folder / "expected.txt").write_text(case.expected, encoding="utf-8")
        if out_path.exists():
            (folder / "actual.txt").write_bytes(out_path.read_bytes())
        (folder / "error.txt").write_text(reason, encoding="utf-8")
        reason += f"\nMentett hibás teszteset: {folder}"
    return False, reason


def self_test() -> int:
    """Csak a tesztkeret mechanikáját próbálja ki egy ideiglenes hamis függvénnyel."""
    cases = build_cases()
    with tempfile.TemporaryDirectory(prefix="q_harness_selftest_") as td:
        root = Path(td)
        target = root / "sample_runner.py"
        target.write_text("""\
def runScriptQ(path, outPath):
    with open(outPath, 'w', encoding='utf-8') as f:
        f.write('EOR\\n')
""", encoding="utf-8")
        proc = invoke(target, None, None, 5, probe=True)
        if proc.returncode:
            print("ÖNTESZT HIBA: a próbaimport nem működik", proc.stderr)
            return 1
        empty = next(c for c in cases if c.name == "ures_program")
        ok, error = run_one(empty, target, 5, None)
        if not ok:
            print("ÖNTESZT HIBA: az egyező naplót elutasította", error)
            return 1
        different = next(c for c in cases if c.name == "csak_szamok")
        ok, error = run_one(different, target, 5, None)
        if ok or "NAPLÓELTÉRÉS" not in error:
            print("ÖNTESZT HIBA: az eltérő naplót nem jelezte")
            return 1
        target.write_text("""\
def runScriptQ(path, outPath):
    while True:
        pass
""", encoding="utf-8")
        ok, error = run_one(empty, target, 0.8, None)
        if ok or "IDŐTÚLLÉPÉS" not in error:
            print("ÖNTESZT HIBA: a végtelen ciklust nem szakította meg")
            return 1
        target.write_text("""\
def runScriptQ(path, outPath):
    input('Tovább: ')
""", encoding="utf-8")
        ok, error = run_one(empty, target, 3, None)
        if ok or "bemenetet kérni" not in error:
            print("ÖNTESZT HIBA: az interaktív bemenetkérést nem vette észre")
            return 1
    print(f"ÖNTESZT SIKERES: {len(cases)} fixture ellenőrizve; import, siker, eltérés, "
          "időtúllépés, interaktív kérés tesztelve.")
    print("FONTOS: ez nem jelenti a valódi runScriptQ / ProgramRunner sikeres tesztelését!")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="A MineScript runScriptQ(-q) teljes naplózási tesztkészlete")
    parser.add_argument("--target", type=Path, default=Path(__file__).resolve().parent / "mineScriptRunner.py",
                        help="A vizsgált Python-fájl (alapértelmezés: mineScriptRunner.py a teszt mellett)")
    parser.add_argument("--timeout", type=float, default=8.0,
                        help="Egy teszt legfeljebb hány másodpercig futhat (alap: 8)")
    parser.add_argument("--only", default="", help="Csak a név/csoport alapján illeszkedő tesztek (regex)")
    parser.add_argument("--list", action="store_true", help="Az összes teszt nevének listázása")
    parser.add_argument("--verbose", action="store_true", help="Minden sikeres teszt kiírása")
    parser.add_argument("--save-failures", type=Path, default=None,
                        help="Eltérések input/expected/actual fájljainak mentési könyvtára")
    parser.add_argument("--skip-console-print", action="store_true",
                        help="Kikapcsolja a print konzolos megjelenésének alapértelmezett ellenőrzését")
    parser.add_argument("--self-test", action="store_true", help="Csak a tesztkeret önellenőrzése")
    # Rejtett: külön folyamatos, közvetlen Python-függvényhívást végző worker.
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_probe", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_input", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--_output", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--_previous_input", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args._worker:
        return worker(args.target, args._input, args._output, args._probe, args._previous_input)
    if args.self_test:
        return self_test()
    if args.timeout <= 0:
        parser.error("--timeout értéke pozitív szám legyen")
    cases = build_cases()
    if args.only:
        try:
            pattern = re.compile(args.only, re.IGNORECASE)
        except re.error as e:
            parser.error(f"Hibás regex: {e}")
        cases = [c for c in cases if pattern.search(c.name) or pattern.search(c.group)]
    if args.list:
        for case in cases:
            print(f"[{case.group:10}] {case.name}")
        print(f"Összesen: {len(cases)} teszt")
        return 0
    if not cases:
        print("Nincs a szűrőnek megfelelő teszt.")
        return 2
    target = args.target.resolve()
    if not target.is_file():
        print(f"HIÁNYZIK a vizsgált .py fájl: {target}")
        return 2
    try:
        probe = invoke(target, None, None, args.timeout, probe=True)
    except subprocess.TimeoutExpired:
        print("A tesztelt modul importja időtúllépésbe futott.")
        return 2
    if probe.returncode:
        print("NEM FUTTATHATÓ: runScriptQ importálása sikertelen.\n" + probe.stderr)
        print("A mineScriptRunner.py és a hozzá szükséges core/interpreter.py (és egyéb függőségek) "
              "legyenek együtt a projektben.")
        return 2
    print(f"Tesztelt modul: {target}\nTeszt: {len(cases)} eset; időkorlát: {args.timeout:g} s/teszt")
    passed = 0
    for idx, case in enumerate(cases, 1):
        ok, error = run_one(case, target, args.timeout, args.save_failures,
                            require_print=not args.skip_console_print)
        if ok:
            passed += 1
            if args.verbose:
                print(f"  OK {idx}/{len(cases)} [{case.group}] {case.name}")
        else:
            print(f"  HIBA {idx}/{len(cases)} [{case.group}] {case.name}\n{textwrap.indent(error, '       ')}")
    fail_count = len(cases) - passed
    print(f"\nEREDMÉNY: {passed}/{len(cases)} sikeres; {fail_count} hibás")
    if fail_count and args.save_failures is None:
        print("A hibás bemenetek megőrzéséhez használd a --save-failures HIBAK könyvtár kapcsolót.")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
