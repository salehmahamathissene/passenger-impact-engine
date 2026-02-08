#!/usr/bin/env python3
import requests
import json
import sys
import argparse
from datetime import datetime

BASE_URL = "http://localhost:8080"


def list_orders(limit=10):
    """List recent orders"""
    resp = requests.get(f"{BASE_URL}/pro/orders?limit={limit}")
    if resp.status_code == 200:
        orders = resp.json()
        print(f"\n📦 Recent Orders (showing {len(orders)}):")
        print("=" * 80)
        for order in orders:
            status_icon = {
                'paid': '✅',
                'pending': '⏳',
                'failed': '❌'
            }.get(order['status'], '❓')
            
            print(f"{status_icon} #{order['id']:4d} {order['email'][:30]:30} {order['plan']:12} €{order['amount_cents']/100:8.2f} {order['status']:10} {order['created_at'][:19]}")
    else:
        print(f"❌ Failed to get orders: {resp.status_code}")


def get_order(order_id):
    """Get order details"""
    resp = requests.get(f"{BASE_URL}/pro/orders/{order_id}")
    if resp.status_code == 200:
        order = resp.json()
        print(f"\n📄 Order #{order_id} Details:")
        print("=" * 80)
        print(f"   Email: {order['email']}")
        print(f"   Plan: {order['plan']}")
        print(f"   Amount: €{order['amount_cents']/100:.2f}")
        print(f"   Status: {order['status']}")
        print(f"   Created: {order['created_at']}")
        
        if order.get('stripe_checkout_session_id'):
            print(f"   Stripe Session: {order['stripe_checkout_session_id']}")
        
        if order.get('job'):
            job = order['job']
            print(f"\n   📊 Job Status: {job['status']}")
            if job.get('artifact_path'):
                print(f"   📁 Artifact: {job['artifact_path']}")
            if job.get('runs_completed'):
                print(f"   🔢 Runs Completed: {job['runs_completed']:,}")
            if job.get('processing_time_ms'):
                print(f"   ⏱️  Processing Time: {job['processing_time_ms']:,}ms")
            if job.get('error'):
                print(f"   ❌ Error: {job['error'][:200]}...")
    else:
        print(f"❌ Order not found: {resp.status_code}")


def create_order(email, plan):
    """Create a new order"""
    data = {"email": email, "plan": plan}
    resp = requests.post(f"{BASE_URL}/pro/checkout", json=data)
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"\n✅ Order created!")
        print(f"   Order ID: {result.get('order_id')}")
        print(f"   Email: {email}")
        print(f"   Plan: {plan}")
        
        if 'checkout_url' in result:
            print(f"   🔗 Checkout URL: {result['checkout_url']}")
        elif 'test_payment_url' in result:
            print(f"   🔗 Test Payment: {BASE_URL}{result['test_payment_url']}")
        
        return result.get('order_id')
    else:
        print(f"❌ Failed to create order: {resp.status_code}")
        print(f"   Response: {resp.text}")
        return None


def mark_paid(order_id):
    """Mark order as paid (test mode)"""
    resp = requests.post(f"{BASE_URL}/pro/test-pay/{order_id}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"\n✅ {result['message']}")
        print(f"   Job queued: {result.get('job_queued', False)}")
    else:
        print(f"❌ Failed to mark as paid: {resp.status_code}")


def system_status():
    """Check system status"""
    print("\n🔍 System Status:")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"✅ API: {resp.json().get('status')}")
    except:
        print("❌ API: Offline")
    
    try:
        resp = requests.get(f"{BASE_URL}/pro/health")
        print(f"✅ Pro API: {resp.json().get('status')}")
    except:
        print("❌ Pro API: Offline")
    
    # Check database
    try:
        resp = requests.get(f"{BASE_URL}/pro/orders?limit=1")
        orders = resp.json()
        print(f"✅ Database: Connected ({len(orders)} orders)")
    except:
        print("❌ Database: Connection failed")


def main():
    parser = argparse.ArgumentParser(description="PIE Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List orders
    list_parser = subparsers.add_parser("list", help="List recent orders")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of orders to show")
    
    # Get order
    get_parser = subparsers.add_parser("get", help="Get order details")
    get_parser.add_argument("order_id", type=int, help="Order ID")
    
    # Create order
    create_parser = subparsers.add_parser("create", help="Create a new order")
    create_parser.add_argument("email", help="Customer email")
    create_parser.add_argument("plan", choices=["starter", "pro", "enterprise"], help="Plan type")
    
    # Mark paid
    pay_parser = subparsers.add_parser("pay", help="Mark order as paid (test mode)")
    pay_parser.add_argument("order_id", type=int, help="Order ID")
    
    # Status
    subparsers.add_parser("status", help="Check system status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "list":
            list_orders(args.limit)
        elif args.command == "get":
            get_order(args.order_id)
        elif args.command == "create":
            create_order(args.email, args.plan)
        elif args.command == "pay":
            mark_paid(args.order_id)
        elif args.command == "status":
            system_status()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is it running?")
        print("   Start with: systemctl --user start pie-api.service")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
