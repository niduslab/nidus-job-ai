from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import Optional
from cover_letter_agent import CoverLetterAgent
from career_objective_agent import CareerObjectiveAgent
import time
import json
import re
import logging
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Cover Letter & Career Objective Generator API", 
    version="1.0.0",
    description="Professional AI-powered cover letter and career objective generation"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer(auto_error=False)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load data files with error handling
def load_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info(f"Successfully loaded {len(data)} items from {filename}")
            return data
    except FileNotFoundError:
        logger.error(f"File {filename} not found")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filename}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error loading {filename}: {str(e)}")
        return []

user_profiles = load_json_file('user_profiles.json')
jobs = load_json_file('jobs.json')

# Input validation and sanitization
def sanitize_text(text: str) -> str:
    """Remove potentially harmful content from user input"""
    if not text:
        return ""
    # Remove script tags and other potentially harmful content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text.strip()

# Enhanced input schemas with validation
class CandidateInfo(BaseModel):
    Name: str
    Email: str
    Phone: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Date: Optional[str] = None

    @validator('Name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return sanitize_text(v)

    @validator('Email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    job_desc: str
    cv_text: str
    candidate_info: CandidateInfo
    llm_name: str = "ollama"
    model_name: str = "llama3.1:latest"

    @validator('job_title', 'company_name', 'job_desc', 'cv_text')
    def validate_text_fields(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Field must be at least 5 characters long')
        if len(v) > 5000:
            raise ValueError('Field too long (max 5000 characters)')
        return sanitize_text(v)

    @validator('llm_name')
    def validate_llm_name(cls, v):
        if v not in ['openai', 'ollama']:
            raise ValueError('llm_name must be either "openai" or "ollama"')
        return v

class CareerObjectiveRequest(BaseModel):
    job_title: str
    company_name: str
    job_desc: str
    cv_text: str
    current_objective: Optional[str] = None
    llm_name: str = "ollama"
    model_name: str = "llama3.1:latest"

    @validator('job_title', 'company_name', 'job_desc', 'cv_text')
    def validate_text_fields(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Field must be at least 5 characters long')
        if len(v) > 5000:
            raise ValueError('Field too long (max 5000 characters)')
        return sanitize_text(v)

    @validator('current_objective')
    def validate_current_objective(cls, v):
        if v and len(v) > 1000:
            raise ValueError('Current objective too long (max 1000 characters)')
        return sanitize_text(v) if v else None

    @validator('llm_name')
    def validate_llm_name(cls, v):
        if v not in ['openai', 'ollama']:
            raise ValueError('llm_name must be either "openai" or "ollama"')
        return v

class QuickCoverLetterRequest(BaseModel):
    user_id: str
    job_id: str
    llm_name: str = "ollama"
    model_name: str = "llama3.1:latest"

    @validator('user_id', 'job_id')
    def validate_ids(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid ID format')
        return v

    @validator('llm_name')
    def validate_llm_name(cls, v):
        if v not in ['openai', 'ollama']:
            raise ValueError('llm_name must be either "openai" or "ollama"')
        return v

class QuickCareerObjectiveRequest(BaseModel):
    user_id: str
    job_id: str
    llm_name: str = "ollama"
    model_name: str = "llama3.1:latest"

    @validator('user_id', 'job_id')
    def validate_ids(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid ID format')
        return v

    @validator('llm_name')
    def validate_llm_name(cls, v):
        if v not in ['openai', 'ollama']:
            raise ValueError('llm_name must be either "openai" or "ollama"')
        return v

# Response models
class CoverLetterResponse(BaseModel):
    cover_letter: str
    processing_time: Optional[float] = None

class CareerObjectiveResponse(BaseModel):
    career_objective: str
    processing_time: Optional[float] = None

# Middleware for logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add timing header
        response.headers["X-Process-Time"] = str(round(process_time, 3))
        
        # Log response
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed after {process_time:.3f}s: {str(e)}")
        raise

# Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        return None  
    return credentials

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Cover Letter & Career Objective Generator API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "cover_letters": {
                "manual": "/generate",
                "quick": "/generate-quick"
            },
            "career_objectives": {
                "manual": "/generate-objective",
                "quick": "/generate-objective-quick"
            },
            "data": {
                "users": "/users",
                "jobs": "/jobs"
            },
            "monitoring": {
                "health": "/health",
                "docs": "/docs"
            }
        },
        "loaded_data": {
            "users": len(user_profiles),
            "jobs": len(jobs)
        }
    }

# COVER LETTER ENDPOINTS
@app.post("/generate", response_model=CoverLetterResponse)
@limiter.limit("5/minute")
async def generate_cover_letter(request: Request, req: CoverLetterRequest, token=Depends(verify_token)):
    start_time = time.time()
    
    try:
        logger.info(f"Generating cover letter for {req.candidate_info.Name}")
        
        agent = CoverLetterAgent(
            llm_name=req.llm_name,
            model_name=req.model_name,
        )
        
        letter = agent.generate(
            cv_text=req.cv_text,
            job_title=req.job_title,
            company_name=req.company_name,
            job_desc=req.job_desc,
            candidate_info=req.candidate_info.model_dump(),
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Cover letter generated successfully in {processing_time:.3f}s")
        
        return CoverLetterResponse(
            cover_letter=letter,
            processing_time=processing_time
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@app.post("/generate-quick", response_model=CoverLetterResponse)
@limiter.limit("10/minute")
async def generate_quick_cover_letter(request: Request, req: QuickCoverLetterRequest, token=Depends(verify_token)):
    start_time = time.time()
    
    try:
        # Find user profile
        user = next((u for u in user_profiles if u['user_id'] == req.user_id), None)
        if not user:
            logger.warning(f"User not found: {req.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find job
        job = next((j for j in jobs if j.get('id') == req.job_id), None)
        if not job:
            logger.warning(f"Job not found: {req.job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Prepare candidate info
        candidate_info = {
            "Name": user['name'],
            "Email": user['email'],
            "Phone": user.get('phone', ''),
            "City": user.get('city', ''),
            "Country": user.get('country', ''),
            "Date": datetime.now().strftime("%B %d, %Y")
        }
        
        logger.info(f"Generating quick cover letter for user {req.user_id}, job {req.job_id}")
        
        # Generate cover letter
        agent = CoverLetterAgent(
            llm_name=req.llm_name,
            model_name=req.model_name,
        )
        
        letter = agent.generate(
            cv_text=user['cv_text'],
            job_title=job.get('title', 'Position'),
            company_name=job.get('company_name', 'Company'),
            job_desc=job.get('description', job.get('job_desc', '')),
            candidate_info=candidate_info,
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Quick cover letter generated successfully in {processing_time:.3f}s")
        
        return CoverLetterResponse(
            cover_letter=letter,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quick cover letter: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

# CAREER OBJECTIVE ENDPOINTS
@app.post("/generate-objective", response_model=CareerObjectiveResponse, tags=["Career Objectives"])
@limiter.limit("10/minute")
async def generate_career_objective(request: Request, req: CareerObjectiveRequest, token=Depends(verify_token)):
    start_time = time.time()
    
    try:
        logger.info(f"Generating career objective for {req.job_title} at {req.company_name}")
        
        agent = CareerObjectiveAgent(
            llm_name=req.llm_name,
            model_name=req.model_name,
        )
        
        objective = agent.generate(
            cv_text=req.cv_text,
            job_title=req.job_title,
            company_name=req.company_name,
            job_desc=req.job_desc,
            current_objective=req.current_objective,
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Career objective generated successfully in {processing_time:.3f}s")
        
        return CareerObjectiveResponse(
            career_objective=objective,
            processing_time=processing_time
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating career objective: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@app.post("/generate-objective-quick", response_model=CareerObjectiveResponse, tags=["Career Objectives"])
@limiter.limit("15/minute")
async def generate_quick_career_objective(request: Request, req: QuickCareerObjectiveRequest, token=Depends(verify_token)):
    start_time = time.time()
    
    try:
        # Find user profile
        user = next((u for u in user_profiles if u['user_id'] == req.user_id), None)
        if not user:
            logger.warning(f"User not found: {req.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find job
        job = next((j for j in jobs if j.get('id') == req.job_id), None)
        if not job:
            logger.warning(f"Job not found: {req.job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Generating quick career objective for user {req.user_id}, job {req.job_id}")
        
        # Generate career objective
        agent = CareerObjectiveAgent(
            llm_name=req.llm_name,
            model_name=req.model_name,
        )
        
        objective = agent.generate(
            cv_text=user['cv_text'],
            job_title=job.get('title', 'Position'),
            company_name=job.get('company_name', 'Company'),
            job_desc=job.get('description', job.get('job_desc', '')),
            current_objective=user.get('career_objective', None),
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Quick career objective generated successfully in {processing_time:.3f}s")
        
        return CareerObjectiveResponse(
            career_objective=objective,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quick career objective: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

# Health check endpoint
@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "loaded_users": len(user_profiles),
        "loaded_jobs": len(jobs),
        "features": ["cover_letters", "career_objectives"],
        "api_version": "1.0.0"
    }

@app.get("/users", tags=["Data"])
@limiter.limit("30/minute")
async def get_users(request: Request):
    try:
        return {
            "users": [
                {
                    "user_id": u["user_id"], 
                    "name": u["name"],
                    "email": u.get("email", ""),
                    "city": u.get("city", ""),
                    "current_title": u.get("current_title", ""),
                    "has_career_objective": bool(u.get("career_objective"))
                } for u in user_profiles
            ],
            "total_users": len(user_profiles)
        }
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@app.get("/jobs", tags=["Data"])
@limiter.limit("30/minute")
async def get_jobs(request: Request):
    try:
        return {
            "jobs": [
                {
                    "job_id": j.get("id"), 
                    "title": j.get("title"), 
                    "company": j.get("company_name"),
                    "location": j.get("location", ""),
                    "type": j.get("type", "")
                } for j in jobs
            ],
            "total_jobs": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")