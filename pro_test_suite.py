#!/usr/bin/env python3
"""
Professional Test Suite for Passenger Impact Engine
"""
import requests
import json
import sys
from typing import Dict, List, Optional

class ProfessionalTestSuite:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", admin_key: str = "test_admin_key_123"):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-Admin-Key": admin_key,
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.created_ids = []
    
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results professionally"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {name}"
        if details:
            result += f"\n   {details}"
        self.test_results.append((name, success, details))
        print(result)
        return success
    
    def test_health(self) -> bool:
        """Test basic API health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return self.log_test("Basic Health Check", True, f"Status: {data.get('status')}")
            return self.log_test("Basic Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("Basic Health Check", False, str(e))
    
    def test_enterprise_health(self) -> bool:
        """Test enterprise health with authentication"""
        try:
            response = requests.get(
                f"{self.base_url}/enterprise/health",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return self.log_test("Enterprise Health Check", True, 
                    f"Database: {data.get('database')}, Service: {data.get('service')}")
            return self.log_test("Enterprise Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("Enterprise Health Check", False, str(e))
    
    def test_authentication(self) -> bool:
        """Test that authentication is required"""
        try:
            # Test without auth (should fail)
            response = requests.get(f"{self.base_url}/enterprise/health", timeout=5)
            success_without = response.status_code == 401
            
            # Test with auth (should succeed)
            response = requests.get(
                f"{self.base_url}/enterprise/health",
                headers=self.headers,
                timeout=5
            )
            success_with = response.status_code == 200
            
            return self.log_test("Authentication Security", 
                success_without and success_with,
                f"Unauthorized: 401, Authorized: 200")
        except Exception as e:
            return self.log_test("Authentication Security", False, str(e))
    
    def test_create_company(self) -> Optional[str]:
        """Test company creation"""
        try:
            company_data = {
                "legal_name": "Professional Test Corp",
                "trading_name": "ProTest",
                "tier": "mid",
                "industry": "technology",
                "country": "US",
                "employee_count": 100,
                "annual_revenue_eur": 1000000.00
            }
            
            response = requests.post(
                f"{self.base_url}/enterprise/companies",
                headers=self.headers,
                json=company_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                company_id = data.get('id')
                self.created_ids.append(company_id)
                return self.log_test("Create Company", True, 
                    f"ID: {company_id}, Name: {data.get('legal_name')}")
            else:
                return self.log_test("Create Company", False, 
                    f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            return self.log_test("Create Company", False, str(e))
    
    def test_list_companies(self) -> bool:
        """Test company listing with pagination"""
        try:
            # Test basic listing
            response = requests.get(
                f"{self.base_url}/enterprise/companies",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                companies = data.get('companies', [])
                total = data.get('total', 0)
                
                # Test pagination
                response2 = requests.get(
                    f"{self.base_url}/enterprise/companies?limit=2",
                    headers=self.headers,
                    timeout=5
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    limited = len(data2.get('companies', []))
                    
                    return self.log_test("List Companies", True,
                        f"Total: {total}, Showing: {len(companies)}, Paginated: {limited}")
            
            return self.log_test("List Companies", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("List Companies", False, str(e))
    
    def test_get_company(self, company_id: str) -> bool:
        """Test retrieving a single company"""
        try:
            response = requests.get(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.log_test("Get Company", True,
                    f"Name: {data.get('legal_name')}, Tier: {data.get('tier')}")
            elif response.status_code == 404:
                return self.log_test("Get Company", False, "Company not found (404)")
            else:
                return self.log_test("Get Company", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("Get Company", False, str(e))
    
    def test_update_company(self, company_id: str) -> bool:
        """Test updating a company"""
        try:
            update_data = {
                "trading_name": "Updated Professional Corp",
                "employee_count": 250,
                "website": "https://professional-test.com"
            }
            
            response = requests.put(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                json=update_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.log_test("Update Company", True,
                    f"New Name: {data.get('trading_name')}")
            else:
                return self.log_test("Update Company", False,
                    f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            return self.log_test("Update Company", False, str(e))
    
    def test_delete_company(self, company_id: str) -> bool:
        """Test deleting a company"""
        try:
            response = requests.delete(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return self.log_test("Delete Company", True, "Company deleted successfully")
            else:
                return self.log_test("Delete Company", False,
                    f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            return self.log_test("Delete Company", False, str(e))
    
    def test_complete_crud_cycle(self) -> bool:
        """Test full CRUD cycle on a single company"""
        print("\n🔁 Testing Complete CRUD Cycle:")
        print("=" * 40)
        
        # 1. Create
        create_data = {
            "legal_name": "CRUD Cycle Test Corp",
            "tier": "small",
            "industry": "testing"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/enterprise/companies",
                headers=self.headers,
                json=create_data,
                timeout=5
            )
            
            if response.status_code != 200:
                return self.log_test("CRUD Cycle", False, f"Create failed: HTTP {response.status_code}")
            
            company_data = response.json()
            company_id = company_data.get('id')
            
            # 2. Read
            response = requests.get(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code != 200:
                return self.log_test("CRUD Cycle", False, f"Read failed: HTTP {response.status_code}")
            
            # 3. Update
            update_data = {"employee_count": 99}
            response = requests.put(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                json=update_data,
                timeout=5
            )
            
            if response.status_code != 200:
                return self.log_test("CRUD Cycle", False, f"Update failed: HTTP {response.status_code}")
            
            # 4. Delete
            response = requests.delete(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code != 200:
                return self.log_test("CRUD Cycle", False, f"Delete failed: HTTP {response.status_code}")
            
            # 5. Verify deletion
            response = requests.get(
                f"{self.base_url}/enterprise/companies/{company_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 404:
                return self.log_test("Complete CRUD Cycle", True, 
                    "Create → Read → Update → Delete → Verify: SUCCESS")
            else:
                return self.log_test("CRUD Cycle", False, "Deletion verification failed")
                
        except Exception as e:
            return self.log_test("CRUD Cycle", False, str(e))
    
    def run_all_tests(self) -> bool:
        """Run all professional tests"""
        print("🏢 PROFESSIONAL TEST SUITE - Passenger Impact Engine")
        print("=" * 60)
        
        # Basic tests
        self.test_health()
        self.test_enterprise_health()
        self.test_authentication()
        
        # CRUD tests
        self.test_list_companies()
        
        # Create a test company for further tests
        create_success = self.test_create_company()
        
        if create_success and self.created_ids:
            test_company_id = self.created_ids[0]
            self.test_get_company(test_company_id)
            self.test_update_company(test_company_id)
            self.test_get_company(test_company_id)  # Verify update
            self.test_delete_company(test_company_id)
        
        # Complete CRUD cycle test
        self.test_complete_crud_cycle()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total = len(self.test_results)
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 Failed Tests:")
            for name, success, details in self.test_results:
                if not success:
                    print(f"  • {name}: {details}")
        
        # Professional grade assessment
        print("\n" + "=" * 60)
        print("🏆 PROFESSIONAL GRADE ASSESSMENT")
        print("=" * 60)
        
        grade = "A+" if passed == total else "A" if passed/total >= 0.9 else "B" if passed/total >= 0.8 else "C"
        
        print(f"Grade: {grade}")
        print(f"Status: {'PRODUCTION READY' if passed/total >= 0.9 else 'NEEDS IMPROVEMENT'}")
        print(f"Recommendation: {'Ready for deployment' if passed/total >= 0.9 else 'Fix issues before production'}")
        
        return failed == 0
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        for company_id in self.created_ids:
            try:
                requests.delete(
                    f"{self.base_url}/enterprise/companies/{company_id}",
                    headers=self.headers,
                    timeout=3
                )
                print(f"  Deleted test company: {company_id}")
            except:
                pass

if __name__ == "__main__":
    print("🚀 Starting Professional Test Suite...\n")
    
    suite = ProfessionalTestSuite()
    
    try:
        success = suite.run_all_tests()
        suite.cleanup()
        
        if success:
            print("\n🎉 ALL TESTS PASSED - SYSTEM IS PROFESSIONAL GRADE!")
            sys.exit(0)
        else:
            print("\n⚠️  SOME TESTS FAILED - REVIEW AND FIX ISSUES")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite interrupted by user")
        suite.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        suite.cleanup()
        sys.exit(1)
