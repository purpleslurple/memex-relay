#!/usr/bin/env python3
"""
Test script for Memex Relay API
"""
import asyncio
import httpx
import json

API_BASE = "http://127.0.0.1:5000"
API_TOKEN = "memex-dev-token-2025"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        print("Testing Memex Relay API...")
        
        # Test health check
        print("\n1. Health check:")
        try:
            response = await client.get(f"{API_BASE}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test list notebooks
        print("\n2. List notebooks:")
        try:
            response = await client.get(f"{API_BASE}/v1/notebooks", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Notebooks: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test search
        print("\n3. Search test:")
        try:
            search_data = {"query": "HHMH mandrel", "limit": 5}
            response = await client.post(
                f"{API_BASE}/v1/search", 
                headers=headers, 
                json=search_data
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Results: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test get page
        print("\n4. Get page test:")
        try:
            page_data = {"page_id": "sample-page-id-123"}
            response = await client.post(
                f"{API_BASE}/v1/get_page", 
                headers=headers, 
                json=page_data
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Page: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())