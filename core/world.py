
player_chars = {"<": [-1,0], "v": [0,1], ">": [1,0], "^":[0,-1]}
map_chars = {0: ".", 1: "#", 2:"@"}

class Map:
    def __init__(self, map, size):
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
                    self._discover(x, y)  # ahol a robot áll, az felfedezett mező
                    return

    def move(self, n):
        for _ in range(n):
            new_x = self.robot_dir[0] + self.robot_x
            new_y = self.robot_dir[1] + self.robot_y
            if not(0 <= new_x < self.x and 0 <= new_y < self.y):
                return False
            if self.map[new_y][new_x] == "#":
                # Falba ütközéskor a fal NEM lesz felfedezett: a feladat szerint csak az a
                # mező az, ahol a robot járt, vagy amire isThere hívódott.
                return False
            self.robot_y = new_y
            self.robot_x = new_x
            self._discover(new_x, new_y)
        return True

    def turn(self, n):
        for _ in range(n):
            self.robot_dir = [self.robot_dir[1], -self.robot_dir[0]]

    def get_map(self):
        new_map = [row[:] for row in self.discovered]
        new_map[self.robot_y][self.robot_x] = [key for key, val in player_chars.items() if val == self.robot_dir][0]
        return new_map

    def isThere(self, search_type):
        if search_type not in (0, 1, 2):
            return "E_BAD_ARG"
        new_x = self.robot_dir[0] + self.robot_x
        new_y = self.robot_dir[1] + self.robot_y
        if 0 <= new_x < self.x and 0 <= new_y < self.y:
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
        self.map[self.robot_y][self.robot_x] = "."
        self._discover(self.robot_x, self.robot_y)  # a felfedezett térképen is eltűnik az arany
        self.player_gold_collected += 1
        return True

    def get_robot_dir(self):
        dirchar = [key if val == self.robot_dir else None for key, val in player_chars.items()]
        while None in dirchar:
            dirchar.remove(None)
        return  dirchar[0]

    def print(self, out):
        self.console.append(out)
        print(out)