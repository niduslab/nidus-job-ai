from dataclasses import dataclass
from typing import Dict

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM 
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") or os.getenv("openaikey", "")

SYSTEM_PROMPT = """
You are a professional career storyteller and expert cover letter writer.
Write a compelling, tailored cover letter connecting the candidate's experience to the job.
Follow this structure and formatting:

1. Contact information (name, phone, email, city/Country, date)
2. Salutation (address the hiring manager by name if available, otherwise use 'Dear Hiring Manager,')
3. Opening paragraph: Express enthusiasm for the role and company, mention how your goals align, and reference the job title.
4. Middle paragraph(s): Highlight your most relevant experience, skills, and quantified achievements that match the job description. Make clear connections between your background and the employer's needs.
5. Closing paragraph: Thank the employer, restate your interest, and mention your desire to discuss further.
6. Complimentary close and signature (e.g., Sincerely, [Your Name])

Be professional, engaging, and avoid clichés. Use clear formatting with spaces between sections. But keep it concise, ideally one page and be specific to the job description provided.

IMPORTANT: Return ONLY the cover letter content. Do not include any introductory phrases like "Here is a tailored cover letter..." or explanatory text before the letter.
"""

FEW_SHOTS = """
Example:
Job Title: [Job Title]
Company Name: [Company Name]
Job Description: [Key requirements and responsibilities from the job posting.]
CV Text: [Summary of candidate's relevant experience, skills, and achievements.]
Candidate Info: Name: [Candidate Name], Email: [Candidate Email], Phone: [Candidate Phone], City: [City], Country: [Country], Date: [Date]
Cover Letter:
[Candidate Name]
[City], [Country]
[Candidate Phone]
[Candidate Email]
[Date]

Dear Hiring Manager,

I am excited to apply for the [Job Title] position at [Company Name]. With my background in [relevant skills/experience], I am confident that I can contribute to your team and help achieve [Company Name]'s goals.

In my previous role at [Previous Company or Organization if given else don't show], I [describe a key achievement or responsibility that relates to the new job]. My experience in [mention relevant skills or industries] has equipped me with the ability to [describe how your skills match the job requirements]. For example, I [quantified achievement or project], which resulted in [positive outcome].

I am particularly drawn to [Company Name]'s commitment to [mention a value, mission, or project of the company that resonates with you]. I am eager to bring my passion for [industry or skill] and my dedication to [related value or goal] to your organization.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experience can contribute to the success of your team.

Sincerely,
[Candidate Name]
"""

@dataclass
class CoverLetterAgent:
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
            + "CV Text: {cv_text}\nCandidate Info: {candidate_info}\n\nCover Letter:\n"
        )
        prompt = PromptTemplate.from_template(template)
        self.chain = prompt | self.llm

    def generate(
        self,
        cv_text: str,
        job_title: str,
        company_name: str,
        job_desc: str,
        candidate_info: Dict[str, str],
    ) -> str:
        try:
          
            ci_str = "\n".join(f"{k}: {v}" for k, v in candidate_info.items() if v)
            result = self.chain.invoke(
                {
                    "job_title": job_title,
                    "company_name": company_name,
                    "job_desc": job_desc,
                    "cv_text": cv_text,
                    "candidate_info": ci_str,
                }
            )
            # Handle different return types from different LLMs
            if hasattr(result, 'content'):
                return result.content
            elif isinstance(result, str):
                return result
            else:
                return str(result)
        except Exception as e:
            return f"❌ Error generating cover letter: {str(e)}"