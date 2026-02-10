import random
import time

TOTAL_QUESTIONS = 20
correct = 0
wrong = 0

questions = []

for i in range(TOTAL_QUESTIONS):
    n1 = random.randint(0, 9)
    n2 = random.randint(0, 9)
    op = random.choice("+-")

    if op == "-" and n1 < n2:
        n1, n2 = n2, n1

    if op == "+":
        answer = n1 + n2
    else:
        answer = n1 - n2

    questions.append((f"{n1} {op} {n2}", answer))

print("Game Started...!")

start_time = time.time()
for i, (q, ans) in enumerate(questions, start=1):
    user_input = input(f"{q} = ")

    try:
        user_answer = int(user_input)
    except ValueError:
        wrong += 1
        continue

    if user_answer == ans:
        correct += 1
    else:
        wrong += 1

end_time = time.time()
total_time = round(end_time - start_time, 2)
score = (correct * 100) - (wrong * 50) - int(total_time * 2)


print("🎯 Final Result")
print(f"Correct: {correct}")
print(f"Wrong: {wrong}")
print(f"in {total_time} sec")
print("-------------------")
print(f"Score: {score}")
