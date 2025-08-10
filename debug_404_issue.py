#!/usr/bin/env python
"""
Debug 404 issue with Thawani checkout
"""

import requests
import json
import time
from datetime import datetime

def debug_404_issue():
    """Debug the 404 issue step by step"""
    print("🔍 Debugging 404 Issue...")
    
    # Thawani configuration
    secret_key = 'rRQ26GcsZzoEhbrP2HZvLYDbn9C9et'
    base_url = 'https://uatcheckout.thawani.om/api/v1'
    
    # Create fresh payload
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    payload = {
        "client_reference_id": f"DEBUG_404_{timestamp}",
        "products": [
            {
                "name": "Test Product",
                "unit_amount": 1000,
                "quantity": 1
            }
        ],
        "total_amount": 1000,
        "currency": "OMR",
        "success_url": "http://localhost:8000/thawani/success/",
        "cancel_url": "http://localhost:8000/thawani/cancel/",
        "metadata": {
            "Customer name": "Test User",
            "Contact number": "+96812345678",
            "Email address": "test@example.com",
            "order_id": f"DEBUG_404_{timestamp}"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'thawani-api-key': secret_key
    }
    
    print(f"📋 Test Details:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Order ID: {payload['client_reference_id']}")
    print(f"   Amount: {payload['total_amount']} baisa ({payload['total_amount']/1000} OMR)")
    
    try:
        # Step 1: Create session
        print(f"\n🔄 Step 1: Creating session...")
        response = requests.post(
            f"{base_url}/checkout/session",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response Data: {json.dumps(data, indent=2)}")
            
            if 'data' in data and 'session_id' in data['data']:
                session_id = data['data']['session_id']
                session_data = data['data']
                
                print(f"\n✅ Session created successfully!")
                print(f"   Session ID: {session_id}")
                print(f"   Payment Status: {session_data.get('payment_status', 'Unknown')}")
                print(f"   Invoice: {session_data.get('invoice', 'Unknown')}")
                print(f"   Created At: {session_data.get('created_at', 'Unknown')}")
                print(f"   Expires At: {session_data.get('expire_at', 'Unknown')}")
                
                # Step 2: Test different URL formats
                print(f"\n🔄 Step 2: Testing URL formats...")
                
                url_formats = [
                    f"https://uatcheckout.thawani.om/pay/{session_id}",
                    f"https://uatcheckout.thawani.om/pay/{session_id}/",
                    f"https://uatcheckout.thawani.om/checkout/{session_id}",
                    f"https://uatcheckout.thawani.om/checkout/{session_id}/",
                    f"https://uatcheckout.thawani.om/session/{session_id}",
                    f"https://uatcheckout.thawani.om/session/{session_id}/"
                ]
                
                for i, url in enumerate(url_formats, 1):
                    print(f"\n   Test {i}: {url}")
                    try:
                        url_response = requests.head(url, timeout=10, allow_redirects=True)
                        print(f"   Status: {url_response.status_code}")
                        print(f"   Final URL: {url_response.url}")
                        
                        if url_response.status_code == 200:
                            print(f"   ✅ SUCCESS! This URL works!")
                            print(f"\n🎯 Use this URL:")
                            print(f"   {url}")
                            return url
                        elif url_response.status_code == 302:
                            print(f"   🔄 Redirect to: {url_response.headers.get('Location', 'Unknown')}")
                        else:
                            print(f"   ❌ Failed with status {url_response.status_code}")
                            
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")
                
                # Step 3: Check session status via API
                print(f"\n🔄 Step 3: Checking session status via API...")
                status_response = requests.get(
                    f"{base_url}/checkout/session/{session_id}",
                    headers={'thawani-api-key': secret_key},
                    timeout=30
                )
                
                print(f"Status API Response: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Session Status: {json.dumps(status_data, indent=2)}")
                else:
                    print(f"Status API Error: {status_response.text}")
                
                print(f"\n⚠️  All URL formats failed. This suggests:")
                print(f"   1. Session might not be immediately available")
                print(f"   2. Thawani UAT environment might have issues")
                print(f"   3. URL format might be different")
                
            else:
                print(f"❌ No session_id in response")
                print(f"Response: {data}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_404_issue() 