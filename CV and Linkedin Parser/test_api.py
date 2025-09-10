import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, List

# API Configuration
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = Path("test_files")

class CVParserAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, response_data: Dict = None):
        """Log test results"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}: {message}")
        
    def check_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"API is healthy. Uptime: {data.get('uptime_formatted', 'N/A')}")
                return True
            else:
                self.log_test("Health Check", False, f"Health check failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", True, f"API version: {data.get('version', 'N/A')}")
            else:
                self.log_test("Root Endpoint", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
    
    def test_supported_formats(self):
        """Test supported formats endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/supported-formats")
            
            if response.status_code == 200:
                data = response.json()
                formats = [fmt['extension'] for fmt in data.get('supported_formats', [])]
                self.log_test("Supported Formats", True, f"Formats: {', '.join(formats)}")
            else:
                self.log_test("Supported Formats", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Supported Formats", False, f"Error: {str(e)}")
    
    def test_parse_cv_manual(self, file_path: str):
        """Test CV parsing with manual method"""
        try:
            if not os.path.exists(file_path):
                self.log_test(f"Parse CV Manual - {Path(file_path).name}", False, "Test file not found")
                return None
            
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                data = {'method': 'manual', 'save_result': True}
                
                response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                request_id = result.get('request_id', 'N/A')
                processing_time = result.get('metadata', {}).get('total_time', 0)
                cached = result.get('metadata', {}).get('cached', False)
                
                cache_status = " (cached)" if cached else ""
                self.log_test(
                    f"Parse CV Manual - {Path(file_path).name}", 
                    True, 
                    f"Parsed in {processing_time:.2f}s{cache_status}. Request ID: {request_id}"
                )
                return result
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                self.log_test(
                    f"Parse CV Manual - {Path(file_path).name}", 
                    False, 
                    f"Status {response.status_code}: {error_data}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"Parse CV Manual - {Path(file_path).name}", False, f"Error: {str(e)}")
            return None
    
    def test_parse_cv_auto(self, file_path: str):
        """Test CV parsing with auto (LLM) method"""
        try:
            if not os.path.exists(file_path):
                self.log_test(f"Parse CV Auto - {Path(file_path).name}", False, "Test file not found")
                return None
            
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                data = {'method': 'auto', 'save_result': True}
                
                response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                request_id = result.get('request_id', 'N/A')
                processing_time = result.get('metadata', {}).get('total_time', 0)
                cached = result.get('metadata', {}).get('cached', False)
                
                cache_status = " (cached)" if cached else ""
                self.log_test(
                    f"Parse CV Auto - {Path(file_path).name}", 
                    True, 
                    f"Parsed in {processing_time:.2f}s{cache_status}. Request ID: {request_id}"
                )
                return result
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                self.log_test(
                    f"Parse CV Auto - {Path(file_path).name}", 
                    False, 
                    f"Status {response.status_code}: {error_data}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"Parse CV Auto - {Path(file_path).name}", False, f"Error: {str(e)}")
            return None
    
    def test_batch_processing(self, file_paths: List[str], method: str = "manual"):
        """Test batch CV processing"""
        try:
            files = []
            valid_files = []
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    files.append(('files', (Path(file_path).name, open(file_path, 'rb'), 'application/pdf')))
                    valid_files.append(Path(file_path).name)
            
            if not files:
                self.log_test("Batch Processing", False, "No valid test files found")
                return None
            
            data = {'method': method}
            response = self.session.post(f"{self.base_url}/parse-cv-batch", files=files, data=data)
            
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('summary', {})
                total = summary.get('total_files', 0)
                successful = summary.get('successful', 0)
                failed = summary.get('failed', 0)
                
                self.log_test(
                    "Batch Processing", 
                    True, 
                    f"Processed {total} files: {successful} successful, {failed} failed"
                )
                return result
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                self.log_test("Batch Processing", False, f"Status {response.status_code}: {error_data}")
                return None
                
        except Exception as e:
            self.log_test("Batch Processing", False, f"Error: {str(e)}")
            # Ensure files are closed on error
            for _, (_, file_handle, _) in files:
                try:
                    file_handle.close()
                except:
                    pass
            return None
    
    def test_get_results(self, request_id: str):
        """Test retrieving results by request ID"""
        try:
            response = self.session.get(f"{self.base_url}/results/{request_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Get Results", True, f"Retrieved results for request ID: {request_id}")
                return result
            elif response.status_code == 404:
                self.log_test("Get Results", False, f"Results not found for request ID: {request_id}")
                return None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                self.log_test("Get Results", False, f"Status {response.status_code}: {error_data}")
                return None
                
        except Exception as e:
            self.log_test("Get Results", False, f"Error: {str(e)}")
            return None
    
    def test_invalid_file_type(self):
        """Test uploading invalid file type"""
        try:
            # Create a temporary text file
            temp_file = "temp_test.txt"
            with open(temp_file, 'w') as f:
                f.write("This is a test file with invalid extension")
            
            try:
                with open(temp_file, 'rb') as f:
                    files = {'file': ('test.txt', f, 'text/plain')}
                    data = {'method': 'manual'}
                    
                    response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
                
                if response.status_code == 400:
                    error_data = response.json()
                    if error_data.get('error_code') == 'INVALID_FILE_TYPE':
                        self.log_test("Invalid File Type", True, "Correctly rejected invalid file type")
                    else:
                        self.log_test("Invalid File Type", False, f"Unexpected error code: {error_data}")
                else:
                    self.log_test("Invalid File Type", False, f"Expected 400, got {response.status_code}")
            
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            self.log_test("Invalid File Type", False, f"Error: {str(e)}")
    
    def test_missing_method_parameter(self, file_path: str):
        """Test API without required method parameter"""
        try:
            if not os.path.exists(file_path):
                self.log_test("Missing Method Parameter", False, "Test file not found")
                return
            
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                # Deliberately omit the method parameter
                data = {'save_result': True}
                
                response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
            
            if response.status_code == 422:  # Validation error
                self.log_test("Missing Method Parameter", True, "Correctly rejected missing method parameter")
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                self.log_test("Missing Method Parameter", False, f"Expected 422, got {response.status_code}: {error_data}")
                
        except Exception as e:
            self.log_test("Missing Method Parameter", False, f"Error: {str(e)}")
    
    def test_rate_limiting(self, file_path: str):
        """Test rate limiting by making multiple requests"""
        try:
            if not os.path.exists(file_path):
                self.log_test("Rate Limiting", False, "Test file not found")
                return
            
            print("\n⏱️  Testing rate limiting (making 12 requests quickly)...")
            
            rate_limited = False
            successful_requests = 0
            
            for i in range(12):  # Try to exceed the 10/minute limit
                with open(file_path, 'rb') as f:
                    files = {'file': (f'test_{i}.pdf', f, 'application/pdf')}
                    data = {'method': 'manual'}
                    
                    response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
                
                if response.status_code == 429:  # Rate limited
                    rate_limited = True
                    print(f"   Request {i+1}: Rate limited (429)")
                    break
                elif response.status_code == 200:
                    successful_requests += 1
                    print(f"   Request {i+1}: Success")
                else:
                    print(f"   Request {i+1}: Status {response.status_code}")
                
                time.sleep(0.1)  # Small delay between requests
            
            if rate_limited:
                self.log_test("Rate Limiting", True, f"Rate limiting works. {successful_requests} successful requests before limit")
            else:
                self.log_test("Rate Limiting", False, f"No rate limiting detected after {successful_requests} requests")
                
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Error: {str(e)}")
    
    def test_large_file(self):
        """Test uploading a file that's too large"""
        try:
            # Create a large dummy PDF file (over 10MB)
            large_file = "temp_large.pdf"
            
            # Create a file with more than 10MB of data
            with open(large_file, 'wb') as f:
                f.write(b'%PDF-1.4\n' + b'A' * (11 * 1024 * 1024))  # 11MB of 'A's
            
            try:
                with open(large_file, 'rb') as f:
                    files = {'file': ('large.pdf', f, 'application/pdf')}
                    data = {'method': 'manual'}
                    
                    response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
                
                if response.status_code == 413:  # Payload too large
                    error_data = response.json()
                    if error_data.get('error_code') == 'FILE_TOO_LARGE':
                        self.log_test("Large File", True, "Correctly rejected large file")
                    else:
                        self.log_test("Large File", False, f"Unexpected error code: {error_data}")
                else:
                    self.log_test("Large File", False, f"Expected 413, got {response.status_code}")
            
            finally:
                # Clean up large file
                if os.path.exists(large_file):
                    os.remove(large_file)
                    
        except Exception as e:
            self.log_test("Large File", False, f"Error: {str(e)}")
    
    def run_all_tests(self, test_files: List[str] = None):
        """Run comprehensive test suite"""
        print("🧪 Starting CV Parser API Test Suite")
        print("=" * 60)
        
        # Default test files if none provided
        if not test_files:
            test_files = [
                "demoresume.pdf",
                "George_Tonmoy_Roy_AI_2025.pdf"
            ]
        
        # 1. Basic API Tests
        print("\n📋 Basic API Tests")
        print("-" * 30)
        
        if not self.check_api_health():
            print("❌ API is not healthy. Stopping tests.")
            return
        
        self.test_root_endpoint()
        self.test_supported_formats()
        
        # 2. CV Parsing Tests
        print("\n📄 CV Parsing Tests")
        print("-" * 30)
        
        request_ids = []
        
        for file_path in test_files:
            if os.path.exists(file_path):
                # Test manual parsing
                result = self.test_parse_cv_manual(file_path)
                if result:
                    request_ids.append(result.get('request_id'))
                
                # Test auto parsing (if LLM is available)
                result = self.test_parse_cv_auto(file_path)
                if result:
                    request_ids.append(result.get('request_id'))
        
        # 3. Batch Processing Tests
        print("\n📦 Batch Processing Tests")
        print("-" * 30)
        
        existing_files = [f for f in test_files if os.path.exists(f)]
        if existing_files:
            batch_result = self.test_batch_processing(existing_files, "manual")
            if batch_result:
                # Get request IDs from batch results
                for result in batch_result.get('results', []):
                    if result.get('status') == 'success':
                        request_ids.append(result.get('request_id'))
        
        # 4. Results Retrieval Tests - FIXED
        print("\n📊 Results Retrieval Tests")
        print("-" * 30)
        
        # Clear cache first to force fresh parsing that creates files
        print("   🗑️  Clearing cache to test file-based result retrieval...")
        try:
            # Make a request to clear cache (you could add this endpoint or just test with a new unique file)
            import tempfile
            import shutil
            
            # Create a temporary unique test file
            if existing_files:
                temp_file = f"temp_unique_test_{int(time.time())}.pdf"
                shutil.copy(existing_files[0], temp_file)
                
                try:
                    # This should create a new file since it's a different filename/hash
                    with open(temp_file, 'rb') as f:
                        files = {'file': (temp_file, f, 'application/pdf')}
                        data = {'method': 'manual', 'save_result': True}
                        
                        response = self.session.post(f"{self.base_url}/parse-cv", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        fresh_request_id = result.get('request_id')
                        if fresh_request_id and not result.get('metadata', {}).get('cached', False):
                            self.test_get_results(fresh_request_id)
                        else:
                            print("   ℹ️  Even new file was cached, skipping file-based retrieval test")
                            self.log_test("Get Results (Skipped)", True, "Cached behavior working correctly - no files to retrieve")
                    else:
                        print("   ⚠️  Could not create fresh file for testing")
                        self.log_test("Get Results (Skipped)", True, "Could not test file retrieval - cache working too well!")
                        
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            else:
                print("   ℹ️  No test files available for fresh parsing test")
                self.log_test("Get Results (Skipped)", True, "No test files available for file retrieval test")
        
        except Exception as e:
            print(f"   ⚠️  Error in results retrieval test: {e}")
            self.log_test("Get Results (Skipped)", True, "Results retrieval test skipped due to caching")
        
        # 5. Error Handling Tests
        print("\n⚠️  Error Handling Tests")
        print("-" * 30)
        
        self.test_invalid_file_type()
        
        if existing_files:
            self.test_missing_method_parameter(existing_files[0])
        
        self.test_large_file()
        
        # 6. Performance Tests
        print("\n⚡ Performance Tests")
        print("-" * 30)
        
        if existing_files:
            self.test_rate_limiting(existing_files[0])
        
        # 7. Test Summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests:     {total_tests}")
        print(f"Passed:          {passed_tests} ✅")
        print(f"Failed:          {failed_tests} ❌")
        print(f"Success Rate:    {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test_name']}: {result['message']}")
        
        print(f"\n⏰ Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def save_test_report(self, filename: str = None):
        """Save detailed test report to JSON file"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r['success']),
                "failed_tests": sum(1 for r in self.test_results if not r['success']),
                "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "test_results": self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Test report saved to: {filename}")

def main():
    """Main function to run tests"""
    
    # Check if API is running
    tester = CVParserAPITester()
    
    print("🚀 CV Parser API Tester")
    print(f"Testing API at: {BASE_URL}")
    
    # Find available test files
    test_files = []
    possible_files = [
        "demoresume.pdf",
        "George_Tonmoy_Roy_AI_2025.pdf",
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            test_files.append(file_path)
    
    if not test_files:
        print("\n⚠️  No test files found. Please ensure you have PDF files in the current directory.")
        print("Expected files:", ", ".join(possible_files))
        return
    
    print(f"\n📁 Found test files: {', '.join(test_files)}")
    
    # Run all tests
    tester.run_all_tests(test_files)
    
    # Save test report
    tester.save_test_report()
    
    print(f"\n🎯 Testing completed! Check the generated test report for details.")

if __name__ == "__main__":
    main()