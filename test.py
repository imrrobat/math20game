import random

quiz = {}

for i in range(20):
    n1 = random.randint(0, 9)
    n2 = random.randint(0, 9)
    op = random.choice("+-")

    if op == "-" and n1 < n2:
        n1, n2 = n2, n1

    math = f"{n1}{op}{n2}"
    quiz[math] = eval(math)

for q, ans in quiz.items():
    print(f"{q} = {ans}")
