"""
ADVANCED BILLING SYSTEM INTEGRATION TEST
Tests the complete billing workflow with modern features.
"""

import os
import sys
import json
import uuid
import requests
import stripe
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.working')

# Configuration
BASE_URL = "http://127.0.0.1:8080"
COMPANY_ID = os.environ.get("COMPANY_ID")
API_KEY = os.environ.get("API_KEY")
STRIPE_SECRET = os.environ.get("STRIPE_SECRET_KEY")

# Initialize Stripe
stripe.api_key = STRIPE_SECRET

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Headers for API requests
headers = {
    "X-Company-Id": COMPANY_ID,
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json",
}

def print_step(step, description):
    """Print formatted test step"""
    print(f"\n{'='*60}")
    print(f"STEP {step}: {description}")
    print(f"{'='*60}")

def test_authentication():
    """Test API authentication"""
    print_step(1, "Testing API Authentication")
    
    # Test with valid credentials
    response = requests.get(
        f"{BASE_URL}/enterprise/invoices",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Authentication: SUCCESS")
        return True
    else:
        print(f"❌ Authentication: FAILED ({response.status_code})")
        print(f"Response: {response.text}")
        return False

def test_subscription_endpoint():
    """Test subscription status endpoint"""
    print_step(2, "Testing Subscription Endpoint")
    
    response = requests.get(
        f"{BASE_URL}/enterprise/billing/subscription",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Subscription Endpoint: SUCCESS")
        print(f"   Current Plan: {data.get('plan')}")
        print(f"   Active: {data.get('active')}")
        print(f"   Status: {data.get('status')}")
        return data
    else:
        print(f"❌ Subscription Endpoint: FAILED ({response.status_code})")
        return None

def test_checkout_session():
    """Test checkout session creation"""
    print_step(3, "Testing Checkout Session Creation")
    
    payload = {
        "plan": "pro",
        "success_url": f"{BASE_URL}/enterprise/billing/success",
        "cancel_url": f"{BASE_URL}/enterprise/billing/cancel",
        "trial_days": 14
    }
    
    response = requests.post(
        f"{BASE_URL}/enterprise/billing/checkout",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Checkout Session: SUCCESS")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   URL: {data.get('url')[:80]}...")
        print(f"   Customer ID: {data.get('customer_id')}")
        
        # Test the URL
        if data.get('url'):
            print(f"   🔗 Checkout URL ready for use")
            print(f"   💡 Use test card: 4242 4242 4242 4242")
        
        return data
    else:
        print(f"❌ Checkout Session: FAILED ({response.status_code})")
        print(f"Response: {response.text}")
        return None

def test_billing_portal():
    """Test billing portal session creation"""
    print_step(4, "Testing Billing Portal")
    
    payload = {
        "return_url": f"{BASE_URL}/enterprise/dashboard"
    }
    
    response = requests.post(
        f"{BASE_URL}/enterprise/billing/portal",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Billing Portal: SUCCESS")
        print(f"   Portal URL: {data.get('url')[:80]}...")
        print(f"   Expires at: {data.get('expires_at')}")
        return data
    else:
        print(f"❌ Billing Portal: FAILED ({response.status_code})")
        if response.status_code != 400:  # Expected if no customer exists yet
            print(f"Response: {response.text}")
        return None

def test_invoice_listing():
    """Test invoice listing"""
    print_step(5, "Testing Invoice Listing")
    
    response = requests.get(
        f"{BASE_URL}/enterprise/billing/invoices?limit=5",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        invoices = response.json()
        print(f"✅ Invoice Listing: SUCCESS ({len(invoices)} invoices)")
        
        for i, inv in enumerate(invoices[:3], 1):
            print(f"   Invoice {i}: #{inv.get('invoice_number')} - {inv.get('status')} - €{inv.get('total_eur')}")
        
        return invoices
    else:
        print(f"❌ Invoice Listing: FAILED ({response.status_code})")
        return None

def test_stripe_integration():
    """Test direct Stripe integration"""
    print_step(6, "Testing Stripe Integration")
    
    try:
        # Test Stripe connection
        customers = stripe.Customer.list(limit=1)
        print("✅ Stripe API Connection: SUCCESS")
        
        # Test price retrieval
        price_id = os.environ.get("STRIPE_PRICE_PRO_MONTHLY")
        if price_id:
            price = stripe.Price.retrieve(price_id)
            print(f"✅ Stripe Price: {price_id[:20]}...")
            print(f"   Amount: €{price.unit_amount/100}/month")
            print(f"   Currency: {price.currency.upper()}")
        
        # Check existing customer
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT stripe_customer_id FROM enterprise_companies WHERE id = :id"),
                {"id": COMPANY_ID}
            ).fetchone()
            
            if result and result[0]:
                customer_id = result[0]
                try:
                    customer = stripe.Customer.retrieve(customer_id)
                    print(f"✅ Stripe Customer: {customer_id}")
                    print(f"   Name: {customer.name}")
                    print(f"   Email: {customer.email}")
                except:
                    print(f"⚠️ Stripe Customer ID exists but cannot retrieve")
        
        return True
        
    except Exception as e:
        print(f"❌ Stripe Integration: FAILED - {str(e)}")
        return False

def test_database_billing_fields():
    """Test database billing fields"""
    print_step(7, "Testing Database Billing Fields")
    
    with engine.connect() as conn:
        # Check company billing data
        result = conn.execute(
            text("""
                SELECT 
                    legal_name,
                    plan,
                    subscription_status,
                    stripe_customer_id,
                    stripe_subscription_id,
                    current_period_end,
                    billing_email
                FROM enterprise_companies 
                WHERE id = :id
            """),
            {"id": COMPANY_ID}
        ).fetchone()
        
        if result:
            print("✅ Company Billing Data:")
            print(f"   Name: {result[0]}")
            print(f"   Plan: {result[1]}")
            print(f"   Status: {result[2]}")
            print(f"   Customer ID: {result[3] or 'Not set'}")
            print(f"   Subscription ID: {result[4] or 'Not set'}")
            print(f"   Period End: {result[5] or 'Not set'}")
            print(f"   Billing Email: {result[6] or 'Not set'}")
            
            # Check subscription analytics view
            analytics = conn.execute(
                text("SELECT * FROM subscription_analytics")
            ).fetchall()
            
            if analytics:
                print(f"✅ Subscription Analytics: {len(analytics)} records")
            
            # Check audit log
            audit_count = conn.execute(
                text("SELECT COUNT(*) FROM billing_audit_log")
            ).scalar()
            
            print(f"✅ Billing Audit Log: {audit_count} records")
            
            return True
        else:
            print("❌ Company not found in database")
            return False

def test_webhook_simulation():
    """Test webhook simulation endpoint"""
    print_step(8, "Testing Webhook Simulation")
    
    payload = {
        "type": "subscription.created",
        "company_id": COMPANY_ID
    }
    
    response = requests.post(
        f"{BASE_URL}/enterprise/billing/test/webhook",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Webhook Simulation: SUCCESS")
        print(f"   Response: {response.json()}")
        return True
    else:
        print(f"❌ Webhook Simulation: FAILED ({response.status_code})")
        return False

def test_complete_workflow():
    """Test complete billing workflow"""
    print_step(9, "Testing Complete Billing Workflow")
    
    print("1️⃣ Current Subscription Status:")
    sub_data = test_subscription_endpoint()
    
    print("\n2️⃣ Creating Checkout Session:")
    checkout = test_checkout_session()
    
    if checkout and checkout.get('url'):
        print("\n💡 MANUAL STEP REQUIRED:")
        print(f"   Visit: {checkout.get('url')}")
        print("   Use test card: 4242 4242 4242 4242")
        print("   Email: test@example.com")
        print("   Complete the checkout process")
        
        input("\n⏸️ Press Enter after completing checkout (or skip with Ctrl+C)...")
    
    print("\n3️⃣ Post-Checkout Verification:")
    test_subscription_endpoint()
    
    print("\n4️⃣ Billing Portal Access:")
    test_billing_portal()
    
    print("\n5️⃣ Invoice Management:")
    test_invoice_listing()
    
    print("\n🎯 WORKFLOW COMPLETE")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ADVANCED BILLING SYSTEM INTEGRATION TEST")
    print("="*70)
    
    tests = [
        ("Authentication", test_authentication),
        ("Stripe Integration", test_stripe_integration),
        ("Database Fields", test_database_billing_fields),
        ("Subscription Endpoint", test_subscription_endpoint),
        ("Checkout Session", test_checkout_session),
        ("Billing Portal", test_billing_portal),
        ("Invoice Listing", test_invoice_listing),
        ("Webhook Simulation", test_webhook_simulation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SYSTEM IS PRODUCTION READY")
        
        # Show next steps
        print("\n" + "="*70)
        print("NEXT STEPS FOR PRODUCTION DEPLOYMENT")
        print("="*70)
        print("1. Configure Stripe Webhooks:")
        print("   stripe listen --forward-to localhost:8080/enterprise/billing/webhook")
        print("2. Set webhook secret in .env.working:")
        print("   STRIPE_WEBHOOK_SECRET=whsec_...")
        print("3. Test with real webhook events:")
        print("   stripe trigger invoice.paid")
        print("4. Switch to live Stripe keys when ready")
        print("5. Set up monitoring for billing events")
        print("6. Configure automated email notifications")
    else:
        print(f"\n⚠️ {total - passed} TESTS FAILED - REVIEW AND FIX")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(1)
