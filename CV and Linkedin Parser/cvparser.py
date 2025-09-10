import os
import json
import re
import time
from typing import List, Optional
from pathlib import Path
from datetime import datetime

# Pydantic imports
from pydantic import BaseModel, Field

# LangChain imports
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM 

# PDF processing
from pdfminer.high_level import extract_text
import docx2txt

# Configuration
MODEL_NAME = "llama3.1:latest"
OLLAMA_BASE_URL = "http://localhost:11434"

# Pydantic Models
class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None

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

class CompleteResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    years_of_experience: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)

def get_llm():
    """Get the LLM instance."""
    return OllamaLLM(model=MODEL_NAME, temperature=0.1, base_url=OLLAMA_BASE_URL)

def clean_json_response(response: str) -> str:
    """Clean and extract JSON from LLM response."""
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*$', '', response)
    
    start_idx = response.find('{')
    if start_idx != -1:
        response = response[start_idx:]
    
    end_idx = response.rfind('}')
    if end_idx != -1:
        response = response[:end_idx + 1]
    
    return response.strip()

def calculate_years_of_experience(work_experiences: List[dict]) -> str:
    """Calculate total years of experience."""
    if not work_experiences:
        return "0 years"
    
    total_months = 0
    current_year = datetime.now().year
    
    for exp in work_experiences:
        duration = exp.get('duration', '').lower().replace('–', '-').replace('—', '-')
        
        if 'present' in duration:
            start_match = re.search(r'(\d{4})', duration)
            if start_match:
                start_year = int(start_match.group(1))
                total_months += (current_year - start_year) * 12
        else:
            years = re.findall(r'(\d{4})', duration)
            if len(years) >= 2:
                start_year = int(years[0])
                end_year = int(years[-1])
                total_months += (end_year - start_year) * 12
            elif len(years) == 1:
                total_months += 12
    
    total_years = max(1, total_months // 12)
    return f"{total_years} years"

def extract_complete_resume_info(resume_text: str) -> CompleteResume:
    """Extract all resume information in a single API call."""
    
    prompt_template = """
Extract information from the resume text and return ONLY a valid JSON object.

JSON Format:
{{
    "name": "Full Name",
    "email": "email@domain.com",
    "phone": "phone number",
    "location": "City, Country",
    "summary": "Professional summary",
    "technical_skills": ["Python", "Java", "React"],
    "soft_skills": ["Leadership", "Communication"],
    "education": [
        {{
            "institution": "University Name",
            "degree": "Bachelor/Master",
            "field_of_study": "Computer Science",
            "graduation_year": "2020"
        }}
    ],
    "work_experience": [
        {{
            "company": "Company Name",
            "position": "Job Title",
            "duration": "Start Date – End Date",
            "description": "Job responsibilities"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Project description",
            "technologies": "Technologies used",
            "duration": "Timeline"
        }}
    ],
    "years_of_experience": null,
    "certifications": ["Certification 1"]
}}

Resume Text:
{resume_text}
"""

    try:
        llm = get_llm()
        response = llm.invoke(prompt_template.format(resume_text=resume_text))
        
        cleaned_response = clean_json_response(response)
        parsed_data = json.loads(cleaned_response)
        
        # Calculate years of experience
        if parsed_data.get('work_experience'):
            calculated_years = calculate_years_of_experience(parsed_data['work_experience'])
            parsed_data['years_of_experience'] = calculated_years
        
        return CompleteResume(**parsed_data)
        
    except Exception as e:
        print(f"Error in extraction: {e}")
        return CompleteResume()

def read_file(file_path: str) -> str:
    """Read text from PDF, DOCX, or DOC file."""
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.pdf':
        return extract_text(str(file_path))
    elif file_path.suffix.lower() == '.docx':
        return docx2txt.process(str(file_path))
    elif file_path.suffix.lower() == '.doc':
        try:
            import doc2text
            doc = doc2text.Document(lang="eng")
            doc.read(str(file_path))
            doc.process()
            doc.extract_text()
            text = doc.get_text()
            return text
        except Exception as e:
            print(f"❌ Error extracting DOC with doc2text: {e}")
            return ""
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

def process_resume_with_timing(file_path: str):
    """Process resume and track timing for each step."""
    
    print(f"🔍 Processing: {file_path}")
    total_start_time = time.time()
    
    # Step 1: File Reading
    read_start_time = time.time()
    try:
        extracted_text = read_file(file_path)
        read_end_time = time.time()
        read_time = read_end_time - read_start_time
        
        if not extracted_text.strip():
            print("❌ No text extracted from file")
            return None
            
        print(f"📄 Text Reading: {read_time:.2f} seconds ({len(extracted_text)} characters)")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    # Step 2: LLM Processing
    llm_start_time = time.time()
    try:
        resume = extract_complete_resume_info(extracted_text)
        llm_end_time = time.time()
        llm_time = llm_end_time - llm_start_time
        
        print(f"🤖 LLM Processing: {llm_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error in LLM processing: {e}")
        return None
    
    # Step 3: Save Results
    save_start_time = time.time()
    try:
        output_file = f"Results/{Path(file_path).stem}_extracted.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(resume.model_dump_json(indent=2))
        
        save_end_time = time.time()
        save_time = save_end_time - save_start_time
        
        print(f"💾 File Saving: {save_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
    
    # Total Time
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    
    print(f"\n⏱️  TIMING SUMMARY:")
    print(f"   Text Reading:    {read_time:.2f}s ({(read_time/total_time)*100:.1f}%)")
    print(f"   LLM Processing:  {llm_time:.2f}s ({(llm_time/total_time)*100:.1f}%)")
    print(f"   File Saving:     {save_time:.2f}s ({(save_time/total_time)*100:.1f}%)")
    print(f"   TOTAL TIME:      {total_time:.2f}s")
    
    return resume, {
        'read_time': read_time,
        'llm_time': llm_time,
        'save_time': save_time,
        'total_time': total_time,
        'text_length': len(extracted_text)
    }

def print_resume_summary(resume: CompleteResume):
    """Print concise resume summary."""
    print(f"\n{'='*50}")
    print(f"📋 RESUME EXTRACTION RESULTS")
    print(f"{'='*50}")
    print(f"Name: {resume.name or 'Not found'}")
    print(f"Email: {resume.email or 'Not found'}")
    print(f"Phone: {resume.phone or 'Not found'}")
    print(f"Experience: {resume.years_of_experience or 'Not calculated'}")
    print(f"Technical Skills: {len(resume.technical_skills)} found")
    print(f"Education: {len(resume.education)} entries")
    print(f"Work Experience: {len(resume.work_experience)} entries")
    print(f"Projects: {len(resume.projects)} found")
    print(f"Certifications: {len(resume.certifications)} found")
    print(f"{'='*50}")

def main():
    """Main function with timing measurement."""
    
    # Process the resume
    resume_file = "demoresume.pdf"  # Change this to your file
    
    if not os.path.exists(resume_file):
        print(f"❌ Resume file not found: {resume_file}")
        
        # Show available files
        available_files = list(Path(".").glob("*.pdf")) + list(Path(".").glob("*.docx"))
        if available_files:
            print("\n📁 Available files:")
            for file in available_files:
                print(f"   - {file}")
        return
    
    # Process with timing
    result = process_resume_with_timing(resume_file)
    
    if result:
        resume, timing_info = result
        
        # Print summary
        print_resume_summary(resume)
        
        # Performance metrics
        chars_per_second = timing_info['text_length'] / timing_info['total_time']
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"   Processing Speed: {chars_per_second:.0f} characters/second")
        print(f"   LLM Efficiency: {timing_info['text_length'] / timing_info['llm_time']:.0f} chars/sec")
        
        print(f"\n✅ Complete data saved to: {Path(resume_file).stem}_extracted.json")
    
    else:
        print("❌ Failed to process the resume.")

if __name__ == "__main__":
    main()