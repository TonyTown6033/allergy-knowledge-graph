import requests
import os
import json
import sys

def test_upload(file_path, server_url="http://localhost:5001"):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    print(f"Testing upload for: {file_path}")
    print(f"Server URL: {server_url}")

    url = f"{server_url}/api/articles/upload"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(url, files=files)
            
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            print("\n✅ Upload and analysis successful!")
            print(f"Extracted {result['data']['claims_count']} claims and {result['data']['evidence_count']} evidences.")
        else:
            print(f"\n❌ Upload failed: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Error during request: {str(e)}")

if __name__ == "__main__":
    test_file = "./过敏原特异性IgE抗体检测及其临床规范化应用-韩彦熙.pdf"
    test_upload(test_file)
