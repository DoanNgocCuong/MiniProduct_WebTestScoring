import requests
import json

# Import config
# Add the parent directory to sys.path để import được config.py
import os
import sys

file_path = os.path.abspath(__file__) # Đường dẫn tuyệt đối đến file hiện tại
current_dir = os.path.dirname(file_path) # Đường dẫn đến thư mục hiện tại: APIBasicRAG_chatbot/backend_package
parent_dir = os.path.dirname(current_dir) # Đường dẫn đến thư mục cha của thư mục hiện tại: APIBasicRAG_chatbot
sys.path.append(parent_dir) # Thêm đường dẫn đến thư mục cha vào sys.path
import config  # Now we can import config from the parent directory 

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Define app credentials
app_DoanNgocCuong_id = os.getenv("APP_DOANNGOCCUONG_ID")
app_DoanNgocCuong_secret = os.getenv("APP_DOANNGOCCUONG_SECRET")

def get_tenant_access_token():
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({
        "app_id": app_DoanNgocCuong_id,
        "app_secret": app_DoanNgocCuong_secret
    })

    headers = {
        'Content-Type': 'application/json'
    }

    # Add this line to disable SSL certificate verification
    requests.packages.urllib3.disable_warnings()
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    return response.json().get('tenant_access_token')

# Example usage
if __name__ == "__main__":
    result = get_tenant_access_token()
    print(result)