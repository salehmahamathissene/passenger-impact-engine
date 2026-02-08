import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

stripe_key = os.environ.get('STRIPE_SECRET_KEY')
print(f"Stripe Key: {stripe_key[:20]}...{stripe_key[-20:] if stripe_key and len(stripe_key) > 40 else ''}")
print(f"Length: {len(stripe_key) if stripe_key else 0}")

# Try to use Stripe
try:
    import stripe
    stripe.api_key = stripe_key
    
    # Simple test
    from datetime import datetime
    print(f"Testing at {datetime.now().isoformat()}")
    
    # List charges (limit 1)
    try:
        charges = stripe.Charge.list(limit=1)
        print("✅ Stripe API key is VALID")
        print(f"   Test successful: Found {len(charges.data)} charges")
    except stripe.error.AuthenticationError as e:
        print(f"❌ Stripe Authentication Error: {e}")
    except Exception as e:
        print(f"⚠️  Other Stripe error: {e}")
        
except ImportError:
    print("❌ Stripe module not installed")
    print("Install: pip install stripe")
except Exception as e:
    print(f"❌ Error: {e}")
