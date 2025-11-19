"""
Test script for toggling materials_ordered status
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_toggle_materials_ordered(quotation_id):
    """Test toggling the materials_ordered status"""
    print(f"\n=== Testing Toggle Materials Ordered for ID: {quotation_id} ===")
    
    # Get current quotation status
    print("\n1. Getting current quotation:")
    response = requests.get(f"{BASE_URL}/quotations/{quotation_id}")
    if response.status_code == 200:
        quotation = response.json()
        print(f"   Current materials_ordered: {quotation.get('materials_ordered', 'N/A')}")
    else:
        print(f"   Error: {response.status_code}")
        return
    
    # Toggle the status
    print("\n2. Toggling materials_ordered status:")
    response = requests.put(f"{BASE_URL}/quotations/{quotation_id}/toggle-materials-ordered")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        print(f"   ✓ New materials_ordered status: {result['materials_ordered']}")
    else:
        print(f"   Error: {response.json()}")
        return
    
    # Verify the change
    print("\n3. Verifying the change:")
    response = requests.get(f"{BASE_URL}/quotations/{quotation_id}")
    if response.status_code == 200:
        quotation = response.json()
        print(f"   Verified materials_ordered: {quotation.get('materials_ordered', 'N/A')}")
    
    # Toggle back
    print("\n4. Toggling back:")
    response = requests.put(f"{BASE_URL}/quotations/{quotation_id}/toggle-materials-ordered")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Materials_ordered toggled back to: {result['materials_ordered']}")

def get_first_quotation_id():
    """Get the first quotation ID from the database"""
    print("\n=== Getting First Quotation ID ===")
    response = requests.get(f"{BASE_URL}/quotations?limit=1")
    
    if response.status_code == 200:
        quotations = response.json()
        if quotations:
            quotation_id = quotations[0].get('id')
            print(f"Found quotation ID: {quotation_id}")
            return quotation_id
        else:
            print("No quotations found in database")
            return None
    else:
        print(f"Error fetching quotations: {response.status_code}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("TOGGLE MATERIALS ORDERED STATUS TEST")
    print("=" * 60)
    
    # Test health check
    print("\n=== Testing API Health ===")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print(f"✓ API is healthy: {response.json()}")
    else:
        print("✗ API is not responding")
        exit(1)
    
    # Get first quotation ID
    quotation_id = get_first_quotation_id()
    
    if quotation_id:
        # Test toggle functionality
        test_toggle_materials_ordered(quotation_id)
    else:
        print("\n⚠ No quotations available to test.")
        print("Please create a quotation first using POST /quotations/generate")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
