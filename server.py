import argparse
import json
import os
import re
import sys
from pathlib import Path
from threading import RLock, Thread

from flask import Flask, jsonify, request, send_from_directory
# A webview-t és a werkzeug szervert csak a grafikus ágban importáljuk (lásd lent),
# így a -q mód és a tesztek nem függnek a pywebview-tól.

if __package__:
    from .core.errors import BuildError, MineScriptRuntimeError
    from .core.interpreter import ProgramRunner
    from .core.praser import ident as RESERVED_IDENTIFIERS
else:
    from core.errors import BuildError, MineScriptRuntimeError
    from core.interpreter import ProgramRunner
    from core.praser import ident as RESERVED_IDENTIFIERS


# PyInstaller-rel épített robot.exe-ben a csomagolt fájlok (frontend/dist) a
# sys._MEIPASS mappába kerülnek kicsomagolásra.
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DEFAULT_OUTPUT_NAME = "output.txt"
RESERVED = {word.lower() for word in RESERVED_IDENTIFIERS}
BIN_OPERATORS = {"+", "-", "*", "=", "<>", "<", "<=", ">", ">=", "and", "or", "@"}
# simpleval-literálok: a 'list' az üres lista (nyelvi kiterjesztés).
LITERALS = {"true", "false", "list"}
IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
# A szenzor kódja megegyezik az isThere paraméterével (3-5 csak isThere_extended mellett hívható).
SENSOR_CODES = {".": 0, "#": 1, "@": 2, "+": 3, "T": 4, "~": 5}
SENSOR_NAMES = ("empty", "wall", "gold", "drillable", "support", "station")
MANUAL_ACTIONS = ("turn", "step", "mine", "drill", "place", "charge")
TERMINAL_MARKERS = {"EOR", "INSTRUCTION_COUNT_LIMIT_EXCEEDED"}
# Szerkesztés közben üres mező is lehet; a szöveges nézetben ez a jel áll a helyén.
EMPTY_PLACEHOLDER = "…"

# A robot beállításai a felületről jönnek (nem a bemeneti fájlból). Ha a felhasználó
# nem ad meg mást, ezek érvényesek (modositas.txt: akkumulátor 15, minden művelet 1).
DEFAULT_SETTINGS = {
    "battery_cap": 15,
    "drill_usage": 1,
    "step_usage": 1,
    "turn_usage": 1,
    "mine_usage": 1,
    "isThere_usage": 1,
    "safeToDrill_usage": 1,
    "print_usage": 1,
    "place_usage": 1,
    "isThere_extended": False,
}

app = Flask(__name__, static_folder=None)

app.json.ensure_ascii = False

_lock = RLock()


def _error(message, status=400):
    return jsonify({"error": message}), status


class _EmptyFields:
    """Számolja a kitöltetlen mezőket egy AST fordítása közben."""
    def __init__(self):
        self.count = 0

    def take(self):
        self.count += 1
        return EMPTY_PLACEHOLDER


def _simpleval(value, field, empty=None):
    if not isinstance(value, str):
        raise ValueError(f"{field}: szöveges értéket várunk")
    if value == "" and empty is not None:
        return empty.take()
    if value in LITERALS:
        return value
    if value.isascii() and value.isdecimal():
        if int(value) <= 100:
            return value
        raise ValueError(f"{field}: a számliterál legfeljebb 100 lehet")
    if IDENTIFIER_RE.fullmatch(value) and value.lower() not in RESERVED:
        return value
    raise ValueError(f"{field}: érvénytelen simpleval: {value!r}")


def _identifier(value, field, empty=None):
    if value == "" and empty is not None:
        return empty.take()
    if (not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value)
            or value.lower() in RESERVED):
        raise ValueError(f"{field}: érvénytelen vagy foglalt változónév: {value!r}")
    return value


def _value_to_code(value, field, empty=None):
    if not isinstance(value, dict):
        raise ValueError(f"{field}: hiányzó értékblokk")
    kind = value.get("kind")
    if kind == "simple":
        return _simpleval(value.get("a"), field + ".a", empty)
    if kind == "isThere":
        return "isThere " + _simpleval(value.get("a"), field + ".a", empty)
    if kind == "safeToDrill":
        return "safeToDrill"
    if kind == "list":
        return "list"
    if kind == "unop":
        if value.get("op") not in ("not", "length"):
            raise ValueError(f"{field}: az egyoperandusú művelet 'not' vagy 'length' lehet")
        return value["op"] + " " + _simpleval(value.get("a"), field + ".a", empty)
    if kind == "binop":
        operator = value.get("op")
        if operator not in BIN_OPERATORS:
            raise ValueError(f"{field}: érvénytelen operátor")
        return (f"{_simpleval(value.get('a'), field + '.a', empty)} {operator} "
                f"{_simpleval(value.get('b'), field + '.b', empty)}")
    raise ValueError(f"{field}: ismeretlen értékblokk: {kind!r}")


def ast_to_code(ast, allow_empty=False):
    """Compile the editor's structural AST; do not do runtime type checking.

    allow_empty=True: a kitöltetlen ("") mezők helyére EMPTY_PLACEHOLDER kerül,
    és a harmadik visszatérési érték megadja, hány ilyen mező volt.
    """
    if not isinstance(ast, list):
        raise ValueError("Az AST-nek listának kell lennie")
    lines, line_map, used_ids = [], {}, set()
    empty = _EmptyFields() if allow_empty else None

    def compile_blocks(blocks, indent, control_depth):
        if not isinstance(blocks, list):
            raise ValueError("A blokk törzsének listának kell lennie")
        for block in blocks:
            if not isinstance(block, dict):
                raise ValueError("Minden blokknak objektumnak kell lennie")
            node_id = block.get("id")
            if (not isinstance(node_id, (str, int)) or isinstance(node_id, bool)
                    or node_id == "" or node_id in used_ids):
                raise ValueError("Minden blokkhoz egyedi, nem üres 'id' szükséges")
            used_ids.add(node_id)
            kind = block.get("type")
            field = f"{kind} blokk ({node_id})"
            if kind == "set":
                row = ("set " + _identifier(block.get("ident"), field + ".ident", empty)
                       + " to " + _value_to_code(block.get("value"), field + ".value", empty))
            elif kind == "step":
                row = "step forward " + _simpleval(block.get("arg"), field + ".arg", empty)
            elif kind == "turn":
                row = "turn by " + _simpleval(block.get("arg"), field + ".arg", empty)
            elif kind == "mine":
                row = "mine here"
            elif kind == "drill":
                row = "drill forward"
            elif kind == "place":
                row = "place here"
            elif kind == "charge":
                row = "charge"
            elif kind == "print":
                row = "print " + _simpleval(block.get("arg"), field + ".arg", empty)
            elif kind == "add":
                row = ("add " + _simpleval(block.get("arg"), field + ".arg", empty)
                       + " to " + _identifier(block.get("ident"), field + ".ident", empty))
            elif kind == "remove":
                row = ("remove " + _identifier(block.get("ident"), field + ".ident", empty)
                       + " @ " + _simpleval(block.get("arg"), field + ".arg", empty))
            elif kind in ("if", "while"):
                if control_depth >= 3:
                    raise ValueError("Legfeljebb három egymásba ágyazott vezérlőblokk lehet")
                row = kind + " " + _simpleval(block.get("cond"), field + ".cond", empty)
            else:
                raise ValueError(f"Ismeretlen blokk: {kind!r}")

            lines.append("  " * indent + row)
            line_map[len(lines)] = node_id
            if kind == "while":
                compile_blocks(block.get("body"), indent + 1, control_depth + 1)
            elif kind == "if":
                compile_blocks(block.get("then"), indent + 1, control_depth + 1)
                if block.get("else") is not None:
                    lines.append("  " * indent + "else")
                    line_map[len(lines)] = node_id
                    compile_blocks(block["else"], indent + 1, control_depth + 1)

    compile_blocks(ast, 0, 0)
    if allow_empty:
        return "\n".join(lines), line_map, empty.count
    return "\n".join(lines), line_map


def _runner_to_ast(statements):
    """Convert the parser's syntax tree to editable blocks for the initial file."""
    blocks = []
    for node in statements:
        kind = node["type"]
        block = {"id": f"line-{node['index']}", "type": kind}
        if kind == "set":
            expression = node["calcvalue"]
            expr_kind = expression["type"]
            if expr_kind == "simple":
                if expression["value"] in ("safeToDrill", "list"):
                    value = {"kind": expression["value"]}
                else:
                    value = {"kind": "simple", "a": expression["value"]}
            elif expr_kind == "unop":
                op = expression["operator"]
                value = ({"kind": "isThere", "a": expression["value"]} if op == "isThere"
                         else {"kind": "unop", "op": op, "a": expression["value"]})
            elif expr_kind == "binop":
                value = {"kind": "binop", "a": expression["value1"],
                         "op": expression["operator"], "b": expression["value2"]}
            else:
                raise ValueError("A core ismeretlen kifejezést adott vissza")
            block.update(ident=node["identifier"], value=value)
        elif kind in ("step", "turn", "print"):
            block["arg"] = node["value"]
        elif kind in ("add", "remove"):
            block.update(arg=node["value"], ident=node["identifier"])
        elif kind == "if":
            block["cond"] = node["value"]
            block["then"] = _runner_to_ast(node["block"])
            block["else"] = (_runner_to_ast(node["else_block"])
                             if "else_line" in node else None)
        elif kind == "while":
            block["cond"] = node["value"]
            block["body"] = _runner_to_ast(node["block"])
        elif kind not in ("mine", "drill", "place", "charge"):
            raise ValueError(f"A core ismeretlen parancsot adott vissza: {kind}")
        blocks.append(block)
    return blocks


def _format_log_entry(parts):
    # The core supplies the parsed, evaluated elements, not an already formatted line.
    return " ".join("true" if part is True else "false" if part is False else str(part)
                    for part in parts)


def checked_settings(data):
    """A felületről érkező beállítások ellenőrzése; a hiányzó kulcsok alapértéket kapnak."""
    if not isinstance(data, dict):
        raise ValueError("A beállításokat JSON objektumként kell megadni")
    unknown = sorted(set(data) - set(DEFAULT_SETTINGS))
    if unknown:
        raise ValueError(f"Ismeretlen beállítás: {', '.join(unknown)}")
    settings = dict(DEFAULT_SETTINGS)
    for key, value in data.items():
        if key == "isThere_extended":
            if type(value) is not bool:
                raise ValueError("Az isThere_extended értéke true vagy false lehet")
        elif type(value) is not int or value < 0:
            raise ValueError(f"A(z) {key} értéke nemnegatív egész szám legyen")
        settings[key] = value
    if settings["battery_cap"] < 1:
        raise ValueError("Az akkumulátor kapacitása legalább 1 legyen")
    return settings


def _runner_lines(map_lines, settings, program_lines):
    # A core a térkép utáni JSON-blokkból olvassa a beállításokat: a felületen
    # megadott értékeket ide illesztjük be, így a core változatlanul használható.
    return [*map_lines, json.dumps(settings), *program_lines]


class IncompleteProgram(Exception):
    """Futtatás kitöltetlen mezőkkel: a felhasználó hibája, nem a szerveré."""


class SimulatorSession:
    def __init__(self, input_path, output_path, settings):
        self.input_path = Path(input_path).resolve()
        self.output_path = Path(output_path).resolve()
        self.settings = dict(settings)
        try:
            raw_lines = self.input_path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError:
            raise BuildError("SYNTAX_ERROR", "A bemeneti fájl nem UTF-8 kódolású szöveg")
        if not raw_lines:
            raise BuildError("SYNTAX_ERROR", "A bemeneti fájl üres")
        try:
            rows, cols = (int(n) for n in raw_lines[0].split())
        except ValueError:
            raise BuildError("SYNTAX_ERROR", "Hibás térképfejléc (sorok és oszlopok száma)")
        if len(raw_lines) < rows + 1:
            raise BuildError("SYNTAX_ERROR", "Hiányzó térképsor")
        self.map_input = tuple(raw_lines[:rows + 1])
        program_lines = raw_lines[rows + 1:]
        if program_lines and program_lines[0].strip().startswith("{"):
            raise BuildError("SYNTAX_ERROR", "A bemeneti fájlban nem lehet beállítás-blokk: "
                             "a beállításokat a Beállítások ablakban kell megadni")
        if any(len(row.strip()) != cols for row in self.map_input[1:]):
            raise BuildError("SYNTAX_ERROR", "A térkép sorainak hossza nem egyezik a fejléccel")
        if not any(ch in "<>^v" for row in self.map_input[1:] for ch in row):
            raise BuildError("SYNTAX_ERROR", "A térképen nincs robot")
        self.total_gold = sum(line.count("@") for line in self.map_input[1:])
        self.source = "\n".join(program_lines)
        self.runner = self._new_runner()
        self.ast = _runner_to_ast(self.runner.code)
        self.line_map = self._imported_line_map(self.runner.code)
        self.empty_fields = 0
        self.status = "idle"
        self.mode = None
        self.last_step = None
        self.error = None
        self.collapsed = False

    @staticmethod
    def _imported_line_map(nodes):
        mapping = {}
        for node in nodes:
            node_id = f"line-{node['index']}"
            mapping[node["index"]] = node_id
            if node["type"] == "if":
                mapping.update(SimulatorSession._imported_line_map(node["block"]))
                if "else_line" in node:
                    mapping[node["else_line"]] = node_id
                    mapping.update(SimulatorSession._imported_line_map(node["else_block"]))
            elif node["type"] == "while":
                mapping.update(SimulatorSession._imported_line_map(node["block"]))
        return mapping

    def _new_runner(self, program_lines=None):
        lines = self.source.splitlines() if program_lines is None else program_lines
        return ProgramRunner(_runner_lines(self.map_input, self.settings, lines))

    def reset(self):
        # Félkész programnál csak a térképet töltjük vissza, a kódot nem kell értelmezni.
        self.runner = self._new_runner([]) if self.empty_fields else self._new_runner()
        self.status = "idle"
        self.mode = None
        self.last_step = None
        self.error = None
        self.collapsed = False

    def apply_settings(self, settings):
        # Ellenőrzés a core-ral, mielőtt átvennénk; utána a bánya alaphelyzetbe kerül.
        ProgramRunner(_runner_lines(self.map_input, settings, []))
        self.settings = dict(settings)
        self.reset()

    def set_output(self, output_path):
        self.output_path = _checked_output(output_path, self.input_path)
        self.stop()  # Egy futás naplója ne kerüljön két fájlba.

    def edit_program(self, blocks):
        source, line_map, empty_fields = ast_to_code(blocks, allow_empty=True)
        if empty_fields == 0:
            # Check that the actual core accepts the generated text before committing.
            self._new_runner(source.splitlines())
        self.ast = blocks
        self.source = source
        self.line_map = line_map
        self.empty_fields = empty_fields
        if self.status == "running":
            self.status = "stopped"
            self.mode = None

    def start(self, mode):
        if self.empty_fields:
            raise IncompleteProgram(
                f"A programban {self.empty_fields} kitöltetlen mező van, így nem futtatható")
        runner = self._new_runner()
        # A new run, unlike reset/edit/manual control, replaces the log file.
        with self.output_path.open("w", encoding="utf-8"):
            pass
        self.runner = runner
        self.status = "running"
        self.mode = mode
        self.last_step = None
        self.error = None
        self.collapsed = False

    def stop(self):
        if self.status == "running":
            self.status = "stopped"
        self.mode = None

    def _write_log(self, parts):
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(_format_log_entry(parts) + "\n")

    def step(self):
        if self.status != "running":
            raise RuntimeError("Nincs futó program")
        result = self.runner.next_step()
        if not isinstance(result, list) or not result:
            raise RuntimeError("A core nem adott értelmezhető lépést")
        self._write_log(result)

        if result == ["EOR"]:
            self.status = "finished"
            self.last_step = {"finished": True, "line": None, "node_id": None,
                              "log_entry": "EOR", "error": None}
        elif result == ["INSTRUCTION_COUNT_LIMIT_EXCEEDED"]:
            self.status = "limit_exceeded"
            self.error = "INSTRUCTION_COUNT_LIMIT_EXCEEDED"
            self.last_step = {"finished": True, "line": None, "node_id": None,
                              "log_entry": self.error, "error": self.error}
        else:
            line = int(result[0])
            error = result[-1] if isinstance(result[-1], str) and result[-1].startswith("E_") else None
            self.last_step = {"finished": bool(error), "line": line,
                              "node_id": self.line_map.get(line),
                              "log_entry": _format_log_entry(result), "error": error}
            if error:
                self.status = "error"
                self.error = error
                self.collapsed = error == "E_MINE_COLLAPSE"
                # The core emits EOR only on the subsequent call after a runtime error.
                # Finish the file now, without requiring a second user-visible step.
                end = self.runner.next_step()
                if end != ["EOR"]:
                    raise RuntimeError("A core nem zárta le a hibás futást EOR-ral")
                self._write_log(end)
        return self.last_step

    def manual(self, action, value):
        self.stop()  # Abort program execution; never append to its output log.
        # A beomlott bánya használhatatlan: a visszaállításig semmilyen művelet nem megy.
        if self.collapsed:
            return {"ok": False, "error": "E_MINE_COLLAPSE"}
        world = self.runner.map
        try:
            # Ugyanazok a core-műveletek, mint a programban: ugyanúgy fogyasztanak
            # energiát, és ugyanúgy beomolhat a bánya.
            if action == "turn":
                world.turn(value % 4)
            elif action == "step":
                world.move(value)
            elif action == "mine":
                world.mineHere()
            elif action == "drill":
                world.drill()
            elif action == "place":
                world.place()
            elif action == "charge":
                world.charge()
            else:
                raise ValueError("Ismeretlen kézi művelet")
        except MineScriptRuntimeError as err:
            if err.code == "E_MINE_COLLAPSE":
                self.collapsed = True
            return {"ok": False, "error": err.code}
        return {"ok": True, "error": None}

    @staticmethod
    def _safe_to_drill(world, x, y):
        # A core beomlás-ellenőrzése, de energiafogyasztás nélkül (csak kijelzéshez).
        try:
            world._check_collapse(x, y)
        except MineScriptRuntimeError:
            return False
        return True

    def state(self):
        world = self.runner.map
        x, y = world.robot_x, world.robot_y
        next_x, next_y = x + world.robot_dir[0], y + world.robot_dir[1]
        inside = 0 <= next_x < world.x and 0 <= next_y < world.y
        char = world.map[next_y][next_x] if inside else "#"
        sensor_code = SENSOR_CODES[char]
        collected = world.player_gold_collected
        energy = max(0, world.energy)
        return {
            "loaded": True,
            "files": {"input": str(self.input_path), "output": str(self.output_path)},
            "map": {"width": world.x, "height": world.y,
                    # A teljes, aktuális térkép ('.', '#', '@', '+', 'T', '~').
                    "tiles": ["".join(row) for row in world.map],
                    # Felfedezett-e a mező: ahol a robot járt, vagy amire isThere hívódott.
                    "discovered": [[cell != "?" for cell in row] for row in world.discovered],
                    # Régi formátum: csak a felfedezett mezők, a többi '?'.
                    "visible": ["".join(row) for row in world.get_map()]},
            "robot": {"x": x, "y": y, "direction": world.get_robot_dir(),
                      "on_gold": world.map[y][x] == "@",
                      "on_station": world.map[y][x] == "~",
                      "destroyed": self.collapsed},
            # A kijelzés nem fogyaszt energiát és nem tesz felfedezetté mezőt.
            "sensor": {"code": sensor_code, "type": SENSOR_NAMES[sensor_code],
                       "safe_to_drill": (self._safe_to_drill(world, next_x, next_y)
                                         if char == "+" else None)},
            "energy": {"currentenergy": energy, "maxenergy": world.energy_capacity},
            "current_energy": energy,
            "max_energy": world.energy_capacity,
            "settings": dict(self.settings),
            "mine": {"collapsed": self.collapsed},
            "gold": {"collected": collected, "remaining": self.total_gold - collected,
                     "total": self.total_gold},
            "console": world.console[:],
            "variables": self.runner.variables.copy(),
            "program": {"source": self.source, "lines": self.source.splitlines(),
                        "ast": self.ast, "line_map": self.line_map,
                        "empty_fields": self.empty_fields,
                        "runnable": self.empty_fields == 0},
            "execution": {"status": self.status, "mode": self.mode,
                          "running": self.status == "running",
                          "instruction_count": self.runner.exec_count,
                          "last_step": self.last_step, "error": self.error},
        }


session = None
# A felületen megadott beállítások; minden betöltött bemenetre érvényesek.
current_settings = dict(DEFAULT_SETTINGS)


class NotLoaded(Exception):
    """Még nincs betöltött bemenet: a felhasználó a felületen választja ki."""


@app.errorhandler(NotLoaded)
def _not_loaded(_exc):
    return _error("Nincs betöltött bánya: előbb nyiss meg egy bemeneti fájlt", 409)


def _current_session():
    if session is None:
        raise NotLoaded()
    return session


class OutputPathError(ValueError):
    """Rossz naplóhely (nem a bemenet hibája)."""


def _checked_output(output_path, input_path):
    path = Path(output_path).resolve()
    if path.is_dir():
        raise OutputPathError("A napló helye egy mappa, nem fájl")
    if not path.parent.is_dir():
        raise OutputPathError("A napló mappája nem létezik")
    if path == Path(input_path).resolve():
        raise OutputPathError("A napló nem írhatja felül a bemeneti fájlt")
    return path


def configure(input_path, output_path=None):
    """Betölti a bemenetet; a napló alapértelmezett helye a korábbi, vagy a bemenet mellett."""
    global session
    if output_path is None:
        output_path = (session.output_path if session is not None
                       else Path(input_path).resolve().parent / DEFAULT_OUTPUT_NAME)
    output_path = _checked_output(output_path, input_path)
    new_session = SimulatorSession(input_path, output_path, current_settings)
    with _lock:
        session = new_session
    return new_session


def _not_loaded_state():
    return {"loaded": False, "files": {"input": None, "output": None},
            "settings": dict(current_settings)}


@app.get("/api/state")
def get_state():
    with _lock:
        if session is None:
            return jsonify(_not_loaded_state())
        return jsonify(session.state())


@app.post("/api/load")
def load_files():
    """Bemenet betöltése és/vagy a napló helyének megadása: {"input": ..., "output": ...}."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("JSON objektumot várunk: {\"input\": ..., \"output\": ...}")
    input_path, output_path = data.get("input"), data.get("output")
    for value, name in ((input_path, "input"), (output_path, "output")):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            return _error(f"Érvénytelen útvonal: {name}")
    if not input_path and not output_path:
        return _error("Add meg a bemeneti fájlt vagy a napló helyét")
    with _lock:
        try:
            if input_path:
                configure(input_path, output_path)
            else:
                _current_session().set_output(output_path)
        except BuildError as err:
            return jsonify({"error": f"Hibás bemenet: {err.msg}", "code": err.code}), 400
        except OutputPathError as err:
            return _error(str(err))
        except FileNotFoundError:
            return _error("A bemeneti fájl nem található")
        except OSError as err:
            return _error(f"A fájl nem olvasható: {err.strerror or err}")
        except (ValueError, TypeError, KeyError, IndexError) as err:
            return _error(f"Hibás bemenet: {err}")
        return jsonify(session.state())


@app.get("/api/settings")
def get_settings():
    with _lock:
        return jsonify({"settings": dict(current_settings), "defaults": dict(DEFAULT_SETTINGS)})


@app.put("/api/settings")
def put_settings():
    """A Beállítások ablak JSON-ja; a hiányzó kulcsok alapértéket kapnak."""
    global current_settings
    data = request.get_json(silent=True)
    try:
        settings = checked_settings(data.get("settings") if isinstance(data, dict) and "settings" in data
                                    else data)
    except ValueError as err:
        return _error(str(err))
    with _lock:
        if session is not None:
            try:
                session.apply_settings(settings)
            except BuildError as err:
                return _error(f"Hibás beállítás: {err.msg}")
        current_settings = settings
        return jsonify(session.state() if session is not None else _not_loaded_state())


@app.put("/api/program")
def update_program():
    data = request.get_json(silent=True)
    blocks = data.get("ast") if isinstance(data, dict) else data
    with _lock:
        try:
            _current_session().edit_program(blocks)
        except BuildError as err:
            return _error(err.msg)
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            return _error(str(exc))
        return jsonify(_current_session().state())


@app.post("/api/run/start")
def start_run():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("mode") not in ("run", "debug"):
        return _error("A mód 'run' vagy 'debug' lehet")
    with _lock:
        try:
            _current_session().start(data["mode"])
        except IncompleteProgram as exc:
            return _error(str(exc), 409)
        except BuildError as err:
            return _error(err.msg)
        except (OSError, ValueError, TypeError, IndexError) as exc:
            return _error(f"Nem sikerült elindítani a futást: {exc}", 500)
        return jsonify(_current_session().state())


@app.post("/api/run/step")
def run_step():
    with _lock:
        if _current_session().status != "running":
            return _error("Nincs futó program", 409)
        try:
            _current_session().step()
        except (RuntimeError, ValueError, OSError) as exc:
            _current_session().stop()
            return _error(f"Nem sikerült végrehajtani a lépést: {exc}", 500)
        return jsonify(_current_session().state())


@app.post("/api/run/stop")
def stop_run():
    with _lock:
        _current_session().stop()
        return jsonify(_current_session().state())


@app.post("/api/manual")
def manual():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("action") not in MANUAL_ACTIONS:
        return _error("Ismeretlen kézi művelet")
    action = data["action"]
    value = data.get("value", 1)
    if action in ("turn", "step") and (type(value) is not int or value < 0):
        return _error("A 'value' nemnegatív egész szám kell legyen")
    with _lock:
        result = _current_session().manual(action, value)
        return jsonify({**_current_session().state(), "manual_result": result})


@app.post("/api/reset")
def reset():
    with _lock:
        _current_session().reset()
        return jsonify(_current_session().state())


@app.get("/api/log")
def get_log():
    """A naplófájl aktuális tartalma (a „Napló megnyitása” gombhoz)."""
    with _lock:
        path = _current_session().output_path
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            content = ""
        return jsonify({"path": str(path), "content": content,
                        "lines": content.splitlines()})


def _ui_dir():
    configured = os.environ.get("ROBOT_UI_DIST")
    candidates = ([Path(configured)] if configured else []) + [
        BASE_DIR / "ui" / "dist", BASE_DIR / "frontend" / "dist",
        BASE_DIR / "dist", BASE_DIR / "build",
        BASE_DIR / "ui" / "build", BASE_DIR / "frontend" / "build",
    ]
    return next((path.resolve() for path in candidates if (path / "index.html").is_file()), None)


@app.get("/")
@app.get("/<path:asset>")
def serve_ui(asset=""):
    # Serve the built SPA at the same origin as the API (works inside pywebview).
    dist = _ui_dir()
    if dist is None:
        return _error("Nem található a React build (ROBOT_UI_DIST)", 404)
    target = dist / asset
    if asset and target.is_file() and target.resolve().is_relative_to(dist):
        return send_from_directory(dist, asset)
    if asset.startswith("api/"):
        return _error("Ismeretlen API endpoint", 404)
    return send_from_directory(dist, "index.html")


def run_quiet(input_path, output_path, settings=None):
    """Csendes futtatás belső teszteléshez, ugyanazzal a core-ral és naplóformátummal."""
    with _lock:
        session_ = SimulatorSession(input_path, output_path, settings or current_settings)
    runner = session_.runner
    with Path(output_path).open("w", encoding="utf-8") as out:
        while True:
            result = runner.next_step()
            if not isinstance(result, list) or not result:
                raise RuntimeError("A core nem adott értelmezhető lépést")
            out.write(_format_log_entry(result) + "\n")
            if result[0] in TERMINAL_MARKERS:
                break


def _has_webview2():
    """Telepítve van-e a Microsoft Edge WebView2 Runtime (a pywebview EdgeChromium motorja)."""
    if sys.platform != "win32":
        return False
    import winreg
    runtime = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for hive, path in ((winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\{runtime}"),
                       (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\{runtime}"),
                       (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\{runtime}")):
        try:
            with winreg.OpenKey(hive, path) as key:
                version, _ = winreg.QueryValueEx(key, "pv")
                if version and version != "0.0.0.0":
                    return True
        except OSError:
            pass
    return False


def _choose_gui():
    """EdgeChromium, ha van WebView2; különben Qt (PyQt6 WebEngine).

    WebView2 nélkül a pywebview a régi Internet Explorer motorra váltana, amelyen a
    React felület nem fut, ezért ilyenkor a Qt-t kérjük. A ROBOT_GUI=qt környezeti
    változóval a Qt kényszeríthető (teszteléshez).
    """
    forced = os.environ.get("ROBOT_GUI", "").strip().lower()
    if forced:
        return forced
    return None if _has_webview2() else "qt"


FILE_TYPES = ("Szövegfájl (*.txt)", "Minden fájl (*.*)")


class DesktopApi:
    """A felület JavaScriptből hívja (window.pywebview.api).

    A fájlválasztók a pywebview saját, programon belüli párbeszédablakai:
    nem indítanak külön alkalmazást. Mégsem esetén None.
    """

    def pick_input(self):
        import webview
        directory = str(session.input_path.parent) if session is not None else ""
        result = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN, directory=directory, file_types=FILE_TYPES)
        return result[0] if result else None

    def pick_output(self):
        import webview
        if session is not None:
            directory, name = str(session.output_path.parent), session.output_path.name
        else:
            directory, name = "", DEFAULT_OUTPUT_NAME
        result = webview.windows[0].create_file_dialog(
            webview.FileDialog.SAVE, directory=directory, save_filename=name, file_types=FILE_TYPES)
        return result[0] if result else None


def run_gui(input_path=None, output_path=None):
    import webview
    from werkzeug.serving import make_server

    # Paraméter nélkül üresen indul; a bemenetet a felületen kell kiválasztani.
    if input_path is not None:
        configure(input_path, output_path)

    # 0-s port: az operációs rendszer ad egy szabad portot, így nem ütközünk más programmal.
    server = make_server("127.0.0.1", 0, app)
    url = f"http://127.0.0.1:{server.server_port}"
    Thread(target=server.serve_forever, daemon=True).start()

    # A felület a Python-alkalmazáson belül, beágyazott webnézetben jelenik meg
    # (a verseny szabálya: külső böngészőt / alkalmazást nem indíthatunk).
    webview.create_window("Robotszimulátor – MineScript IDE", url, js_api=DesktopApi(),
                          width=1600, height=950, min_size=(1100, 700), maximized=True)
    gui = _choose_gui()
    try:
        try:
            webview.start(gui=gui)
        except Exception:
            if gui == "qt":
                raise
            # Ha az EdgeChromium nem indul el, a Qt motorral próbáljuk újra.
            webview.start(gui="qt")
    finally:
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="robot", description="MineScript IDE (Flask + pywebview)")
    parser.add_argument("-q", action="store_true",
                        help="Csendes futtatás belső teszteléshez (bemenet és napló kötelező)")
    parser.add_argument("input", type=Path, nargs="?", help="Térkép és MineScript forráskód (elhagyható)")
    parser.add_argument("output", type=Path, nargs="?", help="Futási naplófájl (elhagyható)")
    args = parser.parse_args()
    if args.q:
        if args.input is None or args.output is None:
            parser.error("a -q módhoz bemeneti és kimeneti fájl is kell")
        run_quiet(args.input, args.output)
    else:
        run_gui(args.input, args.output)
