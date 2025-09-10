import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator

from generator import (
    AIJobDescriptionGenerator, 
    validate_job_parameters, 
    create_job_parameters,
    VALID_EXPERIENCE_LEVELS,
    VALID_LOCATION_TYPES,
    VALID_EMPLOYMENT_TYPES
)

app = FastAPI(
    title="AI Job Description Generator API",
    version="1.0.0",
    description="Production-ready API for generating AI-powered job descriptions"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

generator = None

def get_generator():
    global generator
    if generator is None:
        try:
            generator = AIJobDescriptionGenerator()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to initialize AI generator: {str(e)}"
            )
    return generator

class JobDescriptionRequest(BaseModel):
    job_title: str = Field(..., min_length=1, description="Job title is required and cannot be empty")
    experience: Optional[str] = None
    education: Optional[str] = None
    industry: Optional[str] = None
    location_type: Optional[str] = None
    required_skills: Optional[str] = None
    company_name: Optional[str] = None
    company_information: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    job_responsibilities: Optional[str] = None
    required_qualifications: Optional[str] = None
    preferred_skills: Optional[str] = None
    salary_range: Optional[str] = None
    benefits_perks: Optional[str] = None
    additional_notes: Optional[str] = None

    @validator('job_title')
    def validate_job_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Job title cannot be empty or contain only whitespace')
        return v.strip()

    @validator('location_type')
    def validate_location_type(cls, v):
        if v and v not in VALID_LOCATION_TYPES:
            raise ValueError(f'Invalid location_type. Valid options: {", ".join(VALID_LOCATION_TYPES)}')
        return v

    @validator('employment_type')
    def validate_employment_type(cls, v):
        if v and v not in VALID_EMPLOYMENT_TYPES:
            raise ValueError(f'Invalid employment_type. Valid options: {", ".join(VALID_EMPLOYMENT_TYPES)}')
        return v

    @validator('experience_level')
    def validate_experience_level(cls, v):
        if v and v not in VALID_EXPERIENCE_LEVELS:
            raise ValueError(f'Invalid experience_level. Valid options: {", ".join(VALID_EXPERIENCE_LEVELS)}')
        return v

class ValidationRequest(BaseModel):
    job_title: Optional[str] = Field(None, min_length=1, description="Job title cannot be empty")
    experience: Optional[str] = None
    education: Optional[str] = None
    industry: Optional[str] = None
    location_type: Optional[str] = None
    required_skills: Optional[str] = None
    company_name: Optional[str] = None
    company_information: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    job_responsibilities: Optional[str] = None
    required_qualifications: Optional[str] = None
    preferred_skills: Optional[str] = None
    salary_range: Optional[str] = None
    benefits_perks: Optional[str] = None
    additional_notes: Optional[str] = None

    @validator('job_title')
    def validate_job_title(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Job title cannot be empty or contain only whitespace')
        return v.strip() if v else v

    @validator('location_type')
    def validate_location_type(cls, v):
        if v and v not in VALID_LOCATION_TYPES:
            raise ValueError(f'Invalid location_type. Valid options: {", ".join(VALID_LOCATION_TYPES)}')
        return v

    @validator('employment_type')
    def validate_employment_type(cls, v):
        if v and v not in VALID_EMPLOYMENT_TYPES:
            raise ValueError(f'Invalid employment_type. Valid options: {", ".join(VALID_EMPLOYMENT_TYPES)}')
        return v

    @validator('experience_level')
    def validate_experience_level(cls, v):
        if v and v not in VALID_EXPERIENCE_LEVELS:
            raise ValueError(f'Invalid experience_level. Valid options: {", ".join(VALID_EXPERIENCE_LEVELS)}')
        return v

class JobDescriptionResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    timing: Dict[str, float]
    message: str = "Job description generated successfully"

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    environment: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with HTTP 422 status"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        
        if "job_title" in field:
            if "field required" in message:
                message = "Job title is required and cannot be empty"
            elif "ensure this value has at least 1 characters" in message:
                message = "Job title must contain at least 1 character"
            elif "Job title cannot be empty" in message:
                message = "Job title cannot be empty or contain only whitespace"
        
        errors.append({
            "field": field,
            "message": message,
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "The provided data is invalid",
            "details": {
                "validation_errors": errors
            },
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper status codes"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": "Not Found",
            "message": "The requested endpoint was not found",
            "status_code": 404,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 Internal Server Error"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred on the server",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with 500 status"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Unexpected Error",
            "message": f"An unexpected error occurred: {str(exc)}",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to AI Job Description Generator API",
        "version": "1.0.0",
        "description": "Production-ready API for generating AI-powered job descriptions",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            environment=os.getenv("ENVIRONMENT", "development")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.post("/api/v1/job-description/generate", response_model=JobDescriptionResponse)
async def generate_job_description(request: JobDescriptionRequest):
    """
    Generate a job description using AI
    
    **Required Fields:**
    - job_title: The title of the job position (cannot be empty)
    
    **Optional Fields:**
    - experience: Years of experience required
    - education: Educational requirements
    - industry: Industry sector
    - location_type: Work location type (remote, onsite, hybrid, etc.)
    - required_skills: Essential skills required
    - company_name: Name of the hiring company
    - company_information: Information about the company
    - employment_type: Type of employment (full-time, part-time, etc.)
    - experience_level: Level of experience (junior, senior, etc.)
    - job_responsibilities: Specific job responsibilities
    - required_qualifications: Required qualifications
    - preferred_skills: Preferred but not required skills
    - salary_range: Salary range for the position
    - benefits_perks: Benefits and perks offered
    - additional_notes: Any additional information
    
    **Returns:**
    - HTTP 200: Successfully generated job description
    - HTTP 422: Validation error (e.g., empty job_title)
    - HTTP 500: Internal server error
    - HTTP 503: Service unavailable (AI service issue)
    """
    try:
       
        request_data = request.dict(exclude_unset=True)
        validation_errors = validate_job_parameters(request_data)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Invalid input parameters",
                    "details": validation_errors
                }
            )
        
        job_params = create_job_parameters(request_data)
        generator_instance = get_generator()
        job_desc_json, timing = await generator_instance.generate_async(job_params)
        job_desc = json.loads(job_desc_json)

        response = JobDescriptionResponse(
            success=True,
            data=job_desc,
            timing={
                "ai_generation_time": timing.ai_generation_time,
                "total_execution_time": timing.total_execution_time,
                "processing_time": timing.processing_time
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "JSON Parsing Error",
                "message": f"Failed to parse AI response: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Bad Request",
                "message": f"Invalid data provided: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service Unavailable",
                "message": f"AI service is currently unavailable: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Generation Error",
                "message": f"Failed to generate job description: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/v1/job-description/valid-options")
async def get_valid_options():
    """
    Get valid options for job description parameters
    
    **Returns:**
    - HTTP 200: Successfully retrieved valid options
    - HTTP 500: Internal server error
    """
    try:
        return {
            "success": True,
            "data": {
                "experience_levels": VALID_EXPERIENCE_LEVELS,
                "location_types": VALID_LOCATION_TYPES,
                "employment_types": VALID_EMPLOYMENT_TYPES
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Server Error",
                "message": f"Failed to retrieve valid options: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/v1/job-description/validate")
async def validate_parameters(request: ValidationRequest):
    """
    Validate job description parameters without generating
    
    **Returns:**
    - HTTP 200: Validation completed (success or failure indicated in response body)
    - HTTP 500: Internal server error
    """
    try:
        request_data = request.dict(exclude_unset=True)
        
        validation_errors = validate_job_parameters(request_data)
        
        if validation_errors:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": False,
                    "valid": False,
                    "errors": validation_errors,
                    "message": "Validation failed - please check the errors",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "valid": True,
            "message": "All parameters are valid",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Validation Error",
                "message": f"Failed to validate parameters: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )