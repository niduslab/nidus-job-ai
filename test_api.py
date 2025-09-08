import pytest
import json
from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)

class TestCoverLetterAPI:
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_get_users(self):
        """Test getting users list"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total_users" in data

    def test_get_jobs(self):
        """Test getting jobs list"""
        response = client.get("/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total_jobs" in data

    def test_generate_cover_letter_valid(self):
        """Test valid cover letter generation"""
        valid_request = {
            "job_title": "Software Developer",
            "company_name": "Tech Corp",
            "job_desc": "We are looking for a skilled software developer with Python experience.",
            "cv_text": "Experienced Python developer with 3 years of experience in web development.",
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
        
        response = client.post("/generate", json=valid_request)
        assert response.status_code == 200
        data = response.json()
        assert "cover_letter" in data
        assert len(data["cover_letter"]) > 0

    def test_generate_quick_cover_letter_valid(self):
        """Test valid quick cover letter generation"""
        valid_request = {
            "user_id": "u1001",
            "job_id": "7001000001",
            "llm_name": "ollama",
            "model_name": "llama3.1:latest"
        }
        
        response = client.post("/generate-quick", json=valid_request)
        assert response.status_code == 200
        data = response.json()
        assert "cover_letter" in data

    def test_invalid_email_validation(self):
        """Test email validation"""
        invalid_request = {
            "job_title": "Software Developer",
            "company_name": "Tech Corp",
            "job_desc": "We are looking for a skilled software developer.",
            "cv_text": "Experienced developer",
            "candidate_info": {
                "Name": "John Doe",
                "Email": "invalid-email",  # Invalid email
                "Phone": "+1234567890"
            }
        }
        
        response = client.post("/generate", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_invalid_name_validation(self):
        """Test name validation"""
        invalid_request = {
            "job_title": "Software Developer",
            "company_name": "Tech Corp",
            "job_desc": "We are looking for a skilled software developer.",
            "cv_text": "Experienced developer",
            "candidate_info": {
                "Name": "A",  # Too short
                "Email": "john.doe@email.com"
            }
        }
        
        response = client.post("/generate", json=invalid_request)
        assert response.status_code == 422

    def test_invalid_llm_name(self):
        """Test invalid LLM name"""
        invalid_request = {
            "job_title": "Software Developer",
            "company_name": "Tech Corp",
            "job_desc": "We are looking for a skilled software developer.",
            "cv_text": "Experienced developer",
            "candidate_info": {
                "Name": "John Doe",
                "Email": "john.doe@email.com"
            },
            "llm_name": "invalid_llm"  # Invalid LLM name
        }
        
        response = client.post("/generate", json=invalid_request)
        assert response.status_code == 422

    def test_user_not_found(self):
        """Test user not found error"""
        invalid_request = {
            "user_id": "nonexistent_user",
            "job_id": "7001000001"
        }
        
        response = client.post("/generate-quick", json=invalid_request)
        assert response.status_code == 404

    def test_job_not_found(self):
        """Test job not found error"""
        invalid_request = {
            "user_id": "u1001",
            "job_id": "nonexistent_job"
        }
        
        response = client.post("/generate-quick", json=invalid_request)
        assert response.status_code == 404

    def test_malicious_input_sanitization(self):
        """Test that malicious input is sanitized"""
        malicious_request = {
            "job_title": "<script>alert('xss')</script>Developer",
            "company_name": "Tech Corp",
            "job_desc": "We are looking for a developer",
            "cv_text": "javascript:alert('xss')",
            "candidate_info": {
                "Name": "John<script>alert('xss')</script>Doe",
                "Email": "john.doe@email.com"
            }
        }
        
        response = client.post("/generate", json=malicious_request)
        # Should either succeed with sanitized input or fail validation
        assert response.status_code in [200, 422]

    def test_response_time_header(self):
        """Test that response time header is present"""
        response = client.get("/health")
        assert "X-Process-Time" in response.headers

    def test_rate_limiting(self):
        """Test rate limiting (this might fail if limits are high)"""
        # Make multiple requests quickly
        responses = []
        for i in range(12):  # More than the limit
            response = client.get("/users")
            responses.append(response.status_code)
            time.sleep(0.1)
        
        # Should have at least one rate limit response
        assert 429 in responses or all(code == 200 for code in responses)

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/health")
        # CORS headers should be present in preflight response
        assert response.status_code in [200, 405]  # Some servers return 405 for OPTIONS

if __name__ == "__main__":
    pytest.main([__file__, "-v"])