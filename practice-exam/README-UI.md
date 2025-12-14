# AWS Practice Exam Simulator - Web UI

A modern web-based interface for taking AWS Cloud Practitioner practice exams.

## Features

- 🎓 Beautiful, modern UI design
- ⏱️ 90-minute countdown timer
- 📝 Single and multiple choice question support
- 🔄 Navigate between questions with Previous/Next buttons
- 📊 Detailed results with score breakdown
- 💾 Automatic saving to `results.txt` and `exams-given.txt`

## Setup

1. Install Flask (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. Enter the exam number (e.g., 1, 2, 3, etc.)
2. Click "Start Exam"
3. Answer questions using radio buttons (single choice) or checkboxes (multiple choice)
4. Use Previous/Next buttons to navigate
5. Click "Submit Exam" when finished
6. View your results and detailed breakdown

## File Structure

```
practice-exam/
├── app.py                 # Flask backend
├── templates/
│   └── index.html        # Main UI template
├── static/
│   ├── style.css         # Styling
│   └── script.js         # JavaScript logic
├── requirements.txt      # Python dependencies
└── practice-exam-*.md    # Exam question files
```

## Notes

- The timer will automatically submit the exam when time runs out
- Answers are saved as you navigate between questions
- Results are automatically appended to `results.txt` and `exams-given.txt`
- The exam format matches the original command-line version

