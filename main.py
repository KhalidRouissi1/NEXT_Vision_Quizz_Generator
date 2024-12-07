import re
from PyPDF2 import PdfReader
from transformers import pipeline

# Step 1: Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

# Step 2: Clean and Preprocess Text
def preprocess_text(text):
    # Remove extra spaces and newlines
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    # Split into sentences
    sentences = re.split(r'(?<=[.!?]) +', cleaned_text)
    return sentences

# Step 3: Generate Questions
def generate_questions(text, difficulty="easy"):
    # Load a pre-trained question generation model
    try:
        question_generator = pipeline("text2text-generation", model="valhalla/t5-small-qg-prepend")
    except Exception as e:
        print(f"Error loading model: {e}")
        return []

    questions = []
    for sentence in text:
        try:
            # Generate question based on difficulty level
            question = question_generator(f"question: {sentence} context: {sentence}", max_length=50, num_return_sequences=1)
            if question:
                questions.append({
                    "question": question[0]['generated_text'],
                    "difficulty": difficulty
                })
        except Exception as e:
            print(f"Error generating question for sentence: {sentence}\n{e}")
    return questions

# Step 4: Classify Questions by Difficulty
def classify_questions(sentences):
    easy = [sentence for sentence in sentences if len(sentence.split()) <= 10]
    medium = [sentence for sentence in sentences if 10 < len(sentence.split()) <= 20]
    hard = [sentence for sentence in sentences if len(sentence.split()) > 20]
    return {
        "easy": generate_questions(easy, difficulty="easy"),
        "medium": generate_questions(medium, difficulty="medium"),
        "hard": generate_questions(hard, difficulty="hard")
    }

# Main Function
def main():
    # Input PDF file
    pdf_path = input("Enter the path to the PDF file: ")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("No text extracted. Please check your PDF file.")
        return

    sentences = preprocess_text(text)
    classified_questions = classify_questions(sentences)
    
    # Display Questions
    for difficulty, questions in classified_questions.items():
        print(f"\n=== {difficulty.upper()} QUESTIONS ===")
        for idx, question in enumerate(questions, 1):
            print(f"{idx}. {question['question']}")
    
    # Save questions to a file (optional)
    with open("generated_quiz.txt", "w") as f:
        for difficulty, questions in classified_questions.items():
            f.write(f"\n=== {difficulty.upper()} QUESTIONS ===\n")
            for idx, question in enumerate(questions, 1):
                f.write(f"{idx}. {question['question']}\n")
    print("\nQuiz saved to 'generated_quiz.txt'.")

if __name__ == "__main__":
    main()
