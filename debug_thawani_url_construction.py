#!/usr/bin/env python
"""
Enhanced Debug Script for Thawani URL Construction and Session Creation
Tests the proper URL format: https://uatcheckout.thawani.om/pay/{session_id}?key={publishable_key}
"""

import os
import sys
import django
import json
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.thawani_service import ThawaniPayService
from django.conf import settings

def test_url_construction():
    """Test proper URL construction with publishable key"""
    print("🔧 Testing Thawani URL Construction...")
    
    # Get configuration
    secret_key = getattr(settings, 'THAWANI_SECRET_KEY', 'rRQ26GcsZzoEhbrP2HZvLYDbn9C9et')
    publishable_key = getattr(settings, 'THAWANI_PUBLISHABLE_KEY', 'HGvTMLDssJghr9tlN9gr4DVYt0qyBy')
    base_url = getattr(settings, 'THAWANI_BASE_URL', 'https://uatcheckout.thawani.om/api/v1')
    
    print(f"📋 Configuration:")
    print(f"   Secret Key: {secret_key[:10]}...{secret_key[-10:]}")
    print(f"   Publishable Key: {publishable_key}")
    print(f"   Base URL: {base_url}")
    
    # Test data
    order_data = {
        'order_id': 'URL_TEST_001',
        'total_amount': 1.0,
        'items': [
            {
                'product_name': 'URL Test Product',
                'price': 1.0,
                'quantity': 1
            }
        ]
    }
    
    customer_info = {
        'name': 'URL Test User',
        'email': 'url@example.com',
        'phone': '+96812345678'
    }
    
    print(f"\n📦 Test Data:")
    print(f"   Order ID: {order_data['order_id']}")
    print(f"   Amount: {order_data['total_amount']} OMR")
    print(f"   Customer: {customer_info['name']}")
    
    # Create service instance
    thawani_service = ThawaniPayService()
    
    print(f"\n🔄 Testing session creation with enhanced debugging...")
    
    # Test the session creation
    result = thawani_service.create_checkout_session(order_data, customer_info)
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.get('success', False)}")
    
    if result.get('success'):
        session_id = result.get('session_id')
        checkout_url = result.get('checkout_url')
        
        print(f"   Session ID: {session_id}")
        print(f"   Checkout URL: {checkout_url}")
        
        # Validate URL format
        if checkout_url:
            print(f"\n🔍 URL Analysis:")
            
            # Check if URL contains session_id
            if session_id in checkout_url:
                print(f"   ✅ Session ID found in URL")
            else:
                print(f"   ❌ Session ID missing from URL")
            
            # Check if URL contains publishable key
            if f"key={publishable_key}" in checkout_url:
                print(f"   ✅ Publishable key found in URL")
            else:
                print(f"   ❌ Publishable key missing from URL")
            
            # Check URL format
            if checkout_url.startswith('https://uatcheckout.thawani.om/pay/') or checkout_url.startswith('https://checkout.thawani.om/pay/'):
                print(f"   ✅ Correct domain format")
            else:
                print(f"   ❌ Incorrect domain format")
            
            # Test URL accessibility
            print(f"\n🌐 Testing URL accessibility...")
            try:
                response = requests.head(checkout_url, timeout=10, allow_redirects=True)
                print(f"   Status Code: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ URL is accessible")
                else:
                    print(f"   ⚠️ URL returned status {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error accessing URL: {str(e)}")
        
        # Test session validation
        print(f"\n🔍 Testing session validation...")
        try:
            validation_result = thawani_service._validate_session(session_id)
            print(f"   Validation Success: {validation_result.get('success', False)}")
            if not validation_result.get('success'):
                print(f"   Validation Error: {validation_result.get('error', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Validation Error: {str(e)}")
        
    else:
        print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n✅ URL construction test completed!")
    
    # Test manual URL construction
    print(f"\n🔧 Testing manual URL construction...")
    test_session_id = "test_session_123"
    
    # Correct format
    correct_url = f"https://uatcheckout.thawani.om/pay/{test_session_id}?key={publishable_key}"
    print(f"   ✅ Correct URL format: {correct_url}")
    
    # Wrong formats (for comparison)
    wrong_url1 = f"https://uatcheckout.thawani.om/pay/{test_session_id}"
    wrong_url2 = f"https://uatcheckout.thawani.om/pay/{test_session_id}?publishable_key={publishable_key}"
    
    print(f"   ❌ Wrong format (no key): {wrong_url1}")
    print(f"   ❌ Wrong format (wrong param): {wrong_url2}")

def test_api_response_structure():
    """Test different API response structures"""
    print(f"\n🧪 Testing API Response Structure...")
    
    thawani_service = ThawaniPayService()
    
    # Test payload
    payload = {
        "client_reference_id": "STRUCTURE_TEST_001",
        "products": [
            {
                "name": "Structure Test Product",
                "unit_amount": 1000,  # 1 OMR in baisa
                "quantity": 1
            }
        ],
        "total_amount": 1000,
        "currency": "OMR",
        "success_url": f"{settings.BASE_URL}/thawani/success/",
        "cancel_url": f"{settings.BASE_URL}/thawani/cancel/",
        "metadata": {
            "Customer name": "Structure Test User",
            "Contact number": "+96812345678",
            "Email address": "structure@example.com",
            "order_id": "STRUCTURE_TEST_001"
        }
    }
    
    print(f"📦 Test Payload:")
    print(json.dumps(payload, indent=2))
    
    # Make direct API call
    headers = {
        'thawani-api-key': thawani_service.secret_key,
        'Content-Type': 'application/json'
    }
    
    url = f"{thawani_service.base_url}/checkout/session"
    
    print(f"\n🌐 Making API call to: {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! Response structure:")
            print(json.dumps(result, indent=2))
            
            # Analyze response structure
            print(f"\n🔍 Response Structure Analysis:")
            
            # Check for session_id
            session_id = None
            if 'data' in result and 'session_id' in result['data']:
                session_id = result['data']['session_id']
                print(f"   ✅ Found session_id in data.data: {session_id}")
            elif 'session_id' in result:
                session_id = result['session_id']
                print(f"   ✅ Found session_id in root: {session_id}")
            elif 'id' in result:
                session_id = result['id']
                print(f"   ✅ Found session_id as 'id': {session_id}")
            else:
                print(f"   ❌ No session_id found in response")
            
            # Check for payment_url
            payment_url = None
            if 'data' in result and 'payment_url' in result['data']:
                payment_url = result['data']['payment_url']
                print(f"   ✅ Found payment_url in data.data: {payment_url}")
            elif 'payment_url' in result:
                payment_url = result['payment_url']
                print(f"   ✅ Found payment_url in root: {payment_url}")
            else:
                print(f"   ⚠️ No payment_url found in response")
            
            # Construct proper URL
            if session_id:
                if payment_url:
                    final_url = payment_url
                    print(f"   📝 Using payment_url from response: {final_url}")
                else:
                    final_url = f"https://uatcheckout.thawani.om/pay/{session_id}?key={thawani_service.publishable_key}"
                    print(f"   📝 Constructed URL: {final_url}")
                
                # Test URL
                print(f"\n🌐 Testing constructed URL...")
                try:
                    url_response = requests.head(final_url, timeout=10, allow_redirects=True)
                    print(f"   Status Code: {url_response.status_code}")
                    if url_response.status_code == 200:
                        print(f"   ✅ URL is accessible")
                    else:
                        print(f"   ⚠️ URL returned status {url_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Error accessing URL: {str(e)}")
            
        else:
            print(f"   ❌ Error! Response:")
            print(response.text)
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

if __name__ == '__main__':
    print("🚀 Enhanced Thawani URL Construction Debug Script")
    print("=" * 60)
    
    test_url_construction()
    test_api_response_structure()
    
    print("\n" + "=" * 60)
    print("✅ Debug script completed!")
    print("\n📝 Summary:")
    print("   - Tests proper URL format with publishable key")
    print("   - Validates session creation and response structure")
    print("   - Checks URL accessibility")
    print("   - Provides detailed error analysis") 