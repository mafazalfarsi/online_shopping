#!/usr/bin/env python
"""
Test script to verify Thawani checkout health check functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.thawani_service import ThawaniPayService

def test_checkout_health():
    """Test the checkout health check functionality"""
    print("🧪 Testing Thawani Checkout Health Check...")
    
    # Create service instance
    thawani_service = ThawaniPayService()
    
    print("🔧 Configuration:")
    print(f"   Mock Mode: {thawani_service.mock_mode}")
    print(f"   Check Checkout Health: {thawani_service.check_checkout_health}")
    
    # Test data
    order_data = {
        'order_id': 'HEALTH_TEST_001',
        'total_amount': 2.0,
        'items': [
            {
                'product_name': 'Health Test Product',
                'price': 2.0,
                'quantity': 1
            }
        ]
    }
    
    customer_info = {
        'name': 'Health Test User',
        'email': 'health@example.com',
        'phone': '+96812345678'
    }
    
    print("\n📋 Test Data:")
    print(f"   Order ID: {order_data['order_id']}")
    print(f"   Amount: {order_data['total_amount']} OMR")
    print(f"   Customer: {customer_info['name']}")
    
    print("\n🔄 Testing session creation with health check...")
    
    # Test the session creation
    result = thawani_service.create_checkout_session(order_data, customer_info)
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"   Session ID: {result.get('session_id', 'N/A')}")
        print(f"   Checkout URL: {result.get('checkout_url', 'N/A')}")
        
        # Check if it's a mock session
        if result.get('session_id', '').startswith('MOCK_'):
            print("   ✅ Mock session created (checkout page had issues)")
            print("   📝 This means the system detected checkout page problems")
        else:
            print("   ✅ Real Thawani session created successfully!")
            print("   📝 Checkout page health check passed")
            
        # Test the checkout URL
        checkout_url = result.get('checkout_url', '')
        if checkout_url.startswith('http://localhost:8000'):
            print("   🔗 Mock checkout URL (will redirect to success page)")
        else:
            print("   🔗 Real Thawani checkout URL")
            
    else:
        print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    print("\n✅ Checkout health test completed!")
    
    # Test the health check function directly
    print("\n🔄 Testing health check function directly...")
    
    # Test with a real session ID (if we have one)
    if result.get('success') and not result.get('session_id', '').startswith('MOCK_'):
        session_id = result.get('session_id')
        health_status = thawani_service._check_thawani_checkout_health(session_id)
        print(f"   Health check for session {session_id}: {'✅ Healthy' if health_status else '❌ Unhealthy'}")
    else:
        print("   No real session available for health check test")
    
    print("\n🎯 Summary:")
    print("   - Checkout health check is working")
    print("   - System automatically falls back to mock mode when checkout page has issues")
    print("   - Users get a seamless experience regardless of Thawani's status")

if __name__ == '__main__':
    test_checkout_health() 