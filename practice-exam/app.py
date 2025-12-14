from flask import Flask, render_template, request, jsonify, session
import re
import os
import time
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'aws-exam-simulator-secret-key-2024'  # Change this in production

# In-memory store for exam data (to avoid cookie size limits)
exam_sessions = {}

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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_exam', methods=['POST'])
def start_exam():
    data = request.json
    serial = data.get('serial', '').strip()
    
    filename = f"practice-exam-{serial}.md"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': f"File '{filename}' not found."}), 404
    
    questions = parse_exam(filepath)
    
    # Generate unique session ID
    exam_session_id = str(uuid.uuid4())
    
    # Store exam data in server-side memory (not in session cookie)
    exam_sessions[exam_session_id] = {
        'exam_serial': serial,
        'questions': questions,
        'answers': {},  # Store user answers: {question_num: [selected_options]}
        'start_time': time.time(),
        'question_times': {}  # Store time taken per question
    }
    
    # Only store minimal data in session cookie
    session['exam_session_id'] = exam_session_id
    
    return jsonify({
        'success': True,
        'total_questions': len(questions),
        'serial': serial
    })


@app.route('/get_question/<int:question_num>')
def get_question(question_num):
    exam_session_id = session.get('exam_session_id')
    if not exam_session_id or exam_session_id not in exam_sessions:
        return jsonify({'error': 'No exam started'}), 400
    
    exam_data = exam_sessions[exam_session_id]
    questions = exam_data['questions']
    
    if question_num < 1 or question_num > len(questions):
        return jsonify({'error': 'Invalid question number'}), 400
    
    question = questions[question_num - 1]
    is_multiple = len(question['correct']) > 1
    
    # Get saved answer if exists
    saved_answer = exam_data.get('answers', {}).get(question_num, [])
    
    return jsonify({
        'question': question,
        'is_multiple': is_multiple,
        'saved_answer': saved_answer,
        'correct_answers': question['correct'],  # Include correct answers for checking
        'current_question': question_num,
        'total_questions': len(questions)
    })


@app.route('/save_answer', methods=['POST'])
def save_answer():
    exam_session_id = session.get('exam_session_id')
    if not exam_session_id or exam_session_id not in exam_sessions:
        return jsonify({'error': 'No exam started'}), 400
    
    data = request.json
    question_num = data.get('question_num')
    selected_options = data.get('selected_options', [])
    time_taken = data.get('time_taken', 0)
    
    exam_data = exam_sessions[exam_session_id]
    exam_data['answers'][question_num] = selected_options
    exam_data['question_times'][question_num] = time_taken
    
    return jsonify({'success': True})


@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    exam_session_id = session.get('exam_session_id')
    if not exam_session_id or exam_session_id not in exam_sessions:
        return jsonify({'error': 'No exam data found'}), 400
    
    exam_data = exam_sessions[exam_session_id]
    questions = exam_data['questions']
    user_answers = exam_data.get('answers', {})
    question_times = exam_data.get('question_times', {})
    start_time = exam_data.get('start_time', time.time())
    exam_serial = exam_data.get('exam_serial', '')
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate results
    total_correct = 0
    question_results = []
    
    for q in questions:
        q_num = q['number']
        user_answer_set = set(user_answers.get(q_num, []))
        correct_set = set(q['correct'])
        
        is_correct = user_answer_set == correct_set
        if is_correct:
            total_correct += 1
        
        time_taken = question_times.get(q_num, 0)
        user_answer_str = ",".join(sorted(user_answers.get(q_num, []))) if user_answers.get(q_num) else ""
        correct_answer_str = ",".join(sorted(q['correct']))
        
        question_results.append({
            "number": q_num,
            "result": "✅" if is_correct else "❌",
            "time_taken": time_taken,
            "your_answer": user_answer_str,
            "correct_answer": correct_answer_str,
            "question": q['question'],
            "options": q['options']
        })
    
    total_questions = len(questions)
    total_wrong = total_questions - total_correct
    score_percent = (total_correct / total_questions) * 100
    
    # Save to results.txt
    results_file = os.path.join(os.path.dirname(__file__), 'results.txt')
    with open(results_file, 'a', encoding='utf-8') as f:
        try:
            serial_num = int(exam_serial)
            f.write("\n\n" + "_" * 15 + f" EXAM {serial_num:02d} RESULTS " + "_" * 15 + "\n")
        except ValueError:
            f.write("\n\n" + "_" * 15 + f" EXAM {exam_serial} RESULTS " + "_" * 15 + "\n")
        
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Questions: {total_questions}\n")
        f.write(f"Correct: {total_correct} ✅\n")
        f.write(f"Wrong: {total_wrong} ❌\n")
        f.write(f"Score: {score_percent:.2f}% 🌟\n")
        f.write(f"Total Time: {int(total_time//60)}m {total_time%60:.2f}s ⏱️\n")
    
    # Save to exams-given.txt
    exams_given_file = os.path.join(os.path.dirname(__file__), 'exams-given.txt')
    with open(exams_given_file, 'a', encoding='utf-8') as f:
        f.write(f"\nWelcome to the Python Exam Simulator 🎓\n")
        f.write(f"Enter the exam serial number (e.g. 1): {exam_serial}\n\n")
        f.write(f"📘 Starting Practice Exam {exam_serial} ({total_questions} questions)\n")
        f.write("-" * 50 + "\n\n")
        
        for r in question_results:
            f.write(f"Q{r['number']}. {r['question']}\n")
            for opt in r['options']:
                f.write(f"{opt}\n")
            
            # Check if multiple choice
            correct_count = len([c for c in r['correct_answer'].split(',') if c.strip()])
            if correct_count > 1:
                f.write("ℹ️  This question may have multiple correct answers — separate them with commas.\n\n")
            
            f.write(f"Your answer (e.g. A,B,...): {r['your_answer']}\n")
            if r['result'] == "✅":
                f.write(f"✅  Correct! (⏱️ {r['time_taken']:.2f}s)\n\n")
            else:
                f.write(f"❌  Wrong. Correct answer: {r['correct_answer']} (⏱️ {r['time_taken']:.2f}s)\n\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"📊  EXAM SUMMARY 📊\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total Questions: {total_questions}\n")
        f.write(f"Correct: {total_correct} ✅\n")
        f.write(f"Wrong: {total_wrong} ❌\n")
        f.write(f"Score: {score_percent:.2f}% 🌟\n")
        f.write(f"Total Time: {total_time:.2f} seconds ⏱️\n\n")
    
    # Clean up: remove exam data from memory and clear session
    if exam_session_id in exam_sessions:
        del exam_sessions[exam_session_id]
    session.clear()
    
    return jsonify({
        'success': True,
        'results': {
            'total_questions': total_questions,
            'total_correct': total_correct,
            'total_wrong': total_wrong,
            'score_percent': score_percent,
            'total_time': total_time,
            'question_results': question_results
        }
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)

