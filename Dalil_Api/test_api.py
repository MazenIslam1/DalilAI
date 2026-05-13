"""
Quick API Test Script
=====================
Run this to test the full Dalil AI flow:
  1. Upload a CSV
  2. Ask a question
  3. See the AI response
"""

import json
import urllib.request
import os
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "change_this_to_a_random_secret_key"  # matches .env

def test_health():
    print("=" * 50)
    print("1. Testing /health ...")
    req = urllib.request.Request(f"{BASE_URL}/health")
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"   ✅ Status: {data['status']}")
    print(f"   App: {data['app']} v{data['version']}")
    print()

def test_upload():
    print("=" * 50)
    print("2. Uploading sample CSV ...")

    # Create a sample CSV in memory
    csv_content = """product,sales,price,date,region,category
Widget A,1500,29.99,2025-01-15,North,Electronics
Widget B,2300,49.99,2025-01-20,South,Electronics
Widget C,800,19.99,2025-02-01,North,Home
Widget A,1800,29.99,2025-02-10,East,Electronics
Widget D,3200,99.99,2025-02-15,West,Premium
Widget B,2100,49.99,2025-03-01,South,Electronics
Widget E,450,9.99,2025-03-05,North,Accessories
Widget C,950,19.99,2025-03-10,East,Home
Widget A,2200,29.99,2025-03-20,North,Electronics
Widget D,2800,99.99,2025-04-01,West,Premium""".encode("utf-8")

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"------FormBoundary7MA4YWxkTrZu0gW\r\n"
        f'Content-Disposition: form-data; name="file"; filename="sample_sales.csv"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode() + csv_content + b"\r\n------FormBoundary7MA4YWxkTrZu0gW--\r\n"

    req = urllib.request.Request(
        f"{BASE_URL}/api/files/upload",
        data=body,
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": f"multipart/form-data; boundary=----FormBoundary7MA4YWxkTrZu0gW",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"   ✅ Upload successful!")
        print(f"   Dataset ID: {data['dataset_id']}")
        print(f"   Rows: {data['rows']}, Columns: {data['columns']}")
        print(f"   Columns: {data['column_names']}")
        print()
        return data["dataset_id"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"   ❌ Upload failed: {e.code} - {error_body}")
        print()
        return None

def test_chat(dataset_id):
    print("=" * 50)
    print("3. Asking Dalil AI a question ...")
    print('   Question: "What are the top 3 products by total sales?"')
    print()

    payload = json.dumps({
        "message": "What are the top 3 products by total sales?",
        "dataset_id": dataset_id,
    }).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/",
        data=payload,
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"   ✅ Dalil AI Response:")
        print(f"   Conversation ID: {data['conversation_id']}")
        print(f"   Tokens used: {data.get('tokens_used', 'N/A')}")
        print()
        print("   --- AI Message ---")
        print(data["message"][:1500])
        print()
        return data["conversation_id"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"   ❌ Chat failed: {e.code} - {error_body}")
        return None

def test_datasets():
    print("=" * 50)
    print("4. Listing all datasets ...")

    req = urllib.request.Request(
        f"{BASE_URL}/api/datasets/",
        headers={"X-API-Key": API_KEY},
    )

    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"   ✅ Found {len(data)} dataset(s)")
    for d in data:
        print(f"   - {d['filename']} ({d['row_count']} rows, {d['column_count']} cols)")
    print()


if __name__ == "__main__":
    print()
    print("🚀 Dalil AI - API Test")
    print("=" * 50)
    print()

    test_health()
    dataset_id = test_upload()

    if dataset_id:
        test_datasets()
        test_chat(dataset_id)

    print("=" * 50)
    print("✅ Test complete!")
