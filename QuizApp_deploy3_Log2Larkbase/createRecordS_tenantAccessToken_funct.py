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

app_base_token = config.APP_BASE_TOKEN  # Your app_token
base_table_id = config.BASE_TABLE_ID  # Your table_id


# Get tenant access token
tenant_access_token = get_tenant_access_token()
print("tenant_access_token:", tenant_access_token)


records_fields_json = {
  "records": [
    {
      "fields": {
        "Multi-select column": [
          "Option1",
          "Option2"
        ],
        "conversation_id": "Example Text 1"
      }
    },
    {
      "fields": {
        "Multi-select column": [
          "Option3",
          "Option4"
        ],
        "conversation_id": "Example Text 2"
      }
    }
  ]
}


def create_many_records(app_base_token, base_table_id, tenant_access_token, records_fields_json):
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_base_token}/tables/{base_table_id}/records/batch_create?user_id_type=user_id"
    payload = json.dumps(records_fields_json)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {tenant_access_token}'
    }

    # Add this line to disable SSL certificate verification
    requests.packages.urllib3.disable_warnings()
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    
    # Log response status and text for debugging
    print(f"Response status code: {response.status_code}")
    print(f"Response json: {response.json()}")
    return response

create_many_records(app_base_token, base_table_id, tenant_access_token, records_fields_json)
