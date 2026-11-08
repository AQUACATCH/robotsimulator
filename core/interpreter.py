from .praser import parse_map, parse_code, indent_code
from .world import Map
import copy

class MineScriptRuntimeError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code

class ProgramRunner:
    def __init__(self, lines_raw):
        [data, map, size] = parse_map(lines_raw)
        self.og_map = Map(map, size)
        self._reset_map()
        self.variables = {}
        self.condition_true = None
        self.ended = False
        self.exec_count = 0
        self.is_errored = False

        code_raw = []
        for index, line in enumerate(data):
            parsed = parse_code(line)
            if parsed == None:
                continue
            parsed["index"] = index + 1
            code_raw.append(parsed)
        self.code = indent_code(code_raw)
        self.executor = self._next_line(self.code)

    def _reset_map(self):
        self.map = copy.deepcopy(self.og_map)

    # kiszámolja a calculated val típusú (csak set-nél van) műveletek értékét (unop, binop, simpleval), functiont (isThere) az egyszerűség kedvéért unopnak kezeli
    def _calculated_value(self, calcval, log:list):
        kind = calcval["type"]
        match kind:
            case "simple":
                if calcval["value"] == "isThere":
                    raise MineScriptRuntimeError("E_BAD_ARG")
                return self._resolve(calcval["value"])
            case "unop":
                operator = calcval["operator"]
                if operator == "isThere":
                    # Napló: "isThere <paraméter> <eredmény>". Nem inicializált paraméternél
                    # csak "isThere E_UNINITIALIZED" (paraméter nélkül), érvénytelen paraméternél
                    # a kiértékelt paraméter is a naplóba kerül: "isThere 3 E_BAD_ARG".
                    log.append(operator)
                    val = self._resolve(calcval["value"])
                    log.append(val)
                    if type(val) is not int or val not in (0, 1, 2):
                        raise MineScriptRuntimeError("E_BAD_ARG")
                    res = self.map.isThere(val)
                    log.append(res)
                    return res
                val = self._resolve(calcval["value"])
                if type(val) is not bool:
                    raise MineScriptRuntimeError("E_BAD_OPERAND")
                return not val
            case "binop":
                operator = calcval["operator"]
                # Balról jobbra: minden operandust a beolvasása után azonnal ellenőrzünk,
                # és az első hibánál megállunk (pl. "true + c" -> E_BAD_OPERAND, a c-t
                # már nem olvassuk be). Az = és a <> első operandusa bármilyen típusú
                # lehet, ott a második beolvasása után nézzük a két típus egyezését.
                # Nincs rövidzár: "true or c" esetén a c-t is beolvassuk.
                if operator in ("=", "<>"):
                    expected = None
                elif operator in ("and", "or"):
                    expected = bool
                else:
                    expected = int

                val1 = self._resolve(calcval["value1"])
                if expected is not None and type(val1) is not expected:
                    raise MineScriptRuntimeError("E_BAD_OPERAND")
                val2 = self._resolve(calcval["value2"])
                if type(val2) is not (expected if expected is not None else type(val1)):
                    raise MineScriptRuntimeError("E_BAD_OPERAND")

                if operator == "=":
                    return val1 == val2
                if operator == "<>":
                    return val1 != val2
                if operator == "and":
                    return val1 and val2
                if operator == "or":
                    return val1 or val2
                match operator:
                    case "+":
                        return val1 + val2
                    case "-":
                        return val1 - val2
                    case "*":
                        return val1 * val2
                    case "<":
                        return val1 < val2
                    case "<=":
                        return val1 <= val2
                    case ">":
                        return val1 > val2
                    case ">=":
                        return val1 >= val2


    def _resolve(self, val:str):
        if val == "true":
            return True
        if val == "false":
            return False
        if val.isdecimal():
            return int(val)
        if val not in self.variables:
            raise MineScriptRuntimeError("E_UNINITIALIZED")
        return self.variables[val]

    def _next_line(self, lines):
        for statemant in lines:
            kind = statemant["type"]
            if kind == "while":
                while True:
                    yield statemant
                    if not self.condition_true:
                        break
                    yield from self._next_line(statemant["block"])
            elif kind == "if":
                yield statemant
                if self.condition_true:
                    yield from self._next_line(statemant["block"])
                elif 'else_line' in statemant:
                    yield {'type': 'else', 'index': statemant['else_line']}
                    yield from self._next_line(statemant['else_block'])
            else:
                yield statemant

    def _execute(self, statemant):
        kind = statemant["type"]
        log = [str(statemant["index"])]
        try:
            if kind == "set":
                val = self._calculated_value(statemant["calcvalue"], log)
                ident = statemant["identifier"]
                if ident not in self.variables:
                    self.variables[ident] = val
                elif type(val) != type(self.variables[ident]):
                    raise MineScriptRuntimeError("E_TYPE_MISMATCH")
                else:
                    self.variables[ident] = val
            elif kind in ["step", "turn"]:
                # Előbb az API neve kerül a naplóba, hogy nem inicializált paraméternél
                # "step forward E_UNINITIALIZED" legyen. Rossz paraméternél (logikai érték
                # vagy negatív szám) a kiértékelt paraméter is látszik: "turn by -1 E_BAD_ARG".
                log.append("step forward" if kind == "step" else "turn by")
                val = self._resolve(statemant["value"])
                log.append(val)
                if type(val) is not int or val < 0:
                    raise MineScriptRuntimeError("E_BAD_ARG")
                if kind == "step":
                    res = self.map.move(val)
                    if not res:
                        raise MineScriptRuntimeError("E_BEDROCK_HIT")
                else:
                    self.map.turn(val)
            elif kind == "mine":
                log.append("mine here")
                if not self.map.mineHere():
                    raise MineScriptRuntimeError("E_NO_GOLD")
            elif kind in ["while", "if"]:
                val = self._resolve(statemant["value"])
                if type(val) is not bool:
                    raise MineScriptRuntimeError("E_NON_BOOL_CONDITION")
                self.condition_true = val
            elif kind == "print":
                log.append(kind)
                val = self._resolve(statemant["value"])
                self.map.print(val)
                log.append(val)     
            elif kind == "else":
                pass
            else:
                raise Exception("Hibás sor fordítás")

            """mp = self.map.get_map() if len(log) > 1 else None
            if mp is not None:
                for line in mp:
                    print(line)
                print()"""
            return log, False
                
        except MineScriptRuntimeError as err:
            return log + [err.code], True
    
    #A kód következő lépését végrehajtja
    # Visszaadja a logolni való eredményt
    def next_step(self):
        if self.ended:
            return None
        if self.is_errored:
            self.ended = True
            return ["EOR"]
        line = next(self.executor, None)
        if line == None:
            self.ended = True
            return ["EOR"]
        if self.exec_count >= 1000:
            return ["INSTRUCTION_COUNT_LIMIT_EXCEEDED"]
        self.exec_count += 1
        log, is_errored = self._execute(line)
        if is_errored:
            self.is_errored = is_errored
        return log

    def get_world_data(self):
        return {
            "map": self.map.get_map(),
            "size": [self.map.x, self.map.y],
            "robot_pos": [self.map.robot_x, self.map.robot_y],
            "robot_dir": self.map.get_robot_dir()
        }