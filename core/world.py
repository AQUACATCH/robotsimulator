from .errors import MineScriptRuntimeError, BuildError
from functools import wraps

player_chars = {"<": [-1,0], "v": [0,1], ">": [1,0], "^":[0,-1]}
map_chars = {0: ".", 1: "#", 2:"@", 3: "+", 4:"T", 5: "~"}
support_map_chars = ["#", "+", "T"]
setting_options = ["battery_cap", "drill_usage", "step_usage", "turn_usage", "mine_usage", "isThere_usage", "print_usage", "place_usage", "safeToDrill_usage", "isThere_extended"]

def consume_energy(key):
    def consume_decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.energy -= self.settings[key]
            if self.energy <= 0:
                raise MineScriptRuntimeError("E_OUT_OF_ENERGY")
            return func(self, *args, **kwargs)
        return wrapper
    return consume_decorator

class Map:
    def __init__(self, map, size, settings:dict):
        self.map = [list(lst) for lst in map]
        self.y, self.x = size
        self.player_gold_collected = 0
        self.console = []
        self.discovered = [["?" for _ in range(self.x)] for _ in range(self.y)]
        
        for y,line in enumerate(self.map):
            for x,char in enumerate(line):
                if char in player_chars.keys():
                    self.robot_x = x
                    self.robot_y = y
                    self.robot_dir = player_chars[char]
                    self.map[y][x] = "~"
                    self._discover(self.robot_x, self.robot_y)
                elif char not in map_chars.values():
                    raise BuildError("SYNTAX_ERROR", "Hiba a térkép syntaxisában!")
        self.settings = {}
        try:
            for key, val in settings.items():
                if key == "isThere_extended":
                    if type(val) is not bool or val not in ("true", "false"):
                        raise BuildError("SYNTAX_ERROR", "Hibás beállítás érték")
                    continue
                if key not in setting_options:
                    raise BuildError("SYNTAX_ERROR", "Hibás beállítás opció!")
                if int(val) < 0:
                    raise BuildError("SYNTAX_ERROR", "Hibás beállítás érték")
                self.settings[key] = int(val)
        except:
            raise BuildError("SYNTAX_ERROR", "Hibás beállítások")
        for setting in setting_options:
            if setting not in self.settings.keys():
                if setting == "battery_cap":
                    self.settings[setting] = 15
                elif setting == "isThere_extended":
                    self.settings[setting] = False
                else:
                    self.settings[setting] = 1
        self.energy = self.settings["battery_cap"]
        self.energy_capacity = self.energy

    def _getCordsInFrontOf(self):
        new_x = self.robot_dir[0] + self.robot_x
        new_y = self.robot_dir[1] + self.robot_y
        if not (0 <= new_x <self.x and 0 <= new_y < self.y):
            return [-1,-1]
        return [new_x, new_y]

    def _replace_under(self, char:str):
        self.map[self.robot_y][self.robot_x] = char
        self._discover(self.robot_x, self.robot_y)

    def _discover(self, x,y):
        self.discovered[y][x] = self.map[y][x]

    def _check_collapse(self, xin, yin):
        counter = 0
        check_iterator = [-1,0,1]
        for x in check_iterator:
            for y in check_iterator:
                if x == 0 and y == 0:
                    continue
                newx = xin + x
                newy = yin + y
                if 0 <= newy < self.y and 0 <= newx < self.x and self.map[newy][newx] not in support_map_chars:
                    counter += 1

        if counter >= 6:
            raise MineScriptRuntimeError("E_MINE_COLLAPSE")


    def get_robot_dir(self):
        dirchar = [key if val == self.robot_dir else None for key, val in player_chars.items()]
        while None in dirchar:
            dirchar.remove(None)
        return  dirchar[0]

    def get_map(self):
        new_map = [row[:] for row in self.discovered]
        new_map[self.robot_y][self.robot_x] = [key for key, val in player_chars.items() if val == self.robot_dir][0]
        return new_map

    def charge(self):
        if self.map[self.robot_y][self.robot_x] != "~":
            raise MineScriptRuntimeError("E_CANNOT_CHARGE")
        self.energy = self.energy_capacity

    @consume_energy("step_usage")
    def move(self, n):
        for _ in range(n):
            new_x, new_y = self._getCordsInFrontOf()
            if new_x < 0:
                raise MineScriptRuntimeError("E_BEDROCK_HIT")
            self._discover(new_x,new_y)
            if self.map[new_y][new_x] in ["#", "+"]:
                raise MineScriptRuntimeError("E_BEDROCK_HIT")
            self.robot_y = new_y
            self.robot_x = new_x

    @consume_energy("turn_usage")
    def turn(self, n):
        for _ in range(n):
            self.robot_dir = [self.robot_dir[1], -self.robot_dir[0]]

    @consume_energy("isThere_usage")
    def isThere(self, search_type):
        if search_type not in map_chars.keys():
            raise MineScriptRuntimeError("E_BAD_ARG")
        if not self.settings["isThere_extended"] and search_type not in (0,1,2):
            raise MineScriptRuntimeError("E_BAD_ARG")
        new_x, new_y = self._getCordsInFrontOf()
        if not new_x < 0:
            searched = self.map[new_y][new_x]
            self._discover(new_x, new_y)
        else:
            searched = "#"
        return searched == map_chars[search_type]

    @consume_energy("mine_usage")
    def mineHere(self):
        current = self.map[self.robot_y][self.robot_x]
        if current != "@":
            raise MineScriptRuntimeError("E_NO_GOLD")
        self._replace_under(".")
        self.player_gold_collected += 1

    @consume_energy("print_usage")
    def print(self, out):
        self.console.append(out)

    @consume_energy("drill_usage")
    def drill(self):
        new_x, new_y = self._getCordsInFrontOf()
        if new_x < 0:
            raise MineScriptRuntimeError("E_NOT_DRILLABLE")
        char_at_front = self.map[new_y][new_x]
        if char_at_front != "+":
            raise MineScriptRuntimeError("E_NOT_DRILLABLE")
        self.robot_x = new_x
        self.robot_y = new_y
        self._replace_under(".")
        self._check_collapse(self.robot_x, self.robot_y)

    @consume_energy("place_usage")
    def place(self):
        if self.map[self.robot_y][self.robot_x] == "~":
            raise MineScriptRuntimeError("E_CANNOT_PLACE")
        self._replace_under("T")

    @consume_energy("safeToDrill_usage")
    def safeToDrill(self):
        new_x, new_y = self._getCordsInFrontOf()
        try:
            self._check_collapse(new_x, new_y)
        except:
            return False
        return True
        
