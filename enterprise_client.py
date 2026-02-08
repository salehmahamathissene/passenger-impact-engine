#!/usr/bin/env python3
"""
Enterprise API Client
"""

import requests
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Company:
    legal_name: str
    trading_name: str
    tier: str = "small"
    industry: str = "airline"
    country: str = "US"
    currency: str = "USD"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

@dataclass
class Contact:
    company_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: str = "operations_manager"
    department: str = "operations"

class EnterpriseClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", admin_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.admin_key = admin_key or os.getenv("ENTERPRISE_ADMIN_KEY")
        if not self.admin_key:
            raise ValueError("Admin key is required")
        
        self.headers = {
            "X-Admin-Key": self.admin_key,
            "Content-Type": "application/json"
        }
    
    def health(self) -> Dict:
        """Check API health"""
        response = requests.get(f"{self.base_url}/enterprise/health", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_company(self, company: Company) -> Dict:
        """Create a new company"""
        response = requests.post(
            f"{self.base_url}/enterprise/companies",
            json=asdict(company),
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_companies(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all companies"""
        response = requests.get(
            f"{self.base_url}/enterprise/companies",
            params={"limit": limit, "offset": offset},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_company(self, company_id: str) -> Dict:
        """Get company by ID"""
        response = requests.get(
            f"{self.base_url}/enterprise/companies/{company_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_contact(self, contact: Contact) -> Dict:
        """Create a new contact"""
        response = requests.post(
            f"{self.base_url}/enterprise/companies/{contact.company_id}/contacts",
            json=asdict(contact),
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_contract(self, contract_data: Dict) -> Dict:
        """Create a new contract"""
        response = requests.post(
            f"{self.base_url}/enterprise/contracts",
            json=contract_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_invoice(self, invoice_data: Dict) -> Dict:
        """Create a new invoice"""
        response = requests.post(
            f"{self.base_url}/enterprise/invoices",
            json=invoice_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def generate_invoice_pdf(self, invoice_id: str) -> bytes:
        """Generate PDF for invoice"""
        response = requests.post(
            f"{self.base_url}/enterprise/invoices/{invoice_id}/generate-pdf",
            json={},
            headers=self.headers
        )
        response.raise_for_status()
        return response.content
    
    def search(self, query: str) -> Dict:
        """Search across entities"""
        response = requests.get(
            f"{self.base_url}/enterprise/search",
            params={"q": query},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

def demo():
    """Demonstrate the client usage"""
    print("🚀 Enterprise API Client Demo")
    print("=" * 50)
    
    # Initialize client
    client = EnterpriseClient(
        base_url="http://127.0.0.1:8000",
        admin_key="test_admin_key_123"
    )
    
    # Check health
    health = client.health()
    print(f"✅ API Health: {health}")
    
    # List existing companies
    companies = client.list_companies(limit=5)
    print(f"\n📋 Existing companies: {len(companies)}")
    
    # Create a new company
    new_company = Company(
        legal_name="Demo Airline Corp",
        trading_name="DemoAir",
        tier="medium",
        industry="airline",
        country="UK",
        currency="GBP",
        contact_email="admin@demoair.com"
    )
    
    try:
        company_result = client.create_company(new_company)
        print(f"\n🏢 Created company: {company_result['legal_name']}")
        print(f"   ID: {company_result['id']}")
        
        # Create contact
        contact = Contact(
            company_id=company_result['id'],
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@demoair.com",
            role="director_of_operations"
        )
        
        contact_result = client.create_contact(contact)
        print(f"\n👥 Created contact: {contact_result['first_name']} {contact_result['last_name']}")
        
        # Create contract
        contract_data = {
            "company_id": company_result['id'],
            "contact_id": contact_result['id'],
            "name": "Demo Impact Analysis Package",
            "type": "monthly_subscription",
            "status": "active",
            "billing_frequency": "monthly",
            "price_per_unit": 1999.99,
            "currency": "GBP",
            "start_date": datetime.now().date().isoformat(),
            "terms": "Demo contract for testing"
        }
        
        contract_result = client.create_contract(contract_data)
        print(f"\n📝 Created contract: {contract_result['name']}")
        
        # Search
        search_results = client.search("Demo")
        print(f"\n🔍 Search results for 'Demo': {len(search_results.get('results', []))} items")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")

if __name__ == "__main__":
    demo()
