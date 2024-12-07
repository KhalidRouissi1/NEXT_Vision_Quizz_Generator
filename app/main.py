from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
import random
import io
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from googletrans import Translator
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Models
class QuestionBase(BaseModel):
    question_text: str
    correct_answer: str
    difficulty: str
    score: int = Field(default=1, description="Question score/points")

class Question(QuestionBase):
    question_id: str = Field(default_factory=lambda: str(random.randint(1000, 9999)))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class QuizMetadata(BaseModel):
    total_questions: int
    difficulty_distribution: Dict[str, int]
    total_score: int
    estimated_time_minutes: int
    created_at: str

class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[Question]
    metadata: QuizMetadata

# Text Extraction and Translation Functions
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

# Question Generator Class
class QuestionGenerator:
    def __init__(self):
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
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
        
        difficulty = self._determine_difficulty(sentence, word_to_remove)
        
        return {
            "question_text": question_text,
            "correct_answer": word_to_remove,
            "difficulty": difficulty,
            "score": self._get_score(difficulty)
        }

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

# FastAPI Setup
app = FastAPI(
    title="Quiz Generator API",
    description="API for generating quizzes from PDF documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize question generator
question_generator = QuestionGenerator()

@app.post("/api/v1/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    file: UploadFile = File(...),
    max_questions: int = 10,
    language: str = Query("english", enum=["english", "french", "arabic", "german"])
):
    """Generate a quiz from a PDF file"""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    content = await file.read()
    
    # Extract text from PDF
    text = extract_text_from_pdf(content)
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
    
    # Translate text to the desired language
    translated_text = translate_text(text, target_language=language)
    
    # Generate questions in the selected language (e.g., English, French, etc.)
    raw_questions = question_generator.generate_questions(translated_text, max_questions)
    questions = [Question(**q) for q in raw_questions]
    
    # Calculate metadata
    difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
    total_score = 0
    
    for q in questions:
        difficulty_counts[q.difficulty] += 1
        total_score += q.score
    
    metadata = QuizMetadata(
        total_questions=len(questions),
        difficulty_distribution=difficulty_counts,
        total_score=total_score,
        estimated_time_minutes=len(questions) * 2,
        created_at=datetime.now().isoformat()
    )
    
    # Create quiz response
    quiz_response = QuizResponse(
        quiz_id=f"quiz_{random.randint(10000, 99999)}",
        questions=questions,
        metadata=metadata
    )
    
    return quiz_response

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

