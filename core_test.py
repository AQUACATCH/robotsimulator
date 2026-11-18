from core.interpreter import ProgramRunner


if __name__ == "__main__":
    lines = []
    with open("test.txt", "r", encoding="utf-8") as fIn:
        for line in fIn.readlines():
            lines.append(line.strip("\n"))
    fIn.close()

    runner = ProgramRunner(lines)

    with open("out.txt", "w", encoding="utf-8") as fOut:
        next_log = runner.next_step()
        while "EOR" not in next_log and "INSTRUCTION_COUNT_LIMIT_EXCEEDED" not in next_log and next_log is not None:
            fOut.write(" ".join(next_log) + "\n")
            next_log = runner.next_step()
    fOut.close()