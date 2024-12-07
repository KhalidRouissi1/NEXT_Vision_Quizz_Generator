import io
from typing import List
import PyPDF2
import random
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from googletrans import Translator

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""

def translate_text(text: str, target_language: str) -> str:
    """Translate text to the target language using Google Translate"""
    translator = Translator()
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print(f"Error during translation: {str(e)}")
        return text

class QuestionGenerator:
    def __init__(self):
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except:
            print("Warning: Could not download NLTK data")
        
        self.stop_words = set(stopwords.words('english'))

    def generate_questions(self, text: str, max_questions: int) -> List[dict]:
        sentences = sent_tokenize(text)
        if not sentences:
            return []
        
        questions = []
        for _ in range(min(max_questions, len(sentences))):
            sentence = random.choice(sentences)
            sentences.remove(sentence)
            question = self._create_question_from_sentence(sentence)
            if question:
                questions.append(question)
            if len(questions) >= max_questions:
                break
        
        return questions

    def _create_question_from_sentence(self, sentence: str) -> dict:
        sentence = sentence.strip()
        if len(sentence) < 20:
            return None
            
        words = sentence.split()
        if len(words) < 5:
            return None
            
        content_words = [w for w in words if w.lower() not in self.stop_words]
        if not content_words:
            content_words = words
            
        word_to_remove = random.choice(content_words)
        question_text = sentence.replace(word_to_remove, "________", 1)
        
        wrong_options = self._generate_wrong_options(word_to_remove)
        options = [word_to_remove] + wrong_options
        random.shuffle(options)
        
        difficulty = self._determine_difficulty(sentence, word_to_remove)
        
        return {
            "question_text": question_text,
            "options": options,
            "correct_answer": word_to_remove,
            "difficulty": difficulty,
            "score": self._get_score(difficulty)
        }

    def _generate_wrong_options(self, correct_answer: str) -> List[str]:
        wrong_options = [
            correct_answer.upper(),
            correct_answer.lower(),
            correct_answer + 's'
        ][:3]
        while len(wrong_options) < 3:
            wrong_options.append(f"Option_{len(wrong_options)+1}")
        return wrong_options

    def _determine_difficulty(self, sentence: str, correct_word: str) -> str:
        words = sentence.split()
        word_count = len(words)
        if word_count < 6:
            return "easy"
        elif word_count < 12:
            return "medium"
        else:
            return "hard"

    def _get_score(self, difficulty: str) -> int:
        if difficulty == "easy":
            return 1
        elif difficulty == "medium":
            return 2
        else:
            return 3
