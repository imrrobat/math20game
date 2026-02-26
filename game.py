import random


def mixin_generate():
    n1 = random.randint(0, 16)
    n2 = random.randint(0, 16)

    op = random.choice("+-*/")

    if op == "+":
        answer = n1 + n2
        display_op = "+"
    elif op == "-":
        if n1 < n2:
            n1, n2 = n2, n1
        answer = n1 - n2
        display_op = "-"
    elif op == "*":
        answer = n1 * n2
        display_op = "x"
    else:
        answer = random.randint(1, 11)
        n2 = random.randint(1, 11)
        n1 = answer * n2
        display_op = "÷"

    return f"{n1} {display_op} {n2}", answer


def generate_question(mode="+"):
    op = mode

    if op == "+":
        n1 = random.randint(1, 21)
        n2 = random.randint(1, 21)
        answer = n1 + n2
        display_op = "+"
    elif op == "-":
        n1 = random.randint(1, 21)
        n2 = random.randint(1, 21)
        # if n1 < n2:
        #     n1, n2 = n2, n1
        answer = n1 - n2
        display_op = "-"
    elif op == "*":
        n1 = random.randint(1, 13)
        if n1 > 10:
            n2 = random.randint(1, 10)
        else:
            n2 = random.randint(1, 13)
        answer = n1 * n2
        display_op = "x"
    elif op == "/":
        answer = random.randint(1, 9)
        n2 = random.randint(1, 9)
        n1 = answer * n2
        display_op = "÷"

    return f"{n1} {display_op} {n2}", answer


def generate_options(correct_answer: int):
    options = {correct_answer}

    while len(options) < 4:
        offset = random.randint(-5, 5)
        if offset == 0:
            continue

        option = correct_answer + offset
        options.add(option)

    options = list(options)
    random.shuffle(options)
    return options
