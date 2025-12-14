let currentQuestion = 1;
let totalQuestions = 0;
let examStarted = false;
let timerInterval = null;
let timeRemaining = 90 * 60; // 90 minutes in seconds
let questionStartTime = null;
let currentCorrectAnswers = []; // Store correct answers for current question
let answerChecked = false; // Track if answer has been checked

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('start-exam-btn').addEventListener('click', startExam);
    document.getElementById('prev-btn').addEventListener('click', goToPrevious);
    document.getElementById('next-btn').addEventListener('click', goToNext);
    document.getElementById('check-btn').addEventListener('click', checkAnswer);
    document.getElementById('submit-exam-btn').addEventListener('click', submitExam);
    document.getElementById('restart-btn').addEventListener('click', restartExam);
    
    // Allow Enter key to start exam
    document.getElementById('exam-number').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            startExam();
        }
    });
});

function startExam() {
    const examNumber = document.getElementById('exam-number').value.trim();
    const errorMsg = document.getElementById('error-message');
    
    if (!examNumber) {
        errorMsg.textContent = 'Please enter an exam number';
        errorMsg.classList.add('show');
        return;
    }
    
    errorMsg.classList.remove('show');
    
    fetch('/start_exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ serial: examNumber })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            errorMsg.textContent = data.error;
            errorMsg.classList.add('show');
            return;
        }
        
        totalQuestions = data.total_questions;
        examStarted = true;
        currentQuestion = 1;
        timeRemaining = 90 * 60;
        
        // Show exam screen
        document.getElementById('welcome-screen').classList.add('hidden');
        document.getElementById('exam-screen').classList.remove('hidden');
        
        // Start timer
        startTimer();
        
        // Load first question
        loadQuestion(1);
    })
    .catch(error => {
        errorMsg.textContent = 'Error starting exam: ' + error.message;
        errorMsg.classList.add('show');
    });
}

function startTimer() {
    updateTimerDisplay();
    timerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            alert('Time is up! Submitting exam...');
            submitExam();
        } else if (timeRemaining <= 300) { // 5 minutes warning
            document.getElementById('timer').classList.add('warning');
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    document.getElementById('timer').textContent = 
        `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function loadQuestion(questionNum) {
    questionStartTime = Date.now();
    answerChecked = false; // Reset check status for new question
    
    fetch(`/get_question/${questionNum}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            const question = data.question;
            const isMultiple = data.is_multiple;
            const savedAnswer = data.saved_answer || [];
            currentCorrectAnswers = data.correct_answers || []; // Store correct answers
            
            // Update question counter
            document.getElementById('question-counter').textContent = 
                `Question ${questionNum} of ${totalQuestions}`;
            
            // Update question text
            document.getElementById('question-text').textContent = 
                `Q${questionNum}. ${question.question}`;
            
            // Show/hide hint for multiple choice
            const hintDiv = document.getElementById('question-hint');
            if (isMultiple) {
                hintDiv.textContent = 'ℹ️  This question may have multiple correct answers — select all that apply.';
                hintDiv.classList.remove('hidden');
            } else {
                hintDiv.classList.add('hidden');
            }
            
            // Reset check button
            const checkBtn = document.getElementById('check-btn');
            checkBtn.disabled = false;
            checkBtn.textContent = 'Check Answer';
            
            // Render options
            const optionsContainer = document.getElementById('options-container');
            optionsContainer.innerHTML = '';
            
            question.options.forEach((option, index) => {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'option-item';
                
                const inputType = isMultiple ? 'checkbox' : 'radio';
                const inputName = isMultiple ? `option-${questionNum}` : 'option';
                // Extract letter from option (e.g., "- A. AWS CLI." -> "A")
                const optionMatch = option.match(/[A-Z]\./);
                const optionLetter = optionMatch ? optionMatch[0].replace('.', '') : String.fromCharCode(65 + index);
                
                const input = document.createElement('input');
                input.type = inputType;
                input.name = inputName;
                input.value = optionLetter;
                input.id = `option-${questionNum}-${index}`;
                
                if (savedAnswer.includes(optionLetter)) {
                    input.checked = true;
                    optionDiv.classList.add('selected');
                }
                
                const label = document.createElement('label');
                label.htmlFor = `option-${questionNum}-${index}`;
                label.textContent = option;
                
                input.addEventListener('change', function() {
                    saveAnswer(questionNum);
                    updateOptionSelection(optionDiv, input.checked);
                });
                
                optionDiv.addEventListener('click', function(e) {
                    if (e.target !== input) {
                        input.checked = !input.checked;
                        saveAnswer(questionNum);
                        updateOptionSelection(optionDiv, input.checked);
                    }
                });
                
                optionDiv.appendChild(input);
                optionDiv.appendChild(label);
                optionsContainer.appendChild(optionDiv);
            });
            
            // Clear any previous check styling
            clearCheckStyling();
            
            // Update navigation buttons
            document.getElementById('prev-btn').disabled = questionNum === 1;
            
            if (questionNum === totalQuestions) {
                document.getElementById('next-btn').classList.add('hidden');
                document.getElementById('submit-exam-btn').classList.remove('hidden');
            } else {
                document.getElementById('next-btn').classList.remove('hidden');
                document.getElementById('submit-exam-btn').classList.add('hidden');
            }
        })
        .catch(error => {
            alert('Error loading question: ' + error.message);
        });
}

function updateOptionSelection(optionDiv, isChecked) {
    if (isChecked) {
        optionDiv.classList.add('selected');
    } else {
        optionDiv.classList.remove('selected');
    }
}

function saveAnswer(questionNum) {
    const isMultiple = document.getElementById('question-hint').classList.contains('hidden') === false;
    const inputType = isMultiple ? 'checkbox' : 'radio';
    const inputName = isMultiple ? `option-${questionNum}` : 'option';
    
    const selectedOptions = [];
    const inputs = document.querySelectorAll(`input[name="${inputName}"]:checked`);
    inputs.forEach(input => {
        selectedOptions.push(input.value);
    });
    
    const timeTaken = (Date.now() - questionStartTime) / 1000;
    
    fetch('/save_answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question_num: questionNum,
            selected_options: selectedOptions,
            time_taken: timeTaken
        })
    })
    .catch(error => {
        console.error('Error saving answer:', error);
    });
}

function goToPrevious() {
    if (currentQuestion > 1) {
        saveAnswer(currentQuestion);
        currentQuestion--;
        loadQuestion(currentQuestion);
    }
}

function checkAnswer() {
    const isMultiple = document.getElementById('question-hint').classList.contains('hidden') === false;
    const inputName = isMultiple ? `option-${currentQuestion}` : 'option';
    const selectedInputs = document.querySelectorAll(`input[name="${inputName}"]:checked`);
    const selectedOptions = Array.from(selectedInputs).map(input => input.value);
    
    if (selectedOptions.length === 0) {
        alert('Please select an answer before checking.');
        return;
    }
    
    answerChecked = true;
    
    // Get all option items
    const optionItems = document.querySelectorAll('.option-item');
    
    optionItems.forEach(optionItem => {
        const input = optionItem.querySelector('input');
        const optionLetter = input.value;
        const isSelected = input.checked;
        const isCorrect = currentCorrectAnswers.includes(optionLetter);
        
        // Remove previous styling
        optionItem.classList.remove('correct', 'incorrect', 'correct-not-selected');
        
        if (isSelected && isCorrect) {
            // User selected a correct answer - green
            optionItem.classList.add('correct');
        } else if (isSelected && !isCorrect) {
            // User selected a wrong answer - red
            optionItem.classList.add('incorrect');
        } else if (!isSelected && isCorrect) {
            // Correct answer that user didn't select - show in green but dimmed
            optionItem.classList.add('correct-not-selected');
        }
    });
    
    // Disable check button after checking
    const checkBtn = document.getElementById('check-btn');
    checkBtn.disabled = true;
    checkBtn.textContent = 'Answer Checked';
}

function clearCheckStyling() {
    const optionItems = document.querySelectorAll('.option-item');
    optionItems.forEach(item => {
        item.classList.remove('correct', 'incorrect', 'correct-not-selected');
    });
}

function goToNext() {
    if (currentQuestion < totalQuestions) {
        saveAnswer(currentQuestion);
        currentQuestion++;
        loadQuestion(currentQuestion);
    }
}

function submitExam() {
    if (!confirm('Are you sure you want to submit the exam? You cannot change answers after submission.')) {
        return;
    }
    
    saveAnswer(currentQuestion);
    
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    
    fetch('/submit_exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error submitting exam: ' + data.error);
            return;
        }
        
        showResults(data.results);
    })
    .catch(error => {
        alert('Error submitting exam: ' + error.message);
    });
}

function showResults(results) {
    // Hide exam screen, show results screen
    document.getElementById('exam-screen').classList.add('hidden');
    document.getElementById('results-screen').classList.remove('hidden');
    
    // Update summary
    document.getElementById('total-questions').textContent = results.total_questions;
    document.getElementById('total-correct').textContent = `${results.total_correct} ✅`;
    document.getElementById('total-wrong').textContent = `${results.total_wrong} ❌`;
    document.getElementById('score-percent').textContent = `${results.score_percent.toFixed(2)}% 🌟`;
    
    // Format total time
    const minutes = Math.floor(results.total_time / 60);
    const seconds = (results.total_time % 60).toFixed(2);
    document.getElementById('total-time').textContent = `${minutes}m ${seconds}s ⏱️`;
    
    // Populate detailed results table
    const tbody = document.getElementById('results-tbody');
    tbody.innerHTML = '';
    
    results.question_results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.number}</td>
            <td>${result.result}</td>
            <td>${result.time_taken.toFixed(2)}</td>
            <td>${result.your_answer || 'No answer'}</td>
            <td>${result.correct_answer}</td>
        `;
        tbody.appendChild(row);
    });
}

function restartExam() {
    // Reset everything
    currentQuestion = 1;
    totalQuestions = 0;
    examStarted = false;
    timeRemaining = 90 * 60;
    
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    // Show welcome screen
    document.getElementById('results-screen').classList.add('hidden');
    document.getElementById('welcome-screen').classList.remove('hidden');
    document.getElementById('exam-number').value = '';
    document.getElementById('error-message').classList.remove('show');
}

