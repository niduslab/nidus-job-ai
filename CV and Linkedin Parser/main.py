from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import os
import json
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import hashlib

# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import your existing parsers
import cvparser1  # Manual parser
import cvparser   # LLM-based parser

# Configure logging with UTF-8 encoding fix
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cv_parser_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# In-memory storage for rate limiting and caching
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = {}
        
    def is_allowed(self, ip: str, max_requests: int = 10, time_window: int = 60) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()
        
        # Check if IP is temporarily blocked
        if ip in self.blocked_ips:
            if now < self.blocked_ips[ip]:
                return False
            else:
                del self.blocked_ips[ip]
        
        # Clean old requests
        while self.requests[ip] and self.requests[ip][0] < now - time_window:
            self.requests[ip].popleft()
        
        # Check rate limit
        if len(self.requests[ip]) >= max_requests:
            # Block IP for 5 minutes
            self.blocked_ips[ip] = now + 300
            return False
        
        # Add current request
        self.requests[ip].append(now)
        return True

# File cache for duplicate detection
class FileCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get_file_hash(self, content: bytes) -> str:
        """Get SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def get(self, file_hash: str) -> Optional[Dict]:
        """Get cached result if available."""
        if file_hash in self.cache:
            self.access_times[file_hash] = time.time()
            return self.cache[file_hash]
        return None
    
    def set(self, file_hash: str, result: Dict):
        """Cache result."""
        # Clean cache if full
        if len(self.cache) >= self.max_size:
            # Remove oldest accessed item
            oldest_hash = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_hash]
            del self.access_times[oldest_hash]
        
        self.cache[file_hash] = result
        self.access_times[file_hash] = time.time()

# Initialize rate limiter and cache
rate_limiter = RateLimiter()
file_cache = FileCache()

# Pydantic Models
class ContactInformation(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

class WorkExperience(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[str] = None
    duration: Optional[str] = None

class Certification(BaseModel):
    name: Optional[str] = None
    year: Optional[str] = None

class Skills(BaseModel):
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    all_skills: List[str] = Field(default_factory=list)

class ProcessingMetadata(BaseModel):
    processing_method: str
    total_time: float
    read_time: Optional[float] = None
    llm_time: Optional[float] = None
    save_time: Optional[float] = None
    text_length: int
    file_size: int
    processed_at: str
    request_id: str
    cached: bool = False
    file_hash: Optional[str] = None

class CVParseResponse(BaseModel):
    success: bool
    message: str
    request_id: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[ProcessingMetadata] = None
    error: Optional[str] = None

class BatchResponse(BaseModel):
    success: bool
    message: str
    request_id: str
    results: List[Dict[str, Any]]
    summary: Dict[str, int]

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
    request_id: str
    timestamp: str

# Application state management
class AppState:
    def __init__(self):
        self.is_healthy = False
        self.llm_available = False
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting CV Parser API...")
    
    # Create required directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("Results", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    # Check LLM availability
    try:
        llm = cvparser.get_llm()
        test_response = llm.invoke("Test")
        app_state.llm_available = True
        logger.info("LLM connection successful")
    except Exception as e:
        app_state.llm_available = False
        logger.warning(f"LLM not available: {e}")
    
    app_state.is_healthy = True
    logger.info("CV Parser API started successfully")
    
    yield
    
    logger.info("Shutting down CV Parser API...")

# Initialize FastAPI app
app = FastAPI(
    title="CV Parser API",
    description="Production-ready API for parsing CVs with rate limiting and caching",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Custom rate limiting middleware."""
    client_ip = get_remote_address(request)
    
    # Skip rate limiting for documentation and health endpoints
    skip_paths = ["/health", "/", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]
    if request.url.path in skip_paths:
        response = await call_next(request)
        return response
    
    # Apply rate limiting
    if not rate_limiter.is_allowed(client_ip, max_requests=15, time_window=60):  # Increased from 10 to 15
        app_state.failed_requests += 1
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "message": "Rate limit exceeded. Maximum 15 requests per minute.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "request_id": "rate_limited",
                "retry_after": "60 seconds",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    app_state.total_requests += 1
    response = await call_next(request)
    
    if response.status_code < 400:
        app_state.successful_requests += 1
    else:
        app_state.failed_requests += 1
    
    return response

# Utility functions
def generate_request_id() -> str:
    """Generate unique request ID."""
    return f"req_{uuid.uuid4().hex[:8]}_{int(time.time())}"

def validate_file_type(filename: str) -> bool:
    """Validate uploaded file type."""
    if not filename:
        return False
    allowed_extensions = {'.pdf', '.docx', '.doc'}
    return Path(filename).suffix.lower() in allowed_extensions

def save_uploaded_file(file: UploadFile, request_id: str) -> tuple[str, bytes]:
    """Save uploaded file to temporary location and return content."""
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_FILENAME",
                "message": "Uploaded file must have a filename",
                "request_id": request_id
            }
        )
    
    file_extension = Path(file.filename).suffix
    safe_filename = f"{request_id}_{file.filename.replace(' ', '_')}"
    temp_filename = f"temp/{safe_filename}"
    
    try:
        content = file.file.read()
        
        with open(temp_filename, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"File saved: {temp_filename} ({len(content)} bytes)")
        return temp_filename, content
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error_code": "FILE_SAVE_ERROR",
                "message": f"Failed to save uploaded file: {str(e)}",
                "request_id": request_id
            }
        )

def cleanup_temp_files(file_path: str):
    """Clean up temporary files."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Also remove extracted text files
        txt_path = file_path.rsplit('.', 1)[0] + '_extracted.txt'
        if os.path.exists(txt_path):
            os.remove(txt_path)
        
        # Remove parsed JSON files from cvparser1 
        json_path = file_path.rsplit('.', 1)[0] + '_parsed_comprehensive.json'
        if os.path.exists(json_path):
            os.remove(json_path)
            
        logger.info(f"Cleaned up temporary files: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up files: {e}")

def process_manual_parser_result(data: Dict) -> Dict[str, Any]:
    """Process manual parser result to match API response format."""
    return {
        "contact_information": data.get("contact_information", {}),
        "professional_summary": data.get("professional_summary", ""),
        "skills": data.get("skills", {"technical_skills": [], "soft_skills": [], "all_skills": []}),
        "education": data.get("education", []),
        "work_experience": data.get("work_experience", []),
        "projects": data.get("projects", []),
        "certifications": data.get("certifications", []),
        "years_of_experience": data.get("years_of_experience", ""),
        "ats_score": data.get("ats_score", 0),
        "metadata": data.get("metadata", {})
    }

def process_llm_parser_result(resume, timing_info: Dict) -> Dict[str, Any]:
    """Process LLM parser result to match API response format."""
    return {
        "contact_information": {
            "name": resume.name,
            "email": resume.email,
            "phone": resume.phone,
            "location": resume.location,
            "linkedin": "",
            "github": ""
        },
        "professional_summary": resume.summary or "",
        "skills": {
            "technical_skills": resume.technical_skills,
            "soft_skills": resume.soft_skills,
            "all_skills": resume.technical_skills + resume.soft_skills
        },
        "education": [
            {
                "institution": edu.institution,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "graduation_year": edu.graduation_year
            } for edu in resume.education
        ],
        "work_experience": [
            {
                "company": exp.company,
                "position": exp.position,
                "duration": exp.duration,
                "description": exp.description
            } for exp in resume.work_experience
        ],
        "projects": [
            {
                "name": proj.name,
                "description": proj.description,
                "technologies": proj.technologies,
                "duration": proj.duration
            } for proj in resume.projects
        ],
        "certifications": resume.certifications,
        "years_of_experience": resume.years_of_experience or "",
        "ats_score": 0,
        "metadata": {
            "total_sections": len([x for x in [resume.name, resume.email, resume.technical_skills, resume.education, resume.work_experience] if x]),
            "processed_at": datetime.now().isoformat(),
            "text_length": timing_info.get("text_length", 0)
        }
    }

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Basic API information"""
    return {
        "message": "CV Parser API with Rate Limiting & Caching",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health_check": "/health",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint with comprehensive statistics"""
    uptime = time.time() - app_state.start_time
    
    return {
        "status": "healthy" if app_state.is_healthy else "unhealthy",
        "llm_available": app_state.llm_available,
        "uptime_seconds": round(uptime, 2),
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "statistics": {
            "total_requests": app_state.total_requests,
            "successful_requests": app_state.successful_requests,
            "failed_requests": app_state.failed_requests,
            "success_rate": round((app_state.successful_requests / max(app_state.total_requests, 1)) * 100, 2),
            "cache_size": len(file_cache.cache)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/parse-cv", response_model=CVParseResponse, tags=["CV Parser"])
@limiter.limit("10/minute")  # Increased from 5 to 10
async def parse_cv(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: Literal["auto", "manual"] = Form(...),  # FIXED: Made required, removed default
    save_result: bool = Form(default=True)
):
    """
    Parse CV from uploaded file with caching and rate limiting
    
    REQUIRED Parameters:
    - file: CV file (PDF, DOCX, or DOC) - Max 10MB
    - method: 'manual' (rule-based) or 'auto' (LLM-based) - REQUIRED!
    
    Optional Parameters:
    - save_result: Whether to save results to file (default: true)
    """
    
    request_id = generate_request_id()
    start_time = time.time()
    temp_file_path = None
    
    try:
        logger.info(f"[{request_id}] Processing CV: {file.filename}, method: {method}")
        
        # Validate method parameter explicitly
        if method not in ["auto", "manual"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_METHOD",
                    "message": "Method must be either 'auto' or 'manual'",
                    "provided_method": method,
                    "valid_methods": ["auto", "manual"],
                    "request_id": request_id
                }
            )
        
        # Validate file type
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": "Only PDF, DOCX, and DOC files are supported",
                    "supported_formats": [".pdf", ".docx", ".doc"],
                    "request_id": request_id
                }
            )
        
        # Save file and get content for hashing
        temp_file_path, file_content = save_uploaded_file(file, request_id)
        file_size = len(file_content)
        
        # Check file size (limit to 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail={
                    "error_code": "FILE_TOO_LARGE",
                    "message": "File size must be less than 10MB",
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "max_size_mb": 10,
                    "request_id": request_id
                }
            )
        
        # Check for empty file
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMPTY_FILE",
                    "message": "Uploaded file is empty",
                    "request_id": request_id
                }
            )
        
        # Check cache for duplicate files
        file_hash = file_cache.get_file_hash(file_content)
        cached_result = file_cache.get(file_hash)
        
        if cached_result:
            logger.info(f"[{request_id}] Returning cached result for file hash: {file_hash[:8]}...")
            
            # Update metadata for cached result
            cached_result["metadata"]["request_id"] = request_id
            cached_result["metadata"]["cached"] = True
            cached_result["metadata"]["processed_at"] = datetime.now().isoformat()
            
            background_tasks.add_task(cleanup_temp_files, temp_file_path)
            
            return CVParseResponse(
                success=True,
                message="CV parsed successfully (cached result)",
                request_id=request_id,
                data=cached_result,
                metadata=ProcessingMetadata(**cached_result["metadata"])
            )
        
        # Process based on method - FIXED: Now properly handles required method
        if method == "manual":
            logger.info(f"[{request_id}] Using manual parser")
            
            try:
                parsed_data = cvparser1.parse_cv_file(temp_file_path)
                processed_data = process_manual_parser_result(parsed_data)
                
                processing_time = time.time() - start_time
                
                metadata = ProcessingMetadata(
                    processing_method="manual",
                    total_time=processing_time,
                    text_length=processed_data["metadata"].get("text_length", 0),
                    file_size=file_size,
                    processed_at=datetime.now().isoformat(),
                    request_id=request_id,
                    cached=False,
                    file_hash=file_hash
                )
                
            except Exception as e:
                logger.error(f"[{request_id}] Manual parsing failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "MANUAL_PARSING_FAILED",
                        "message": f"Manual parsing failed: {str(e)}",
                        "parser_type": "manual",
                        "request_id": request_id
                    }
                )
        
        elif method == "auto":
            if not app_state.llm_available:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error_code": "LLM_UNAVAILABLE",
                        "message": "LLM service is not available. Please use manual method.",
                        "alternative": "Use method=manual for rule-based parsing",
                        "request_id": request_id
                    }
                )
            
            logger.info(f"[{request_id}] Using LLM parser")
            
            try:
                result = cvparser.process_resume_with_timing(temp_file_path)
                if not result:
                    raise Exception("LLM parser returned no result")
                
                resume, timing_info = result
                processed_data = process_llm_parser_result(resume, timing_info)
                
                metadata = ProcessingMetadata(
                    processing_method="auto",
                    total_time=timing_info["total_time"],
                    read_time=timing_info["read_time"],
                    llm_time=timing_info["llm_time"],
                    save_time=timing_info["save_time"],
                    text_length=timing_info["text_length"],
                    file_size=file_size,
                    processed_at=datetime.now().isoformat(),
                    request_id=request_id,
                    cached=False,
                    file_hash=file_hash
                )
                
            except Exception as e:
                logger.error(f"[{request_id}] LLM parsing failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "LLM_PARSING_FAILED",
                        "message": f"LLM parsing failed: {str(e)}",
                        "parser_type": "auto",
                        "fallback_suggestion": "Try method=manual",
                        "request_id": request_id
                    }
                )
        
        # Cache the result
        cache_data = {
            **processed_data,
            "metadata": metadata.dict()
        }
        file_cache.set(file_hash, cache_data)
        logger.info(f"[{request_id}] Result cached with hash: {file_hash[:8]}...")
        
        # Save result to file if requested
        if save_result:
            try:
                output_file = f"Results/{request_id}_{Path(file.filename).stem}_parsed.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "request_id": request_id,
                        "filename": file.filename,
                        "method": method,
                        "data": processed_data,
                        "metadata": metadata.dict()
                    }, f, indent=2, ensure_ascii=False)
                
                logger.info(f"[{request_id}] Results saved to {output_file}")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to save results: {e}")
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_files, temp_file_path)
        
        # Prepare response
        response = CVParseResponse(
            success=True,
            message="CV parsed successfully",
            request_id=request_id,
            data=processed_data,
            metadata=metadata
        )
        
        logger.info(f"[{request_id}] CV parsed successfully in {metadata.total_time:.2f}s")
        return response
        
    except HTTPException:
        if temp_file_path:
            background_tasks.add_task(cleanup_temp_files, temp_file_path)
        raise
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}")
        if temp_file_path:
            background_tasks.add_task(cleanup_temp_files, temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected error occurred: {str(e)}",
                "request_id": request_id
            }
        )

@app.post("/parse-cv-batch", response_model=BatchResponse, tags=["CV Parser"])
@limiter.limit("2/minute")  # FIXED: Changed from 5/minute to 2/minute to match description
async def parse_cv_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    method: Literal["auto", "manual"] = Form(...)  # FIXED: Made required, removed default
):
    """
    Parse multiple CV files in batch processing
    
    Rate Limit: 2 requests per minute per IP (strict)
    
    REQUIRED Parameters:
    - files: List of CV files (max 5 files per batch)
    - method: Processing method for all files ('manual' or 'auto') - REQUIRED!
    """
    
    request_id = generate_request_id()
    logger.info(f"[{request_id}] Batch processing {len(files)} files with method: {method}")
    
    # Validate method parameter explicitly
    if method not in ["auto", "manual"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_METHOD",
                "message": "Method must be either 'auto' or 'manual'",
                "provided_method": method,
                "valid_methods": ["auto", "manual"],
                "request_id": request_id
            }
        )
    
    # Validate batch size first - return 400 if exceeded
    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "BATCH_SIZE_EXCEEDED",
                "message": "Maximum 5 files allowed per batch",
                "files_uploaded": len(files),
                "max_allowed": 5,
                "request_id": request_id
            }
        )
    
    # Validate all files first - if any file is invalid, return error immediately
    for i, file in enumerate(files):
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "MISSING_FILENAME",
                    "message": f"File at position {i+1} is missing filename",
                    "request_id": request_id
                }
            )
        
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": f"File '{file.filename}' has unsupported format. Only PDF, DOCX, and DOC files are supported",
                    "supported_formats": [".pdf", ".docx", ".doc"],
                    "request_id": request_id
                }
            )
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for i, file in enumerate(files):
        try:
            # Reset file pointer
            await file.seek(0)
            
            # Process each file individually - this will raise HTTPException on error
            result = await parse_cv(request, background_tasks, file, method, save_result=True)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "request_id": result.request_id,
                "data": result.data,
                "processing_time": result.metadata.total_time if result.metadata else 0,
                "cached": result.metadata.cached if result.metadata else False
            })
            successful_count += 1
            
        except HTTPException as he:
            # Log the error but continue processing other files
            logger.error(f"[{request_id}] Failed to process {file.filename}: HTTP {he.status_code} - {he.detail}")
            
            results.append({
                "filename": file.filename,
                "status": "error",
                "error_code": he.detail.get("error_code", "HTTP_ERROR") if isinstance(he.detail, dict) else "HTTP_ERROR",
                "error_message": he.detail.get("message", str(he.detail)) if isinstance(he.detail, dict) else str(he.detail),
                "http_status": he.status_code
            })
            failed_count += 1
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"[{request_id}] Unexpected error processing {file.filename}: {e}")
            
            results.append({
                "filename": file.filename,
                "status": "error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_message": f"Unexpected error: {str(e)}",
                "http_status": 500
            })
            failed_count += 1
    
    # Determine overall success based on results
    overall_success = successful_count > 0
    
    # Create response
    response = BatchResponse(
        success=overall_success,
        message=f"Batch processing completed: {successful_count} successful, {failed_count} failed",
        request_id=request_id,
        results=results,
        summary={
            "total_files": len(files),
            "successful": successful_count,
            "failed": failed_count
        }
    )
    
    logger.info(f"[{request_id}] Batch processing completed: {successful_count}/{len(files)} successful")
    
    return response

@app.get("/results/{request_id}", tags=["Results"])
@limiter.limit("30/minute")
async def get_result(request: Request, request_id: str):
    """Retrieve saved parsing results by request ID"""
    
    try:
        results_dir = Path("Results")
        if not results_dir.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "RESULTS_DIRECTORY_NOT_FOUND",
                    "message": "Results directory does not exist",
                    "request_id": request_id
                }
            )
        
        matching_files = list(results_dir.glob(f"{request_id}_*_parsed.json"))
        
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "RESULT_NOT_FOUND",
                    "message": f"No results found for request ID: {request_id}",
                    "request_id": request_id,
                    "suggestion": "Check if the request ID is correct or if results have been cleaned up"
                }
            )
        
        with open(matching_files[0], 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return {
            "success": True,
            "message": "Results retrieved successfully",
            "data": result_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving results for {request_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "RESULT_RETRIEVAL_ERROR",
                "message": f"Failed to retrieve results: {str(e)}",
                "request_id": request_id
            }
        )

@app.get("/supported-formats", tags=["Info"])
@limiter.limit("60/minute")
async def get_supported_formats(request: Request):
    """Get comprehensive API information"""
    return {
        "supported_formats": [
            {
                "extension": ".pdf",
                "description": "Portable Document Format",
                "max_size_mb": 10,
                "processing": "Direct text extraction"
            },
            {
                "extension": ".docx",
                "description": "Microsoft Word Document (2007+)",
                "max_size_mb": 10,
                "processing": "Direct text extraction"
            },
            {
                "extension": ".doc",
                "description": "Microsoft Word Document (Legacy)",
                "max_size_mb": 10,
                "processing": "OCR-based extraction (slower)",
                "note": "May require additional processing time"
            }
        ],
        "processing_methods": [
            {
                "method": "manual",
                "description": "Rule-based parsing using regex patterns",
                "speed": "Fast (< 1 second)",
                "accuracy": "High for standard CV formats",
                "pros": ["Fast", "Reliable", "No external dependencies"],
                "cons": ["Less flexible", "May miss complex layouts"],
                "recommended_for": "Standard CV formats, batch processing"
            },
            {
                "method": "auto",
                "description": "AI-powered parsing using Large Language Models",
                "speed": "Slower (2-5 seconds)",
                "accuracy": "High for all formats",
                "pros": ["More intelligent", "Better context understanding", "Handles complex layouts"],
                "cons": ["Slower", "Requires LLM service"],
                "available": app_state.llm_available,
                "recommended_for": "Complex CV layouts, non-standard formats"
            }
        ],
        "rate_limits": {
            "parse_cv": "10 requests per minute per IP",
            "batch_processing": "2 requests per minute per IP (max 5 files)",
            "get_results": "30 requests per minute per IP",
            "supported_formats": "60 requests per minute per IP",
            "general_middleware": "15 requests per minute per IP for all endpoints"
        },
        "features": [
            "File caching to avoid duplicate processing",
            "Automatic cleanup of temporary files",
            "Request tracking and statistics", 
            "Production-ready error handling",
            "Comprehensive logging",
            "Background task processing",
            "CORS support for web applications",
            "Proper HTTP status codes for all errors",
            "Required method parameter validation"
        ],
        "error_codes": {
            "INVALID_FILE_TYPE": "Unsupported file format uploaded",
            "INVALID_METHOD": "Method parameter must be 'auto' or 'manual'",
            "FILE_TOO_LARGE": "File exceeds 10MB size limit",
            "EMPTY_FILE": "Uploaded file is empty",
            "FILE_SAVE_ERROR": "Cannot save uploaded file to temporary storage",
            "MANUAL_PARSING_FAILED": "Rule-based parser encountered an error",
            "LLM_UNAVAILABLE": "AI service is not available",
            "LLM_PARSING_FAILED": "AI parser encountered an error",
            "BATCH_SIZE_EXCEEDED": "Too many files in batch request",
            "MISSING_FILENAME": "Uploaded file missing filename",
            "RESULT_NOT_FOUND": "Request ID not found in results",
            "RESULTS_DIRECTORY_NOT_FOUND": "Results directory does not exist",
            "RESULT_RETRIEVAL_ERROR": "Cannot read saved results",
            "RATE_LIMIT_EXCEEDED": "Too many requests from IP address",
            "INTERNAL_SERVER_ERROR": "Unexpected server error"
        }
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle all HTTP exceptions with structured error responses"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail),
            error_code=exc.detail.get("error_code", "HTTP_ERROR") if isinstance(exc.detail, dict) else "HTTP_ERROR",
            request_id=exc.detail.get("request_id", "unknown") if isinstance(exc.detail, dict) else "unknown",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle SlowAPI rate limit exceptions"""
    logger.warning(f"SlowAPI Rate limit exceeded: {exc.detail}")
    
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            message="Rate limit exceeded",
            error_code="SLOWAPI_RATE_LIMIT_EXCEEDED", 
            request_id="rate_limited",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unexpected exceptions"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="An internal server error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            request_id="unknown",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    
    # FIXED: Disable auto-reload to stop continuous file watching
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # CHANGED: Set to False to stop file watching
        log_level="info",
        access_log=True
    )