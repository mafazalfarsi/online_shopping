#!/usr/bin/env python
"""
Test script to verify Thawani error handling improvements
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.thawani_service import ThawaniPayService

def test_error_handling():
    """Test the improved error handling"""
    print("🧪 Testing Thawani Error Handling...")
    
    # Create service instance
    thawani_service = ThawaniPayService()
    
    # Test data
    order_data = {
        'order_id': 'TEST_ERROR_001',
        'total_amount': 1.0,
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
    
    print("\n🔄 Testing session creation with error handling...")
    
    # Test the session creation
    result = thawani_service.create_checkout_session(order_data, customer_info)
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"   Session ID: {result.get('session_id', 'N/A')}")
        print(f"   Checkout URL: {result.get('checkout_url', 'N/A')}")
        if result.get('mock_mode'):
            print("   ✅ Mock mode activated due to API unavailability")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("\n✅ Error handling test completed!")
    
    # Test the fallback mechanism
    print("\n🔄 Testing fallback mechanism...")
    
    # Temporarily disable mock mode to test fallback
    original_mock_mode = thawani_service.mock_mode
    thawani_service.mock_mode = False
    
    # Test with all endpoints failing
    fallback_result = thawani_service._make_request_with_fallback('test-endpoint', 'GET')
    
    print(f"   Fallback result: {fallback_result}")
    
    # Restore mock mode
    thawani_service.mock_mode = original_mock_mode
    
    print("\n✅ Fallback test completed!")

if __name__ == '__main__':
    test_error_handling() 