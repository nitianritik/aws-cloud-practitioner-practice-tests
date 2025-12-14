import re
import os
import time
from datetime import datetime

# -----------------------------
# Utility: Parse exam markdown
# -----------------------------
def parse_exam(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match each question block
    pattern = re.compile(
        r"(\d+)\.\s+(.*?)\n((?:\s+-\s+[A-Z]\..*?\n)+).*?Correct answer:\s*(.+?)\s*</details>",
        re.DOTALL
    )
    matches = pattern.findall(content)

    questions = []
    for num, question, options, answer in matches:
        opts = [opt.strip() for opt in options.strip().split("\n") if opt.strip()]
        correct = [a.strip() for a in answer.split(",")]
        questions.append({
            "number": int(num),
            "question": question.strip(),
            "options": opts,
            "correct": correct
        })
    return questions


# -----------------------------
# Utility: Emoji helpers
# -----------------------------
RIGHT = "✅"
WRONG = "❌"
CLOCK = "⏱️"
STAR = "🌟"
BOOK = "📘"
FIRE = "🔥"
CHART = "📊"


# -----------------------------
# Exam runner
# -----------------------------
def run_exam(serial):
    filename = f"practice-exam-{serial}.md"
    if not os.path.exists(filename):
        print(f"❌ File '{filename}' not found.")
        return

    questions = parse_exam(filename)
    print(f"\n{BOOK} Starting Practice Exam {serial} ({len(questions)} questions)")
    print("----------------------------------------------------\n")

    total_correct = 0
    question_results = []
    start_time = time.time()

    for q in questions:
        print(f"Q{q['number']}. {q['question']}")
        for opt in q['options']:
            print(opt)

        # ⚡ NEW: show hint for multi-answer questions
        if len(q['correct']) > 1:
            print("ℹ️  This question may have multiple correct answers — separate them with commas.\n")

        q_start = time.time()
        answer = input("Your answer (e.g. A,B,...): ").strip().upper()
        q_end = time.time()

        time_taken = q_end - q_start
        answer_set = {a.strip() for a in answer.split(",") if a.strip()}
        correct_set = set(q['correct'])

        # ⚡ FIX: show correct answer immediately if wrong
        if answer_set == correct_set:
            print(f"{RIGHT}  Correct! ({CLOCK} {time_taken:.2f}s)\n")
            total_correct += 1
            result = RIGHT
        else:
            print(f"{WRONG}  Wrong. Correct answer: {', '.join(q['correct'])} ({CLOCK} {time_taken:.2f}s)\n")
            result = WRONG

        question_results.append({
            "number": q['number'],
            "result": result,
            "time_taken": time_taken,
            "your_answer": answer,
            "correct_answer": ",".join(q['correct'])
        })

    end_time = time.time()
    total_time = end_time - start_time
    total_questions = len(questions)
    total_wrong = total_questions - total_correct
    score_percent = (total_correct / total_questions) * 100

    # -----------------------------
    # Display result summary
    # -----------------------------
    print("\n" + "=" * 60)
    print(f"{CHART}  EXAM SUMMARY {CHART}")
    print("=" * 60)
    print(f"Total Questions: {total_questions}")
    print(f"Correct: {total_correct} {RIGHT}")
    print(f"Wrong: {total_wrong} {WRONG}")
    print(f"Score: {score_percent:.2f}% {STAR}")
    print(f"Total Time: {total_time:.2f} seconds {CLOCK}")
    print("\nDetailed Table:\n")

    print(f"{'Q#':<4} | {'Result':<6} | {'Time(s)':<8} | {'Your Ans':<10} | {'Correct Ans'}")
    print("-" * 60)
    for r in question_results:
        print(f"{r['number']:<4} | {r['result']:<6} | {r['time_taken']:<8.2f} | {r['your_answer']:<10} | {r['correct_answer']}")

    print("\n" + FIRE + " Great effort! Keep practicing!" + FIRE)

    # -----------------------------
    # Append results to results.txt
    # -----------------------------
    with open("results.txt", "a", encoding="utf-8") as f:
        # ⚡ FIX: convert serial safely to int for formatting
        try:
            serial_num = int(serial)
        except ValueError:
            serial_num = serial  # fallback if not numeric

        if isinstance(serial_num, int):
            f.write("\n\n" + "_" * 15 + f" EXAM {serial_num:02d} RESULTS " + "_" * 15 + "\n")
        else:
            f.write("\n\n" + "_" * 15 + f" EXAM {serial} RESULTS " + "_" * 15 + "\n")

        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Questions: {total_questions}\n")
        f.write(f"Correct: {total_correct} ✅\n")
        f.write(f"Wrong: {total_wrong} ❌\n")
        f.write(f"Score: {score_percent:.2f}% 🌟\n")
        f.write(f"Total Time: {int(total_time//60)}m {total_time%60:.2f}s ⏱️\n")
        # f.write("-" * 60 + "\n")
        # for r in question_results:
        #     f.write(f"Q{r['number']:<3} | {r['result']} | {r['time_taken']:.2f}s | Your: {r['your_answer']} | Correct: {r['correct_answer']}\n")
        # f.write("-" * 60 + "\n")

    print(f"\n📁 Results saved to results.txt\n")


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print("Welcome to the Python Exam Simulator 🎓")
    serial = input("Enter the exam serial number (e.g. 1): ").strip()
    run_exam(serial)