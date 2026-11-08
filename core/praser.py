
operators = ["+", "-", "*", "=", "<>", "<", "<=", ">", ">="]
ident = [
    "and", "by", "else", "false", "forward", "here", "if",
    "isThere", "mine", "not", "or", "print", "set", "step",
    "to", "true", "turn", "while"
]

starter_comm_syntax_map = {
        "step": ["forward", "simpleval"], 
        "turn": ["by", "simpleval"], 
        "mine": ["here"], 
        "print": ["simpleval"], 
        "set": ["ident","to", "calculatedval"], 
        "if": ["simpleval"],
        "else": [], 
        "while": ["simpleval"]
    }

def calculatedValue(rem_tokens):
    length = len(rem_tokens)
    if length == 1:
        return {"type": "simple", "value": rem_tokens[0]}
    elif length == 2 and ("not" in rem_tokens or "isThere" in rem_tokens):
        return {"type": "unop", "operator": rem_tokens[0], "value": rem_tokens[1]}
    elif length == 3 and rem_tokens[1] in ["and", "or", *operators]:
        return {"type": "binop", "operator": rem_tokens[1], "value1": rem_tokens[0], "value2": rem_tokens[2]}
    else:
        return "SYNTAX_ERROR"

        

def parse_map(data: list[str]):
    [y,x] = data.pop(0).split(" ")
    map: list[str] = []
    for _ in range(int(y)):
        map.append(data.pop(0).strip())

    return [data, map, [int(y),int(x)]]


def parse_code(line: str,):
    # Szétbontja tokenekre a fáljt pl.: ha a felhasználó így szeretné írni if 5=asd
    # akkor enélkül errort adna
    new_line = []
    for word in line.strip("\n").split(" "):
        new_word = ""
        if word in ident or word in operators:
            new_line.append(word)
            continue
        skip_next = False
        for index, char in enumerate(word):
            if skip_next:
                skip_next = False
                continue
            if char in operators:
                new_line.append(new_word)
                new_word = char
                if len(word) > index+1:
                    if char == "<" and (word[index+1] == ">" or word[index+1] == "="):
                        new_word += word[index+1]
                        skip_next = True
                    elif char == ">" and word[index+1] == "=":
                        new_word += word[index+1]
                        skip_next = True
                new_line.append(new_word)
                new_word = ""
            else:
                new_word += char
        new_line.append(new_word)

    indent_length = 0
    for token in new_line:
        if token == '':
            indent_length += 1
        else: break
    while '' in new_line:
        new_line.remove('')

    if len(new_line) == 0: return None

    parsed_line = {}

    first_token = new_line.pop(0)
    parsed_line["indent_level"] = indent_length
    if not first_token in starter_comm_syntax_map.keys():
        parsed_line["type"] = "error"
        parsed_line["err"] = "SYNTAX_ERROR"
        return parsed_line

    parsed_line["type"] = first_token
    if first_token in ["while", "if", "else"]:
        parsed_line["block"] = []

    for token in starter_comm_syntax_map[first_token]:
        next_token = new_line.pop(0)
        match token:
            case "simpleval":
                parsed_line["value"] = next_token
            case "ident":
                parsed_line["identifier"] = next_token
            case "calculatedval":
                ret = calculatedValue([next_token, *new_line])
                if ret == "SYNTAX_ERROR":
                    parsed_line["type"] = "error"
                    parsed_line["err"] = "SYNTAX_ERROR"
                    return parsed_line
                parsed_line["calcvalue"] = ret
                return parsed_line
            case _:
                if next_token == token:
                    continue
                else:
                    parsed_line["type"] = "error"
                    parsed_line["err"] = "SYNTAX_ERROR"
                    return parsed_line
    return parsed_line

def indent_code(lines: list[str]):

    def block_sequence(start_index, indentation):
        items = []
        k = start_index
        while k < len(lines):
            node = lines[k]
            level = node['indent_level']
            if level < indentation:
                break
            if level != indentation:
                raise ValueError('Hibás tagolás')
            if node['type'] == 'else':
                raise ValueError('Egyedül álló else')
            k += 1
            if node['type'] in ('if', 'while'):
                if k < len(lines) and lines[k]['indent_level'] > level:
                    node['block'], k = block_sequence(k, lines[k]['indent_level'])
                if node['type'] == 'if' and k < len(lines):
                    next_node = lines[k]
                    if next_node['type'] == 'else' and next_node['indent_level'] == level:
                        node['else_line'] = next_node['index']
                        node['else_block'] = []
                        k += 1
                        if k < len(lines) and lines[k]['indent_level'] > level:
                            node['else_block'], k = block_sequence(k, lines[k]['indent_level'])
            items.append(node)
        return items, k

    tree, end = block_sequence(0, 0)
    if end != len(lines):
        raise ValueError('Nem fordított kód')
    return tree
