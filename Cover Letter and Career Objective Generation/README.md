# Cover Letter & Career Objective Generator API

A production-grade FastAPI application that generates personalized **cover letters** and **career objectives** using AI models (OpenAI GPT and Ollama).

## 🚀 Features

### Core Functionality
- **Manual Cover Letter Generation** – Custom input for job details and candidate info
- **Manual Career Objective Generation** – Custom input for job details and candidate info
- **Quick Generation** – Use predefined user and job profiles for both cover letters and career objectives
- **Multi-LLM Support** – Works with both OpenAI GPT and Ollama models
- **Professional Templates** – Following industry best practices

### Production-Grade Features
- ✅ **Security & Validation** – Input sanitization, XSS protection, email validation
- ✅ **Rate Limiting** – Prevents API abuse (per endpoint)
- ✅ **Error Handling** – User-friendly errors without exposing internals
- ✅ **Logging & Monitoring** – Structured logging with request/response tracking
- ✅ **CORS Protection** – Secure cross-origin requests
- ✅ **Health Checks** – Uptime monitoring endpoint
- ✅ **Comprehensive Testing** – Full test suite with security testing
- ✅ **API Documentation** – Auto-generated Swagger/OpenAPI docs

## 📋 Requirements

- Python 3.8+
- OpenAI API Key (optional, for GPT models)
- Ollama (optional, for local models)

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd cover-letter-generator
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

4. **Prepare data files:**
Ensure `user_profiles.json` and `jobs.json` are in the root directory.

5. **Run the application:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 API Endpoints

### Base URL: `http://localhost:8000`

| Method | Endpoint                  | Rate Limit | Description                                      |
|--------|---------------------------|------------|--------------------------------------------------|
| `GET`  | `/health`                 | None       | Health check endpoint                            |
| `GET`  | `/users`                  | 30/min     | List all available users                         |
| `GET`  | `/jobs`                   | 30/min     | List all available jobs                          |
| `POST` | `/generate`               | 5/min      | Generate cover letter (manual input)             |
| `POST` | `/generate-quick`         | 10/min     | Generate cover letter (user_id + job_id)         |
| `POST` | `/generate-objective`     | 10/min     | Generate career objective (manual input)         |
| `POST` | `/generate-objective-quick` | 15/min   | Generate career objective (user_id + job_id)     |
| `GET`  | `/docs`                   | None       | Interactive API documentation                    |

## 📝 API Usage Examples

### 1. Manual Cover Letter Generation

**POST** `/generate`
```json
{
  "job_title": "Software Developer",
  "company_name": "Tech Corp",
  "job_desc": "We are looking for a skilled software developer with Python experience. Responsibilities include developing web applications, working with databases, and collaborating with cross-functional teams.",
  "cv_text": "Experienced Python developer with 3 years of experience in web development. Proficient in Django, Flask, and database management. Led development of e-commerce platform that increased sales by 25%.",
  "candidate_info": {
    "Name": "John Doe",
    "Email": "john.doe@email.com",
    "Phone": "+1234567890",
    "City": "London",
    "State": "UK"
  },
  "llm_name": "ollama",
  "model_name": "llama3.1:latest"
}
```

### 2. Manual Career Objective Generation

**POST** `/generate-objective`
```json
{
  "job_title": "Software Developer",
  "company_name": "Tech Corp",
  "job_desc": "We are looking for a skilled software developer with Python experience.",
  "cv_text": "Experienced Python developer with 3 years of experience in web development.",
  "current_objective": "Seeking to grow as a backend engineer.",
  "llm_name": "openai",
  "model_name": "gpt-4o-mini"
}
```

### 3. Quick Cover Letter Generation (Using IDs)

**POST** `/generate-quick`
```json
{
  "user_id": "u1001",
  "job_id": "7001000001",
  "llm_name": "openai",
  "model_name": "gpt-4o-mini"
}
```

### 4. Quick Career Objective Generation (Using IDs)

**POST** `/generate-objective-quick`
```json
{
  "user_id": "u1001",
  "job_id": "7001000001",
  "llm_name": "ollama",
  "model_name": "llama3.1:latest"
}
```

### 5. Response Formats

**Cover Letter Response**
```json
{
  "cover_letter": "John Doe\nLondon, UK\n+1234567890\njohn.doe@email.com\n\nDear Hiring Manager,\n\nI am excited to apply for the Software Developer position at Tech Corp...",
  "processing_time": 2.453
}
```

**Career Objective Response**
```json
{
  "career_objective": "Results-driven developer with 3 years of experience seeking a Software Developer position at Tech Corp to leverage expertise in Python and web development to drive innovative solutions.",
  "processing_time": 1.872
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest test_api.py -v

# Run specific test categories
pytest test_api.py::TestCoverLetterAPI::test_security_validation -v
```

### Test Coverage
- ✅ Health check and endpoint availability
- ✅ Input validation (email, name, text length)
- ✅ Security testing (XSS, injection protection)
- ✅ Rate limiting verification
- ✅ Error handling (404, 422, 500)
- ✅ Response time monitoring

## 🔒 Security Features

- **Input Sanitization** – Removes HTML tags, scripts, and malicious content
- **Email Validation** – RFC-compliant email format checking
- **Rate Limiting** – IP-based request throttling
- **CORS Protection** – Restricted origins for cross-domain requests
- **Error Sanitization** – No internal details exposed in error responses

## 📊 Monitoring & Logging

- **Request Logging** – All API calls logged with timing
- **Error Tracking** – Comprehensive error logging with context
- **Performance Metrics** – Response times in headers (`X-Process-Time`)
- **Health Monitoring** – `/health` endpoint for uptime checks

## 🎯 Rate Limits

| Endpoint                   | Limit      | Purpose                              |
|----------------------------|------------|--------------------------------------|
| `/generate`                | 5/minute   | Prevent abuse of AI generation       |
| `/generate-quick`          | 10/minute  | Allow more frequent quick requests   |
| `/generate-objective`      | 10/minute  | Career objective manual generation   |
| `/generate-objective-quick`| 15/minute  | Career objective quick generation    |
| `/users`, `/jobs`          | 30/minute  | List endpoints for browsing          |

## 🔧 Configuration

### Environment Variables
```bash
# Required for OpenAI models
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Logging level
LOG_LEVEL=INFO

# Optional: Development mode
DEVELOPMENT_MODE=False
```

### Supported Models
- **OpenAI**: `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo`
- **Ollama**: `llama3.1:latest`, `llama2`, `codellama`, etc.

## 📁 Project Structure

```
cover-letter-generator/
├── main.py                   # FastAPI application
├── cover_letter_agent.py     # LLM agent logic for cover letters
├── career_objective_agent.py # LLM agent logic for career objectives
├── test_api.py               # Test suite
├── requirements.txt          # Dependencies
├── user_profiles.json        # User data
├── jobs.json                 # Job listings
├── .env                      # Environment variables
└── README.md                 # This file
```

## 🚀 Deployment

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📈 Performance

- **Average Response Time**: 2-3 seconds for cover letter or career objective generation
- **Concurrent Users**: Supports 100+ concurrent requests
- **Rate Limits**: Configurable per endpoint
- **Memory Usage**: ~200MB base, +50MB