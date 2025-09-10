# AI Job Description Generator

A production-ready FastAPI application that generates comprehensive job descriptions using OpenAI's GPT models and LangChain. This API accepts job parameters and creates detailed, structured job descriptions with proper validation and error handling.

## 🚀 Features

- **AI-Powered Generation**: Uses OpenAI GPT-4o-mini for intelligent job description creation
- **Comprehensive Structure**: Generates executive summaries, responsibilities, qualifications, and benefits
- **Flexible Input**: Accepts minimal or detailed job parameters
- **Smart Defaults**: Automatically determines missing information based on context
- **Parameter Validation**: Validates input parameters with detailed error messages and HTTP status codes
- **Async Processing**: High-performance asynchronous API endpoints
- **CORS Support**: Cross-origin resource sharing enabled for web applications
- **Health Monitoring**: Built-in health check endpoints
- **Structured Output**: Consistent JSON format with timing metrics
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Input Schema](#input-schema)
- [Output Schema](#output-schema)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)

## 🛠 Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fastapi_langchain_openai_job_description_generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   echo "ENVIRONMENT=development" >> .env
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
```

## 🔗 API Endpoints

### 1. Root Endpoint
```
GET /
```
Returns API information and welcome message.

**Response:**
```json
{
  "message": "Welcome to AI Job Description Generator API",
  "version": "1.0.0",
  "description": "Production-ready API for generating AI-powered job descriptions",
  "docs_url": "/docs",
  "redoc_url": "/redoc",
  "timestamp": "2025-09-10T10:30:00.000000"
}
```

### 2. Health Check
```
GET /health
```
Returns service health status and environment information.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-09-10T10:30:00.000000",
  "environment": "development"
}
```

### 3. Generate Job Description
```
POST /api/v1/job-description/generate
```
Generates a comprehensive job description using AI.

**Status Codes:**
- `200` - Successfully generated job description
- `422` - Validation error (e.g., empty job_title, invalid enum values)
- `400` - Bad request data
- `500` - Internal server error
- `503` - Service unavailable (AI service issue)

### 4. Get Valid Options
```
GET /api/v1/job-description/valid-options
```
Returns valid values for experience levels, location types, and employment types.

**Response:**
```json
{
  "success": true,
  "data": {
    "experience_levels": ["Internship", "Trainee", "Entry-level", "Junior", "Associate", "Mid-level", "Intermediate", "Senior", "Lead", "Manager", "Supervisor", "Director", "Executive", "VP", "C-suite", "None"],
    "location_types": ["remote", "onsite", "In-person", "Hybrid", "flexible"],
    "employment_types": ["Full-Time", "Part-Time", "Contract", "Internship", "Freelance", "Consulting", "Temporary", "Seasonal", "Apprenticeship", "Trainee", "Volunteer", "full-time"]
  },
  "timestamp": "2025-09-10T10:30:00.000000"
}
```

### 5. Validate Parameters
```
POST /api/v1/job-description/validate
```
Validates job parameters without generating a description.

**Status Codes:**
- `200` - Validation completed (success or failure indicated in response body)
- `500` - Internal server error

## 📥 Input Schema

### Request Body Structure

```json
{
  "job_title": "string",
  "experience": "string",
  "education": "string",
  "industry": "string",
  "location_type": "string",
  "required_skills": "string",
  "company_name": "string",
  "company_information": "string",
  "employment_type": "string",
  "experience_level": "string",
  "job_responsibilities": "string",
  "required_qualifications": "string",
  "preferred_skills": "string",
  "salary_range": "string",
  "benefits_perks": "string",
  "additional_notes": "string"
}
```

### Field Specifications

| Field | Type | Required | Default Value | Valid Options | User Input | AI Generation |
|-------|------|----------|---------------|---------------|------------|---------------|
| `job_title` | string | **Yes** | - | Any non-empty string | ✅ Direct Input | ❌ |
| `experience` | string | No | null | Any string (e.g., "2-4 years", "5+ years") | ✅ Direct Input | ✅ If not provided |
| `education` | string | No | "Not Mentioned" | Any string | ✅ Direct Input | ❌ Uses default |
| `industry` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |
| `location_type` | string | No | "onsite" | `"remote"`, `"onsite"`, `"In-person"`, `"Hybrid"`, `"flexible"` | ✅ Direct Input | ❌ Uses default |
| `required_skills` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |
| `company_name` | string | No | "Not mentioned" | Any string | ✅ Direct Input | ❌ Uses default |
| `company_information` | string | No | "Not mentioned" | Any string | ✅ Direct Input | ❌ Uses default |
| `employment_type` | string | No | "full-time" | `"Full-Time"`, `"Part-Time"`, `"Contract"`, `"Internship"`, `"Freelance"`, `"Consulting"`, `"Temporary"`, `"Seasonal"`, `"Apprenticeship"`, `"Trainee"`, `"Volunteer"`, `"full-time"` | ✅ Direct Input | ❌ Uses default |
| `experience_level` | string | No | "None" | `"Internship"`, `"Trainee"`, `"Entry-level"`, `"Junior"`, `"Associate"`, `"Mid-level"`, `"Intermediate"`, `"Senior"`, `"Lead"`, `"Manager"`, `"Supervisor"`, `"Director"`, `"Executive"`, `"VP"`, `"C-suite"`, `"None"` | ✅ Direct Input | ❌ Uses default |
| `job_responsibilities` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |
| `required_qualifications` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |
| `preferred_skills` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |
| `salary_range` | string | No | "negotiable" | Any string | ✅ Direct Input | ❌ Uses default |
| `benefits_perks` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |
| `additional_notes` | string | No | null | Any string | ✅ Direct Input | ✅ If not provided |

### Validation Rules

- **job_title**: Cannot be empty or contain only whitespace
- **location_type**: Must be one of the valid location types if provided
- **employment_type**: Must be one of the valid employment types if provided
- **experience_level**: Must be one of the valid experience levels if provided

## 📤 Output Schema

### Response Structure

```json
{
  "success": boolean,
  "data": {
    "timestamp": "string (ISO format)",
    "data_source": "string",
    "params": {
      "job_title": "string",
      "industry": "string",
      "company_name": "string",
      "company_information": "string",
      "Education_levels": "string",
      "location_type": "string",
      "experience": "string",
      "emplyment_type": "string",
      "experience_level": "string",
      "required_skills": ["string"],
      "salary_range": "string",
      "preferred_skills": ["string"]
    },
    "outputs": {
      "sections": {
        "Executive Summary": "string",
        "About the Role": "string",
        "Job Responsibilities": ["string"],
        "Required Qualifications": ["string"],
        "Preferred Qualifications": ["string"],
        "What We Offer": ["string"],
        "skills": ["string"]
      }
    }
  },
  "timing": {
    "ai_generation_time": number,
    "total_execution_time": number,
    "processing_time": number
  },
  "message": "string"
}
```

### Output Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates if the request was successful |
| `data.timestamp` | string | ISO formatted timestamp of generation |
| `data.data_source` | string | Information about AI model used |
| `data.params` | object | Processed input parameters |
| `data.outputs.sections.Executive Summary` | string | 2-3 sentence overview of the role |
| `data.outputs.sections.About the Role` | string | 3-4 sentence detailed description |
| `data.outputs.sections.Job Responsibilities` | array | List of 5 key responsibilities |
| `data.outputs.sections.Required Qualifications` | array | List of 4 essential qualifications |
| `data.outputs.sections.Preferred Qualifications` | array | List of 3 preferred qualifications |
| `data.outputs.sections.What We Offer` | array | List of 4 benefits and offerings |
| `data.outputs.sections.skills` | array | Consolidated list of all mentioned skills |
| `timing` | object | Performance metrics for the generation process |

## ⚠️ Error Handling

The API implements comprehensive error handling with appropriate HTTP status codes:

### Status Code Reference

| Status Code | Description | When It Occurs |
|-------------|-------------|----------------|
| `200` | Success | Successful operations |
| `400` | Bad Request | Invalid data format |
| `404` | Not Found | Endpoint not found |
| `422` | Unprocessable Entity | Validation errors (empty job_title, invalid enum values) |
| `500` | Internal Server Error | Server errors, JSON parsing failures, unexpected errors |
| `503` | Service Unavailable | AI service issues, initialization failures |

### Error Response Format

```json
{
  "success": false,
  "error": "Error Type",
  "message": "Human-readable error message",
  "details": {
    "validation_errors": [
      {
        "field": "job_title",
        "message": "Job title is required and cannot be empty",
        "type": "value_error.missing"
      }
    ]
  },
  "timestamp": "2025-09-10T10:30:00.000000"
}
```

### Common Validation Errors

#### Empty Job Title (HTTP 422)

**Request:**
```json
{
  "job_title": ""
}
```

**Response:**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "The provided data is invalid",
  "details": {
    "validation_errors": [
      {
        "field": "job_title",
        "message": "Job title is required and cannot be empty",
        "type": "value_error.missing"
      }
    ]
  },
  "timestamp": "2025-09-10T10:30:00.000000"
}
```

#### Invalid Enum Value (HTTP 422)

**Request:**
```json
{
  "job_title": "Software Engineer",
  "location_type": "invalid_location"
}
```

**Response:**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "The provided data is invalid",
  "details": {
    "validation_errors": [
      {
        "field": "location_type",
        "message": "Invalid location_type. Valid options: remote, onsite, In-person, Hybrid, flexible",
        "type": "value_error"
      }
    ]
  },
  "timestamp": "2025-09-10T10:30:00.000000"
}
```

## 📖 Usage Examples

### Minimal Request (Only Required Field)

```json
{
  "job_title": "Senior Software Engineer"
}
```

### Partial Request (Some Optional Fields)

```json
{
  "job_title": "Data Scientist",
  "experience": "3-5 years",
  "industry": "Healthcare",
  "location_type": "remote",
  "required_skills": "Python, Machine Learning, SQL",
  "company_name": "HealthTech Solutions"
}
```

### Complete Request (All Fields)

```json
{
  "job_title": "Java backend developer",
  "company_name": "Niduslab",
  "company_information": "software development company specializing in AI solutions",
  "location_type": "Hybrid",
  "employment_type": "Apprenticeship",
  "experience_level": "Associate",
  "salary_range": "200k-300k",
  "experience": "5-7 years",
  "education": "Bachelor's Degree in Computer Science, Information Technology",
  "additional_notes": "company will provide relocation assistance if needed, and health benefits are included"
}
```

### Using Python

```python
import requests

# Minimal request
response = requests.post("http://localhost:8000/api/v1/job-description/generate", 
    json={
        "job_title": "Senior Software Engineer"
    }
)

if response.status_code == 200:
    result = response.json()
    print("Success:", result["success"])
    print("Job Description:", result["data"])
elif response.status_code == 422:
    error = response.json()
    print("Validation Error:", error["message"])
    print("Details:", error["details"])
else:
    print("Error:", response.status_code, response.text)
```

### Using cURL

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/job-description/generate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_title": "Java backend developer",
    "company_name": "Niduslab",
    "company_information": "software development company specializing in AI solutions",
    "location_type": "Hybrid",
    "employment_type": "Apprenticeship",
    "experience_level": "Associate",
    "salary_range": "200k-300k",
    "experience": "5-7 years",
    "education": "Bachelor'\''s Degree in Computer Science, Information Technology",
    "additional_notes": "company will provide relocation assistance if needed, and health benefits are included"
  }'
```

### Parameter Validation Example

```bash
# Validate parameters without generating
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/job-description/validate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_title": "Software Engineer",
    "location_type": "remote",
    "employment_type": "Full-Time"
  }'
```

### Sample Success Response

```json
{
  "success": true,
  "data": {
    "timestamp": "2025-09-10T10:30:00.000000",
    "data_source": "AI Generated using openai - gpt-4o-mini",
    "params": {
      "job_title": "Java backend developer",
      "industry": "Software Development",
      "company_name": "Niduslab",
      "company_information": "software development company specializing in AI solutions",
      "Education_levels": "Bachelor's Degree in Computer Science, Information Technology",
      "location_type": "Hybrid",
      "experience": "5-7 years",
      "emplyment_type": "Apprenticeship",
      "experience_level": "Associate",
      "required_skills": [
        "Java",
        "Spring Framework",
        "RESTful APIs",
        "Microservices",
        "SQL"
      ],
      "salary_range": "200k-300k",
      "preferred_skills": [
        "Cloud Technologies (AWS, Azure)",
        "Containerization (Docker, Kubernetes)",
        "Agile Methodologies"
      ]
    },
    "outputs": {
      "sections": {
        "Executive Summary": "We are seeking a skilled Java backend developer to join our dynamic team at Niduslab. This role is crucial for developing robust backend solutions that support our innovative AI applications.",
        "About the Role": "As a Java backend developer, you will be responsible for designing and implementing server-side logic, ensuring high performance and responsiveness to requests from the front-end. You will collaborate with cross-functional teams to define, design, and ship new features while maintaining code quality and performance.",
        "Job Responsibilities": [
          "Develop and maintain server-side applications using Java and related technologies.",
          "Design and implement RESTful APIs for seamless integration with front-end components.",
          "Collaborate with front-end developers to integrate user-facing elements with server-side logic.",
          "Optimize applications for maximum speed and scalability.",
          "Participate in code reviews and maintain coding standards."
        ],
        "Required Qualifications": [
          "Bachelor's Degree in Computer Science, Information Technology or related field.",
          "5-7 years of experience in Java development.",
          "Strong understanding of Spring Framework and RESTful API design.",
          "Experience with SQL and NoSQL databases."
        ],
        "Preferred Qualifications": [
          "Familiarity with cloud technologies such as AWS or Azure.",
          "Experience with containerization tools like Docker and Kubernetes.",
          "Knowledge of Agile methodologies and CI/CD pipelines."
        ],
        "What We Offer": [
          "Competitive salary range of 200k-300k.",
          "Relocation assistance if needed.",
          "Comprehensive health benefits.",
          "Opportunity to work in a hybrid environment."
        ],
        "skills": [
          "Java",
          "Spring Framework",
          "RESTful APIs",
          "Microservices",
          "SQL",
          "NoSQL",
          "Version Control (Git)",
          "Problem Solving",
          "Team Collaboration",
          "Cloud Technologies (AWS, Azure)",
          "Containerization (Docker, Kubernetes)",
          "Agile Methodologies",
          "Unit Testing",
          "CI/CD Pipelines"
        ]
      }
    }
  },
  "timing": {
    "ai_generation_time": 14.34,
    "total_execution_time": 14.34,
    "processing_time": 14.34
  },
  "message": "Job description generated successfully"
}
```

## 📁 Project Structure

```
fastapi_langchain_openai_job_description_generator/
├── main.py                 # FastAPI application and API endpoints
├── generator.py            # AI job description generation logic
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
├── README.md              # Project documentation
└── tests/                 # Test files (optional)
```

### Key Components

#### main.py
- FastAPI application setup
- Request/response models with Pydantic validation
- API endpoints and routing
- Comprehensive error handling
- CORS middleware configuration

#### generator.py
- AI job description generation logic
- OpenAI integration using LangChain
- JSON parsing and validation
- Parameter validation functions
- Performance timing tracking

## 🔧 Development

### Running in Development Mode

```bash
# With auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Testing the API

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Get Valid Options**
   ```bash
   curl http://localhost:8000/api/v1/job-description/valid-options
   ```

3. **Test Validation**
   ```bash
   curl -X POST http://localhost:8000/api/v1/job-description/validate \
     -H "Content-Type: application/json" \
     -d '{"job_title": "Software Engineer"}'
   ```

## 🚀 Deployment

### Production Setup

1. **Set production environment**
   ```bash
   export ENVIRONMENT=production
   export OPENAI_API_KEY=your_production_key
   ```

2. **Install production dependencies**
   ```bash
   pip install gunicorn
   ```

3. **Run with production ASGI server**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Environment Variables for Production

```env
OPENAI_API_KEY=your_production_openai_key
ENVIRONMENT=production
```

## 🔍 Monitoring and Troubleshooting

### Common Issues

1. **Empty job_title error (422)**
   - Ensure job_title is provided and not empty
   - Check for whitespace-only strings

2. **Invalid enum values (422)**
   - Use `/valid-options` endpoint to get valid values
   - Check spelling and case sensitivity

3. **AI service unavailable (503)**
   - Verify OpenAI API key is valid
   - Check internet connectivity
   - Monitor OpenAI service status

4. **JSON parsing errors (500)**
   - Usually indicates AI response formatting issues
   - API includes automatic retry mechanisms

### Performance Monitoring

The API includes timing metrics in responses:
- `ai_generation_time`: Time spent generating with AI
- `total_execution_time`: Total request processing time
- `processing_time`: Overall processing time

These metrics help monitor performance and identify