import os
import json
import time
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

class JobParams(BaseModel):
    job_title: str
    industry: str
    education: str
    company_name: str = "Your Company"
    location_type: str = "Hybrid"
    experience: float
    required_skills: List[str]
    preferred_skills: List[str]

class JobSections(BaseModel):
    executive_summary: str = Field(alias="Executive Summary")
    key_responsibilities: List[str] = Field(alias="Key Responsibilities")
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
    params: JobParams
    outputs: JobOutputs

@dataclass
class JobParameters:
    job_title: str
    industry: Optional[str] = None
    experience: Optional[float] = None
    education: Optional[str] = None
    company_name: Optional[str] = None
    location_type: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None

@dataclass
class ExecutionTiming:
    ai_generation_time: float
    total_execution_time: float
    config_load_time: float
    file_save_time: float

class AIJobDescriptionGenerator:
    def __init__(self, model_type: str = "ollama", model_name: str = None, api_key: Optional[str] = None):
        """
        Initialize the AI Job Description Generator
        
        Args:
            model_type: "ollama" or "openai"
            model_name: "llama3.2" for ollama, "gpt-4o-mini" for openai
            api_key: OpenAI API key (required for OpenAI models)
        """
        self.model_type = model_type.lower()
        
        # Set default model names
        if model_name is None:
            if self.model_type == "ollama":
                model_name = "llama3.2"
            else:
                model_name = "gpt-4o-mini"
        
        self.model_name = model_name
        
        if self.model_type == "ollama":
            self._init_ollama()
        elif self.model_type == "openai":
            self._init_openai(api_key)
        else:
            raise ValueError("model_type must be either 'ollama' or 'openai'")
        
        self.prompt = ChatPromptTemplate.from_template(
            """Create a comprehensive job description for: {job_title}

Available Information:
- Industry: {industry}
- Experience Level: {experience} years
- Education: {education}
- Company: {company_name}
- Work Model: {location_type}

AI Instructions:
- Intelligently fill any missing information based on industry standards for this role
- Generate appropriate required and preferred skills for this position
- Create professional, detailed job description sections
- Ensure all generated content is relevant and realistic for this role
- Output must be valid JSON in the exact structure below

{{
  "timestamp": "{timestamp}",
  "params": {{
    "job_title": "{job_title}",
    "industry": "industry (use provided or determine appropriate one)",
    "education": "education requirement (use provided or determine standard for role)",
    "company_name": "company name (use provided or generate professional default)",
    "location_type": "work arrangement (use provided or determine typical for role)",
    "experience": experience_years_as_number,
    "required_skills": ["list of essential skills for this role"],
    "preferred_skills": ["list of preferred/bonus skills for this role"]
  }},
  "outputs": {{
    "sections": {{
      "Executive Summary": "compelling 2-3 sentence overview of the role",
      "Key Responsibilities": ["5-7 specific responsibilities"],
      "Required Qualifications": ["4-6 essential qualifications"],
      "Preferred Qualifications": ["3-5 preferred qualifications"],
      "What We Offer": ["4-5 competitive benefits and opportunities"],
      "skills": ["Combined unique skills from required and preferred, plus relevant bonus skills as needed"]
    }}
  }}
}}
"""
        )

    def _init_ollama(self):
        """Initialize Ollama model - same as main_langchain_ollama.py"""
        try:
            from langchain_ollama import ChatOllama
            
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=0.2, 
                num_predict=1500,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                stop=["\n\n---", "Human:", "Assistant:"]
            )
            self.parser = JsonOutputParser(pydantic_object=JobDescription)
            
            print(f"✓ Connected to Ollama with model: {self.model_name}")
            
        except ImportError:
            raise ImportError("langchain_ollama is required for Ollama models. Install with: pip install langchain-ollama")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Ollama. Make sure Ollama is running and model {self.model_name} is available. Error: {e}")

    def _init_openai(self, api_key: Optional[str] = None):
        """Initialize OpenAI model"""
        try:
            from langchain_openai import ChatOpenAI
            
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                    "or pass it as a parameter."
                )
            
            print(f"✓ Initializing OpenAI with model: {self.model_name}")
            
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=0.1,
                max_tokens=1000,
                top_p=0.85,
                frequency_penalty=0.2,
                request_timeout=30,
                max_retries=1,
                api_key=api_key
            )
            self.parser = JsonOutputParser(pydantic_object=JobDescription)
            
        except ImportError:
            raise ImportError("langchain_openai is required for OpenAI models. Install with: pip install langchain-openai")

    def generate(self, params: JobParameters) -> tuple[str, float]:
        """Generate job description using the selected model"""
        print(f"Generating job description for: {params.job_title}")
        print(f"Using {self.model_type.upper()} model: {self.model_name}")
        
        ai_start_time = time.perf_counter()
        
        try:
            if self.model_type == "ollama":
                return self._generate_ollama(params, ai_start_time)
            else:
                return self._generate_openai(params, ai_start_time)
                
        except Exception as e:
            print(f"AI Generation failed: {e}")
            raise

    def _generate_ollama(self, params: JobParameters, ai_start_time: float) -> tuple[str, float]:
        """Generate using Ollama - use same approach as main_langchain_ollama.py"""
        try:
            chain = self.prompt | self.llm
            
            response = chain.invoke({
                "job_title": params.job_title,
                "industry": params.industry,
                "experience": params.experience,
                "education": params.education,
                "company_name": params.company_name,
                "location_type": params.location_type,
                "timestamp": datetime.now().isoformat(),
            })

            ai_end_time = time.perf_counter()
            ai_generation_time = ai_end_time - ai_start_time
            
            print("✓ Response received from Ollama")
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                try:
                   
                    result = json.loads(json_str)
                    return json.dumps(result, indent=2, ensure_ascii=False), ai_generation_time
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    print(f"Raw response: {response_text[:500]}...")
                    raise
            else:
                print(f"No JSON found in response: {response_text[:500]}...")
                raise ValueError("No valid JSON found in response")

        except Exception as e:
            print(f"Ollama generation failed: {e}")
            raise


    def _generate_openai(self, params: JobParameters, ai_start_time: float) -> tuple[str, float]:
        """Generate using OpenAI - same approach as main_langchain.py"""
        try:
           
            chain = self.prompt | self.llm | self.parser
            
            result = chain.invoke({
                "job_title": params.job_title,
                "industry": params.industry,
                "experience": params.experience,
                "education": params.education,
                "company_name": params.company_name,
                "location_type": params.location_type,
                "timestamp": datetime.now().isoformat(),
            })
            
            ai_end_time = time.perf_counter()
            ai_generation_time = ai_end_time - ai_start_time
            
            print("✓ Response received from OpenAI")
            return json.dumps(result, indent=2, ensure_ascii=False), ai_generation_time

        except Exception as e:
            print(f"OpenAI generation failed, trying fallback: {e}")
         
            return self._openai_fallback(params, ai_start_time)

    def _openai_fallback(self, params: JobParameters, ai_start_time: float) -> tuple[str, float]:
        """Fallback OpenAI generation - same as main_langchain.py"""
        try:
            from openai import OpenAI
            client = OpenAI()

            fallback_prompt = f"""Create a detailed job description JSON for the position of {params.job_title}.

Job Details:
- Industry: {params.industry}
- Experience: {params.experience} years
- Education: {params.education}
- Company Name: {params.company_name}
- Location Type: {params.location_type}

Instructions:
- Auto-generate all missing information based on industry standards for this role
- Generate relevant required and preferred skills
- Provide comprehensive job description sections
- Format as valid JSON matching the required structure

{{
  "timestamp": "{datetime.now().isoformat()}",
  "params": {{
    "job_title": "{params.job_title}",
    "industry": "AI-determined industry",
    "education": "AI-determined education requirement",
    "company_name": "AI-determined or provided company name",
    "location_type": "AI-determined location type",
    "experience": "AI-determined experience level",
    "required_skills": ["AI-generated required skills"],
    "preferred_skills": ["AI-generated preferred skills"]
  }},
  "outputs": {{
    "sections": {{
      "Executive Summary": "AI-generated compelling overview",
      "Key Responsibilities": ["AI-generated responsibilities"],
      "Required Qualifications": ["AI-generated qualifications"],
      "Preferred Qualifications": ["AI-generated preferred qualifications"],
      "What We Offer": ["AI-generated benefits"],
      "skills": ["Generate combined unique individual skills"]
    }}
  }}
}}
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": fallback_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1200
            )
            
            ai_end_time = time.perf_counter()
            ai_generation_time = ai_end_time - ai_start_time
            
            print("✓ Response received from OpenAI fallback")
            return response.choices[0].message.content, ai_generation_time
            
        except Exception as e:
            print(f"OpenAI fallback failed: {e}")
            raise

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Extract and validate JSON from text response"""
        text = text.strip()
        
        print(f"🔍 Extracting JSON from response (first 300 chars): {text[:300]}...")
        
        if text.startswith('{') and text.endswith('}'):
            try:
                result = json.loads(text)
                print("✓ Successfully parsed JSON directly")
                return result
            except json.JSONDecodeError as e:
                print(f"⚠ Direct JSON parsing failed: {e}")
        
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', 
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
        ]
        
        for i, pattern in enumerate(json_patterns):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1) if match.groups() else match.group()
                try:
                    print(f"✓ Pattern {i+1} matched, attempting to parse...")
                    json_str = re.sub(r',\s*}', '}', json_str)  
                    json_str = re.sub(r',\s*]', ']', json_str)
                    result = json.loads(json_str)
                    print("✓ Successfully parsed JSON from pattern")
                    return result
                except json.JSONDecodeError as e:
                    print(f"⚠ Pattern {i+1} JSON parsing failed: {e}")
                    continue
        
        print(f"❌ Could not extract JSON from response")
        print(f"Full response: {text}")
        return None

def save_job_description(job_desc: Dict[str, Any], output_dir: str = "output") -> float:
    """Save job description to JSON file"""
    save_start_time = time.perf_counter()
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    title = job_desc["params"]["job_title"]
    clean_title = "".join(c.lower() if c.isalnum() else '_' for c in title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_title}_{timestamp}.json"
    
    filepath = output_path / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(job_desc, f, indent=2, ensure_ascii=False)
    
    save_end_time = time.perf_counter()
    print(f"✓ Saved to: {filepath}")
    return save_end_time - save_start_time

def load_config(config_path: str = "config.json") -> tuple[JobParameters, float]:
    """Load configuration from JSON file"""
    load_start_time = time.perf_counter()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    
    params = JobParameters(
        job_title=cfg["job_title"],
        industry=cfg.get("industry"),
        experience=cfg.get("experience"),
        education=cfg.get("education"),
        company_name=cfg.get("company_name"),
        location_type=cfg.get("location_type"),
    )
    
    load_end_time = time.perf_counter()
    return params, load_end_time - load_start_time

def print_timing_results(timing: ExecutionTiming) -> None:
    """Print execution timing results - same format as main_langchain.py"""
    print("\n" + "="*50)
    print("EXECUTION TIMING RESULTS")
    print("="*50)
    print(f"Config Load Time:     {timing.config_load_time:.4f} seconds")
    print(f"AI Generation Time:   {timing.ai_generation_time:.4f} seconds")
    print(f"File Save Time:       {timing.file_save_time:.4f} seconds")
    print("-"*50)
    print(f"TOTAL EXECUTION TIME: {timing.total_execution_time:.4f} seconds")
    print("="*50)
    ai_percentage = (timing.ai_generation_time / timing.total_execution_time) * 100
    print(f"\nAI Generation represents {ai_percentage:.1f}% of total execution time")

def select_model() -> tuple[str, str]:
    """Interactive model selection"""
    print("\n🤖 Select AI Model:")
    print("1. Ollama (llama3.2) - Local")
    print("2. OpenAI (gpt-4o-mini) - API")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "1":
            return "ollama", "llama3.2"
        elif choice == "2":
            return "openai", "gpt-4o-mini"
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    """Main function - same structure as main_langchain.py"""
    print("🚀 AI Job Description Generator")
    print("=" * 60)
    
    model_type, model_name = select_model()
    
    print(f"\n📋 Using {model_type.upper()} model: {model_name}")
    print("=" * 60)
    
    total_start_time = time.perf_counter()
    
    try:
        
        params, config_load_time = load_config()
        print(f"📄 Loaded config for: {params.job_title}")
        
        generator = AIJobDescriptionGenerator(model_type=model_type, model_name=model_name)
        job_desc_json, ai_generation_time = generator.generate(params)
        job_desc = json.loads(job_desc_json)
        
        file_save_time = save_job_description(job_desc)
        
        total_end_time = time.perf_counter()
        total_execution_time = total_end_time - total_start_time
        
        timing = ExecutionTiming(
            ai_generation_time=ai_generation_time,
            total_execution_time=total_execution_time,
            config_load_time=config_load_time,
            file_save_time=file_save_time
        )
        print_timing_results(timing)
        
        print("\n Job description generated successfully!")
        return 0
        
    except Exception as e:
        print(f"\n Error: {e}")
        return 1

if __name__ == "__main__":
    main()