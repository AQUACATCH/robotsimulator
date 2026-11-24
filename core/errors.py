class MineScriptRuntimeError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code

class BuildError(Exception):
    def __init__(self, code, msg):
        super().__init__(code, msg)
        self.code = code
        self.msg = msg