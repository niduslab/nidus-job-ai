import os
import json
import time
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

class JobParams(BaseModel):
    job_title: str
    experience: Optional[str] = None
    education: Optional[str] = "Not Mentioned"
    industry: Optional[str] = None
    location_type: str = "onsite"
    required_skills: Optional[str] = None
    company_name: str = "Not mentioned"
    company_information: str = "Not mentioned"
    employment_type: str = "full-time"
    experience_level: Optional[str] = "None"
    job_responsibilities: Optional[str] = None
    required_qualifications: Optional[str] = None
    preferred_skills: Optional[str] = None
    salary_range: str = "Negotiable"
    benefits_perks: Optional[str] = None
    additional_notes: Optional[str] = None

class JobSections(BaseModel):
    executive_summary: str = Field(alias="Executive Summary")
    about_the_role: str = Field(alias="About the Role")
    job_responsibilities: List[str] = Field(alias="Job Responsibilities")
    required_qualifications: List[str] = Field(alias="Required Qualifications")
    preferred_qualifications: List[str] = Field(alias="Preferred Qualifications")
    what_we_offer: List[str] = Field(alias="What We Offer")
    skills: List[str]

    class Config:
        populate_by_name = True

class JobOutputs(BaseModel):
    sections: JobSections

class JobDescription(BaseModel):
    timestamp: str
    data_source: str
    params: JobParams
    outputs: JobOutputs

@dataclass
class JobParameters:
    job_title: str
    experience: Optional[str] = None
    education: str = "Not Mentioned"
    industry: Optional[str] = None
    location_type: str = "onsite"
    required_skills: Optional[str] = None
    company_name: str = "Not mentioned"
    company_information: str = "Not mentioned"
    employment_type: str = "full-time"
    experience_level: str = "None"
    job_responsibilities: Optional[str] = None
    required_qualifications: Optional[str] = None
    preferred_skills: Optional[str] = None
    salary_range: str = "negotiable"
    benefits_perks: Optional[str] = None
    additional_notes: Optional[str] = None

@dataclass
class ExecutionTiming:
    ai_generation_time: float
    total_execution_time: float
    processing_time: float

# Valid values for validation
VALID_EXPERIENCE_LEVELS = [
    "Internship", "Trainee", "Entry-level", "Junior", "Associate", 
    "Mid-level", "Intermediate", "Senior", "Lead", "Manager", 
    "Supervisor", "Director", "Executive", "VP", "C-suite", "None"
]

VALID_LOCATION_TYPES = [
    "remote", "onsite", "In-person", "Hybrid", "flexible"
]

VALID_EMPLOYMENT_TYPES = [
    "Full-Time", "Part-Time", "Contract", "Internship", "Freelance", 
    "Consulting", "Temporary", "Seasonal", "Apprenticeship", 
    "Trainee", "Volunteer", "full-time"
]

class AIJobDescriptionGenerator:
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model_type = "openai"
        self.model_name = model_name
        self._init_openai(api_key)
        
        self.prompt = ChatPromptTemplate.from_template(
            """Create a comprehensive job description for: {job_title}

Available Information:
- Job Title: {job_title}
- Experience Required: {experience}
- Education: {education}
- Industry: {industry}
- Location Type: {location_type}
- Required Skills: {required_skills}
- Company Name: {company_name}
- Company Information: {company_information}
- Employment Type: {employment_type}
- Experience Level: {experience_level}
- Job Responsibilities: {job_responsibilities}
- Required Qualifications: {required_qualifications}
- Preferred Skills: {preferred_skills}
- Salary Range: {salary_range}
- Benefits/Perks: {benefits_perks}
- Additional Notes: {additional_notes}

CRITICAL JSON FORMATTING REQUIREMENTS:
- Generate ONLY valid JSON without any comments, explanations, or additional text
- Do NOT include // comments in the JSON output
- Use proper JSON syntax with double quotes for all strings
- Ensure all arrays and objects are properly closed
- Do NOT add trailing commas

AI Instructions:
- Use provided information when available, generate intelligent content for missing fields
- If industry is "AI_DETERMINE", determine appropriate industry based on job title and other context
- If experience is "AI_DETERMINE", generate specific experience requirements (e.g., "2-4 years", "5 years", "5+ years") based on job title and other context, instead of vague terms like "2-3 years", "1+ years" etc.
- If education is "Not Mentioned", use "Not Mentioned" in output
- If experience_level is "None", use "None" in output
- STRICT REQUIREMENT SEPARATION: Only use skills from "required_skills" for Required Qualifications. Only use skills from "preferred_skills" for Preferred Qualifications. Do NOT mix or cross-reference between required and preferred skills
- If job responsibilities, qualifications, or skills are not provided, generate them based on the job title, industry, and experience level, but respect the required vs preferred skill distinction
- Consider the benefits/perks and additional notes when generating all other sections
- Ensure all generated content aligns with the employment type, experience level, and company context
- Generate realistic and professional content appropriate for the specified role
- The "skills" array MUST combine and consolidate ALL technical skills, soft skills, and competencies mentioned across all sections (required_skills, preferred_skills, job responsibilities, qualifications)
- Remove duplicates and create a comprehensive unified skills list
- IMPORTANT: Use the exact values provided for experience_level, employment_type, location_type, education - do not modify these values unless they need to be generated

Generate valid JSON in this exact format:
{{
  "timestamp": "{timestamp}",
  "data_source": "AI Generated using {model_type} - {model_name}",
  "params": {{
    "job_title": "{job_title}",
    "industry": "generated or provided industry value",
    "company_name": "{company_name}",
    "company_information": "{company_information}",
    "Education_levels": "{education}",
    "location_type": "{location_type}",
    "experience": "generated specific experience requirement like '2-4 years' or '5+ years'",
    "emplyment_type": "{employment_type}",
    "experience_level": "{experience_level}",
    "required_skills": ["skill1", "skill2", "skill3"],
    "salary_range": "{salary_range}",
    "preferred_skills": ["skill1", "skill2", "skill3"]
  }},
  "outputs": {{
    "sections": {{
      "Executive Summary": "compelling 2-3 sentence overview of the role considering all provided context",
      "About the Role": "detailed 3-4 sentence description about the position and its purpose",
      "Job Responsibilities": ["responsibility 1", "responsibility 2", "responsibility 3", "responsibility 4", "responsibility 5"],
      "Required Qualifications": ["qualification based on education and experience requirements", "qualification based on required_skills only", "qualification 3", "qualification 4","qualification 5"],
      "Preferred Qualifications": ["preferred qualification based on preferred_skills only", "preferred qualification 2", "preferred qualification 3", "preferred qualification 4","preferred qualification 5"],
      "What We Offer": ["benefit 1", "benefit 2", "benefit 3", "benefit 4", "benefit 5"],
      "skills": ["Consolidate and normalize skills mentioned across all sections into a structured list, mention all skills from Required Qualifications, Preferred Qualifications, soft skills, domain expertise, and relevant tools/technologies."]
    }}
  }}
}}
"""
        )

    def _init_openai(self, api_key: Optional[str] = None):
        try:
            from langchain_openai import ChatOpenAI
            
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable")
            
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=0.2,
                max_tokens=4000,
                top_p=0.9,
                frequency_penalty=0.1,
                request_timeout=120,
                max_retries=3,
                api_key=api_key
            )
            self.parser = JsonOutputParser(pydantic_object=JobDescription)
            
        except ImportError:
            raise ImportError("langchain_openai is required for OpenAI models")

    async def generate_async(self, params: JobParameters) -> tuple[str, ExecutionTiming]:
        ai_start_time = time.perf_counter()
        
        try:
            chain = self.prompt | self.llm
            experience_value = params.experience if params.experience is not None else "AI_DETERMINE"
            industry_value = params.industry or "AI_DETERMINE"

            response = await chain.ainvoke({
                "job_title": params.job_title,
                "experience": experience_value,
                "education": params.education,
                "industry": industry_value,
                "location_type": params.location_type,
                "required_skills": params.required_skills or "Generate based on job title and industry",
                "company_name": params.company_name,
                "company_information": params.company_information,
                "employment_type": params.employment_type,
                "experience_level": params.experience_level,
                "job_responsibilities": params.job_responsibilities or "Not specified",
                "required_qualifications": params.required_qualifications or "Not specified",
                "preferred_skills": params.preferred_skills or "Generate 2-5 relevant preferred skills based on job title and industry",
                "salary_range": params.salary_range,
                "benefits_perks": params.benefits_perks or "Not specified",
                "additional_notes": params.additional_notes or "Not specified",
                "timestamp": datetime.now().isoformat(),
                "model_type": self.model_type,
                "model_name": self.model_name,
                "valid_experience_levels": VALID_EXPERIENCE_LEVELS,
                "valid_location_types": VALID_LOCATION_TYPES,
                "valid_employment_types": VALID_EMPLOYMENT_TYPES
            })
            
            ai_end_time = time.perf_counter()
            ai_generation_time = ai_end_time - ai_start_time
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            json_str = self._clean_json_response(response_text)

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    if attempt == 0:
                        cleaned_json = json_str
                    elif attempt == 1:
                        cleaned_json = self._fix_json_issues(json_str)
                    else:
                        cleaned_json = self._aggressive_json_clean(json_str)
                    
                    result = json.loads(cleaned_json)
                    
                    processing_end_time = time.perf_counter()
                    processing_time = processing_end_time - ai_start_time
                    
                    timing = ExecutionTiming(
                        ai_generation_time=ai_generation_time,
                        total_execution_time=processing_time,
                        processing_time=processing_time
                    )
                    
                    return json.dumps(result, indent=2, ensure_ascii=False), timing
                    
                except json.JSONDecodeError as e:
                    if attempt == max_attempts - 1:
                        raise Exception(f"JSON parsing failed after {max_attempts} attempts: {e}")
                    
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {e}")

    def _clean_json_response(self, response_text: str) -> str:
        lines = response_text.split('\n')
        cleaned_lines = []
        for line in lines:
            if '//' in line:
                line = line.split('//')[0].rstrip()
            cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return cleaned_text[start_idx:end_idx + 1]
        
        return cleaned_text

    def _fix_json_issues(self, json_str: str) -> str:
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'(?<!\\)"(?=\w)', '\\"', json_str)
        return json_str

    def _aggressive_json_clean(self, json_str: str) -> str:
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        json_str = json_str.replace('\n', '\\n').replace('\t', '\\t')
        return json_str

def validate_job_parameters(params: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate job parameters and return validation errors"""
    errors = {}
    
    if not params.get("job_title"):
        errors.setdefault("job_title", []).append("Job title is required")
    
    location_type = params.get("location_type")
    if location_type and location_type not in VALID_LOCATION_TYPES:
        errors.setdefault("location_type", []).append(
            f"Invalid location_type. Valid options: {', '.join(VALID_LOCATION_TYPES)}"
        )
    
    employment_type = params.get("employment_type")
    if employment_type and employment_type not in VALID_EMPLOYMENT_TYPES:
        errors.setdefault("employment_type", []).append(
            f"Invalid employment_type. Valid options: {', '.join(VALID_EMPLOYMENT_TYPES)}"
        )
    
    experience_level = params.get("experience_level")
    if experience_level and experience_level not in VALID_EXPERIENCE_LEVELS:
        errors.setdefault("experience_level", []).append(
            f"Invalid experience_level. Valid options: {', '.join(VALID_EXPERIENCE_LEVELS)}"
        )
    
    return errors

def create_job_parameters(params: Dict[str, Any]) -> JobParameters:
    """Create JobParameters from request data with proper defaults"""
    return JobParameters(
        job_title=params["job_title"],
        experience=params.get("experience"),
        education=params.get("education", "Not Mentioned"), 
        industry=params.get("industry"),
        location_type=params.get("location_type", "onsite"),
        required_skills=params.get("required_skills"),
        company_name=params.get("company_name", "Not mentioned"),
        company_information=params.get("company_information", "Not mentioned"),
        employment_type=params.get("employment_type", "full-time"),
        experience_level=params.get("experience_level", "None"),
        job_responsibilities=params.get("job_responsibilities"),
        required_qualifications=params.get("required_qualifications"),
        preferred_skills=params.get("preferred_skills"),
        salary_range=params.get("salary_range", "negotiable"),
        benefits_perks=params.get("benefits_perks"),
        additional_notes=params.get("additional_notes")
    )