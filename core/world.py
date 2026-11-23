from .interpreter import MineScriptRuntimeError, BuildError
from functools import wraps

player_chars = {"<": [-1,0], "v": [0,1], ">": [1,0], "^":[0,-1]}
map_chars = {0: ".", 1: "#", 2:"@", 3: "+", 4:"T", 5: "~"}
setting_options = ["battery_cap", "drill_usage", "step_usage", "turn_usage", "mine_usage", "isTher_usage", "print_usage"]

def consume_energy(val): #Valszeg ez a megoldás nem fog működni
    def consume_decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.energy -= val
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
                    self.map[y][x] = "."
                    self._discover(self.robot_x, self.robot_y)
                elif char not in map_chars.values():
                    raise BuildError("SYNTAX_ERROR", "Hiba a térkép syntaxisában!")
        self.settings = {}
        for key, val in settings.items():
            if key not in setting_options:
                raise BuildError("SYNTAX_ERROR", "Hibás beállítás opció!")
            if not val.isDecimal() and int(val) < 0:
                raise BuildError("SYNTAX_ERROR", "Hibás beállítás érték")
            self.settings[key] = int(val)
        for setting in setting_options:
            if setting not in self.settings.keys():
                if setting == "battery_cap":
                    settings[setting] = 15
                else:
                    settings[setting] = 1
        self.energy = self.settings["battery_cap"]

    def _getCordsInFrontOf(self):
        new_x = self.robot_dir[0] + self.robot_x
        new_y = self.robot_dir[1] + self.robot_y
        if not (0 <= new_x <self.x and 0 <= new_y < self.y):
            return [-1,-1]
        return [new_x, new_y]

    def _replace_under(self, char:str):
        self.map[self.robot_y][self.robot_x] = char

    def move(self, n):
        for _ in range(n):
            new_x, new_y = self._getCordsInFrontOf()
            if new_x < 0:
                return False
            self._discover(new_x,new_y)
            if self.map[new_y][new_x] == "#":
                return False
            self.robot_y = new_y
            self.robot_x = new_x
        return True

    def turn(self, n):
        for _ in range(n):
            self.robot_dir = [self.robot_dir[1], -self.robot_dir[0]]

    def get_map(self):
        new_map = [row[:] for row in self.discovered]
        new_map[self.robot_y][self.robot_x] = [key for key, val in player_chars.items() if val == self.robot_dir][0]
        return new_map

    def isThere(self, search_type):
        if search_type not in map_chars.keys():
            raise MineScriptRuntimeError("E_BAD_ARG")
        new_x, new_y = self._getCordsInFrontOf()
        if not new_x < 0:
            searched = self.map[new_y][new_x]
            self._discover(new_x, new_y)
        else:
            searched = "#"
        return searched == map_chars[search_type]

    def _discover(self, x,y):
        self.discovered[y][x] = self.map[y][x]

    def mineHere(self):
        current = self.map[self.robot_y][self.robot_x]
        if current != "@":
            return False
        self._replace_under(".")
        self.player_gold_collected += 1
        return True

    def get_robot_dir(self):
        dirchar = [key if val == self.robot_dir else None for key, val in player_chars.items()]
        while None in dirchar:
            dirchar.remove(None)
        return  dirchar[0]

    def print(self, out):
        self.console.append(out)

    def drill(self):
        if not self.isThere(3):
            raise MineScriptRuntimeError("E_NOT_DRILLABLE")
        self.move(1)
        self._replace_under(".")
        
        
        
