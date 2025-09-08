from dataclasses import dataclass
from typing import Dict, Optional

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM 
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") or os.getenv("openaikey", "")

SYSTEM_PROMPT = """
You are a professional career counselor and expert resume writer specializing in crafting compelling career objectives.
Write a powerful, targeted career objective that aligns the candidate's experience with the specific job opportunity.

Guidelines for effective career objectives:
1. MAKE IT CONCISE: Limit to 2-3 sentences (50-80 words maximum) for easy scanning
2. TAILOR FOR EACH POSITION: Directly relate to the specific job and company mentioned
3. INCLUDE YOUR STRENGTHS: Highlight 2-3 most valuable skills like "critical thinker," "problem solver," "results-driven"
4. MENTION RELEVANT REQUIREMENTS: Include degrees, certifications, experience that match job requirements
5. EXPLAIN YOUR VALUE: Show how you can contribute to the company's success and growth
6. USE ACTION-ORIENTED LANGUAGE: Focus on results and achievements
7. AVOID GENERIC STATEMENTS: Be specific to the role and company

Structure:
- Start with professional identity/title and experience level
- Mention specific skills and qualifications relevant to the job
- Include the exact job title and company name
- End with value proposition (what you bring to the company)

Format: Write as a single paragraph without line breaks.

IMPORTANT: Return ONLY the career objective text. Do not include any introductory phrases like "Here is a career objective..." or explanatory text before the objective.
"""

FEW_SHOTS = """
Example 1:
Job Title: Software Developer
Company Name: TechFlow Solutions
Job Description: Seeking a skilled developer with Python and React experience for building scalable web applications. Requires 3+ years experience and knowledge of database management.
CV Text: Full stack developer with 3 years experience in Python, React, and MySQL database management. Led development of e-commerce platform that increased sales by 25%. Strong problem-solving skills.
Current Objective: Looking for software development opportunities to grow my technical skills.
Career Objective:
Results-driven full stack developer with 3 years of proven expertise in Python, React, and database management seeking a Software Developer position at TechFlow Solutions to leverage my track record of building scalable e-commerce solutions that increased sales by 25% and drive innovative web applications that enhance user experience and business growth.

Example 2:
Job Title: Data Analyst
Company Name: Analytics Corp
Job Description: Looking for a data analyst with SQL, Python, and visualization skills to analyze business metrics. Bachelor's degree required.
CV Text: Data professional with Bachelor's in Statistics and 2 years experience in SQL, Python, and Tableau. Improved reporting efficiency by 40% and identified cost-saving opportunities worth $50K.
Current Objective: None
Career Objective:
Detail-oriented data analyst with Bachelor's degree in Statistics and 2 years of hands-on experience in SQL, Python, and Tableau seeking a Data Analyst role at Analytics Corp to apply my proven ability to improve reporting efficiency by 40% and transform complex datasets into actionable business insights that drive strategic decision-making and cost optimization.

Example 3:
Job Title: Marketing Manager
Company Name: Brand Solutions
Job Description: Seeking a marketing professional with digital marketing, SEO, and campaign management experience. Must have proven track record of lead generation.
CV Text: Marketing specialist with 4 years in digital campaigns, SEO optimization, and social media marketing. Increased lead generation by 60% and managed budgets up to $100K. Certified in Google Analytics.
Current Objective: Ambitious marketing professional seeking growth opportunities in digital marketing field.
Career Objective:
Strategic marketing specialist with 4 years of experience in digital campaign management and Google Analytics certification seeking a Marketing Manager position at Brand Solutions to utilize my proven track record of increasing lead generation by 60% and managing $100K budgets while driving comprehensive marketing strategies that accelerate brand growth and market penetration.
"""

@dataclass
class CareerObjectiveAgent:
    llm_name: str  # "openai" or "ollama"
    model_name: str
    temperature: float = 0.1

    def __post_init__(self):
        if self.llm_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("openaikey")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            
            self.llm = ChatOpenAI(
                model=self.model_name, 
                temperature=self.temperature,
                openai_api_key=api_key
            )
        elif self.llm_name == "ollama":
            self.llm = OllamaLLM(model=self.model_name, temperature=self.temperature)
        else:
            raise ValueError("llm_name must be 'openai' or 'ollama'")

        template = (
            SYSTEM_PROMPT
            + FEW_SHOTS
            + "\n\nJob Title: {job_title}\nCompany Name: {company_name}\nJob Description: {job_desc}\n"
            + "CV Text: {cv_text}\nCurrent Objective: {current_objective}\n\nCareer Objective:\n"
        )
        prompt = PromptTemplate.from_template(template)
        self.chain = prompt | self.llm

    def generate(
        self,
        cv_text: str,
        job_title: str,
        company_name: str,
        job_desc: str,
        current_objective: Optional[str] = None,
    ) -> str:
        try:
            # Format current objective
            current_obj = current_objective if current_objective else "None"
            
            result = self.chain.invoke(
                {
                    "job_title": job_title,
                    "company_name": company_name,
                    "job_desc": job_desc,
                    "cv_text": cv_text,
                    "current_objective": current_obj,
                }
            )
            
            # Handle different return types from different LLMs
            if hasattr(result, 'content'):
                return result.content.strip()
            elif isinstance(result, str):
                return result.strip()
            else:
                return str(result).strip()
        except Exception as e:
            return f"❌ Error generating career objective: {str(e)}"