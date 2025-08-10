#!/usr/bin/env python
"""
Debug Thawani session issues
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.thawani_service import ThawaniPayService

def debug_thawani_session():
    """Debug Thawani session creation and validation"""
    print("🔍 Debugging Thawani Session Issues...")
    
    # Create service instance
    thawani_service = ThawaniPayService()
    
    # Test with minimal data
    order_data = {
        'order_id': 'DEBUG_TEST_001',
        'total_amount': 1.0,  # 1 OMR
        'items': [
            {
                'product_name': 'Test Product',
                'price': 1.0,
                'quantity': 1
            }
        ]
    }
    
    customer_info = {
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '+96812345678'
    }
    
    print("📋 Test Data:")
    print(f"   Order ID: {order_data['order_id']}")
    print(f"   Amount: {order_data['total_amount']} OMR")
    print(f"   Customer: {customer_info['name']}")
    
    # Step 1: Create session
    print("\n🔄 Step 1: Creating session...")
    result = thawani_service.create_checkout_session(order_data, customer_info)
    
    if result['success']:
        session_id = result['session_id']
        checkout_url = result['checkout_url']
        
        print("✅ Session created successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   Checkout URL: {checkout_url}")
        
        # Step 2: Validate session immediately
        print("\n🔄 Step 2: Validating session...")
        status_result = thawani_service.get_session_status(session_id)
        
        if status_result['success']:
            session_data = status_result['data']
            print("✅ Session validation successful!")
            print(f"   Payment Status: {session_data.get('payment_status', 'Unknown')}")
            print(f"   Invoice: {session_data.get('invoice', 'Unknown')}")
            print(f"   Created At: {session_data.get('created_at', 'Unknown')}")
            print(f"   Expires At: {session_data.get('expire_at', 'Unknown')}")
            
            # Check if session is valid
            if session_data.get('payment_status') == 'unpaid':
                print("✅ Session is valid and ready for payment")
            else:
                print(f"⚠️  Session status: {session_data.get('payment_status')}")
        else:
            print(f"❌ Session validation failed: {status_result['error']}")
        
        # Step 3: Test the checkout URL
        print(f"\n🌐 Test the checkout URL manually:")
        print(f"   {checkout_url}")
        print("\n📝 Instructions:")
        print("   1. Copy the URL above")
        print("   2. Open it in a new browser tab")
        print("   3. Check if it loads properly")
        print("   4. If it shows 404, the issue is with Thawani's UAT environment")
        
    else:
        print(f"❌ Session creation failed: {result['error']}")

if __name__ == "__main__":
    debug_thawani_session() 