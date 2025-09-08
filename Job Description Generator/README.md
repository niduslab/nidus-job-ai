# AI Job Description Generator

This project generates professional job descriptions using AI models (Ollama or OpenAI) based on your configuration. It is designed for flexibility, automation, and high-quality output.

---

## Features
- **AI-powered**: Uses either a local Ollama model (Llama 3.2) or OpenAI's GPT-4o-mini via API.
- **Configurable**: Input your job requirements in a simple JSON config file.
- **Professional Output**: Generates detailed sections (summary, responsibilities, qualifications, benefits, skills) in a structured JSON format.
- **Timing Metrics**: Reports execution time for each step.
- **Robust**: Handles missing information by inferring industry standards.

---

## Setup Instructions

### 1. Clone the Repository
```
git clone <your-repo-url>
cd <repo-folder>
```

### 2. Install Dependencies
Create a virtual environment (optional but recommended):
```
python -m venv venv
.\venv\Scripts\activate  # On Windows
```
Install required packages:
```
pip install -r requirements.txt
```

### 3. Configure Environment Variables
- For **OpenAI**: Set your API key in a `.env` file or as an environment variable:
  - `.env` file:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    ```
  - Or set in your shell:
    ```
    $env:OPENAI_API_KEY="your_openai_api_key_here"  # PowerShell
    ```
- For **Ollama**: Ensure Ollama is installed and running locally with the `llama3.2` model available.

---

## Configuration

Edit the `config.json` file to specify your job requirements. Example:
```json
{
  "job_title": "Python Developer",
  "experience": 2,
  "education": null,
  "location_type": null,
  "required_skills": []
}
```
- **job_title**: (Required) The title of the job.
- **experience**: (Optional) Years of experience required.
- **education**: (Optional) Education requirement.
- **location_type**: (Optional) e.g., "Remote", "Hybrid", "Onsite".
- **required_skills**: (Optional) List of must-have skills.
- You may add other fields like `industry`, `company_name`, `preferred_skills` as needed.

---

## Usage

Run the main script:
```
python main.py
```

You will be prompted to select the AI model:
- `1` for Ollama (local, Llama 3.2)
- `2` for OpenAI (API, GPT-4o-mini)

The script will:
1. Load your configuration from `config.json`.
2. Generate a job description using the selected AI model.
3. Save the output as a JSON file in the `output/` directory.
4. Print timing statistics for each step.

---

## Output
- The generated job description is saved as a timestamped JSON file in the `output/` folder.
- The JSON includes all sections: Executive Summary, Key Responsibilities, Required/Preferred Qualifications, What We Offer, and Skills.

---