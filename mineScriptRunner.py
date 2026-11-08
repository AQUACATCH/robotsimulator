from core.interpreter import ProgramRunner


def logger(logList:list, file):
    logListstr = [str(elem) for elem in logList]
    logListstr = list(map(lambda elem: elem if elem != "True" else "true", logListstr))
    logListstr = list(map(lambda elem: elem if elem != "False" else "false", logListstr))
    file.write(" ".join(logListstr) + "\n")

def runScriptQ(path, outPath):
    file_content = []
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip("\n")
            file_content.append(line)
    f.close()

    program = ProgramRunner(file_content)

    with open(outPath, "w") as outF:
        while True:
            result = program.next_step()
            if result == None:
                continue
            logger(result, outF)
            if "EOR" in result or "INSTRUCTION_COUNT_LIMIT_EXCEEDED" in result:
                break


def get_runner_object(path):
    file_content = []
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip("\n")
            file_content.append(line)
    f.close()
    return ProgramRunner(file_content)

if __name__ == "__main__":
    runScriptQ("test.txt", "out.txt")