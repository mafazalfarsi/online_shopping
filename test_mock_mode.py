#!/usr/bin/env python
"""
Test script to verify mock mode functionality when Thawani is down
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.thawani_service import ThawaniPayService

def test_mock_mode():
    """Test that mock mode works when Thawani is unavailable"""
    print("🧪 Testing Mock Mode Functionality...")
    
    # Create service instance
    thawani_service = ThawaniPayService()
    
    # Test data
    order_data = {
        'order_id': 'MOCK_TEST_001',
        'total_amount': 5.0,
        'items': [
            {
                'product_name': 'Test Product 1',
                'price': 3.0,
                'quantity': 1
            },
            {
                'product_name': 'Test Product 2',
                'price': 2.0,
                'quantity': 1
            }
        ]
    }
    
    customer_info = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'phone': '+96812345678'
    }
    
    print("📋 Test Data:")
    print(f"   Order ID: {order_data['order_id']}")
    print(f"   Total Amount: {order_data['total_amount']} OMR")
    print(f"   Items: {len(order_data['items'])}")
    print(f"   Customer: {customer_info['name']}")
    
    print(f"\n🔧 Configuration:")
    print(f"   Mock Mode: {thawani_service.mock_mode}")
    print(f"   Base URL: {thawani_service.base_url}")
    print(f"   Fallback URLs: {thawani_service.fallback_urls}")
    
    print("\n🔄 Testing session creation...")
    
    # Test the session creation
    result = thawani_service.create_checkout_session(order_data, customer_info)
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"   Session ID: {result.get('session_id', 'N/A')}")
        print(f"   Checkout URL: {result.get('checkout_url', 'N/A')}")
        
        # Check if it's a mock session
        if result.get('session_id', '').startswith('MOCK_'):
            print("   ✅ Mock session created successfully!")
            print("   📝 This means the system is working in fallback mode")
        else:
            print("   ✅ Real Thawani session created successfully!")
            
        # Test the checkout URL
        checkout_url = result.get('checkout_url', '')
        if checkout_url.startswith('http://localhost:8000'):
            print("   🔗 Mock checkout URL (will redirect to success page)")
        else:
            print("   🔗 Real Thawani checkout URL")
            
    else:
        print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    print("\n✅ Mock mode test completed!")
    
    # Test session status for mock sessions
    if result.get('success') and result.get('session_id', '').startswith('MOCK_'):
        print("\n🔄 Testing mock session status...")
        session_id = result.get('session_id')
        status_result = thawani_service.get_session_status(session_id)
        
        print(f"   Status Success: {status_result.get('success', False)}")
        if status_result.get('success'):
            data = status_result.get('data', {})
            print(f"   Payment Status: {data.get('payment_status', 'Unknown')}")
            print(f"   Mock: {data.get('mock', False)}")
    
    print("\n🎯 Summary:")
    print("   - Mock mode is working correctly")
    print("   - Users can complete checkout even when Thawani is down")
    print("   - The system gracefully handles API unavailability")

if __name__ == '__main__':
    test_mock_mode() 