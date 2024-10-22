import requests
import json
import os
import sys

# Add the parent directory to sys.path để import được config.py
file_path = os.path.abspath(__file__) # Đường dẫn tuyệt đối đến file hiện tại
current_dir = os.path.dirname(file_path) # Đường dẫn đến thư mục hiện tại: APIBasicRAG_chatbot/backend_package
parent_dir = os.path.dirname(current_dir) # Đường dẫn đến thư mục cha của thư mục hiện tại: APIBasicRAG_chatbot
sys.path.append(parent_dir) # Thêm đường dẫn đến thư mục cha vào sys.path
import config  # Now we can import config from the parent directory 

# Import các module từ backend_package sau
from get_tenantAccessToken_funct import get_tenant_access_token
from createRecord_tenantAccessToken_funct import create_record

app_base_token = config.APP_BASE_TOKEN  # Your app_token
base_table_id = config.BASE_TABLE_ID  # Your table_id


fields_json = {
    "fields": {
        "user_name": "Example Text",
        "stt": 1
    }
}


def create_record_with_checkTenantAccessToken(app_base_token, base_table_id, fields_json):

    # Get tenant_access_token from storage or generate a new one
    try:
        # Attempt to retrieve tenant_access_token from storage (e.g., file or database)
        # For this example, we'll assume it's stored in a file named 'tenantAccessToken_storage.txt'
        with open('tenantAccessToken_storage.txt', 'r') as file:
            tenant_access_token = file.read().strip()
            print("Tenant token from storage:", tenant_access_token)  # Log token retrieved from file
    except FileNotFoundError:
        # If the file doesn't exist, generate a new token
        tenant_access_token = get_tenant_access_token()
        print("Generated new tenant_access_token:", tenant_access_token)

    # Try to create a record
    try:
        response = create_record(app_base_token, base_table_id, tenant_access_token, fields_json)
        
        # Check if response indicates an invalid token
        if response.status_code == 401 or (response.json().get("code") == 99991663 or "Invalid access token" in response.json().get("msg", "")):
            print("Invalid access token or token expired, getting a new token...")
            tenant_access_token = get_tenant_access_token()
            print("New tenant_access_token:", tenant_access_token)
            # Try creating the record again with the new token
            response = create_record(app_base_token, base_table_id, tenant_access_token, fields_json)
        else:
            print("Record created successfully.")
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        raise
    
    # Save the (potentially new) tenant_access_token to storage
    with open('tenantAccessToken_storage.txt', 'w') as file:
        file.write(tenant_access_token)

    print("Final tenant_access_token:", tenant_access_token)
    
create_record_with_checkTenantAccessToken(app_base_token, base_table_id, fields_json)
