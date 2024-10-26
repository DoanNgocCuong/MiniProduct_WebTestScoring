import requests
import json
import os
import sys
from dotenv import load_dotenv
import aiohttp

# Add the parent directory to sys.path to import config.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import config

class LarkBaseOperations:
    def __init__(self):
        load_dotenv()
        self.app_base_token = config.APP_BASE_TOKEN
        self.base_table_id = config.BASE_TABLE_ID
        self.app_id = os.getenv("APP_DOANNGOCCUONG_ID")
        self.app_secret = os.getenv("APP_DOANNGOCCUONG_SECRET")
        self.tenant_access_token = None

    async def get_tenant_access_token(self):
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        payload = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    self.tenant_access_token = data.get('tenant_access_token')
                    if not self.tenant_access_token:
                        print("Error: Received 200 status but no tenant_access_token in response")
                        print(f"Response: {data}")
                else:
                    print(f"Error getting tenant access token. Status code: {response.status}")
                    response_json = await response.json()
                    print(f"Response: {response_json}")
                    self.tenant_access_token = None
                
                return self.tenant_access_token

    async def create_many_records(self, records_fields_json):
        url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{self.app_base_token}/tables/{self.base_table_id}/records/batch_create?user_id_type=user_id"
        payload = json.dumps(records_fields_json)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.tenant_access_token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload, ssl=False) as response:
                print(f"Response status code: {response.status}")
                response_json = await response.json()
                print(f"Response body: {response_json}")
                return response

    async def create_many_records_with_checkTenantAccessToken(self, records_fields_json):
        try:
            with open('tenantAccessToken_storage.txt', 'r') as file:
                self.tenant_access_token = file.read().strip()
                if not self.tenant_access_token:
                    raise FileNotFoundError
            print("Tenant token from storage:", self.tenant_access_token)
        except FileNotFoundError:
            self.tenant_access_token = await self.get_tenant_access_token()
            if not self.tenant_access_token:
                print("Failed to get a new tenant_access_token")
                return None
            print("Created new tenant_access_token:", self.tenant_access_token)

        try:
            response = await self.create_many_records(records_fields_json)
            response_json = await response.json()
            
            if response.status in [400, 401] or (response_json.get("code") in [99991661, 99991663, 99991668] or "Invalid access token" in response_json.get("msg", "")):
                print("Invalid or expired access token, getting a new token...")
                self.tenant_access_token = await self.get_tenant_access_token()
                if not self.tenant_access_token:
                    print("Failed to get a new tenant_access_token")
                    return None
                print("New tenant_access_token:", self.tenant_access_token)
                response = await self.create_many_records(records_fields_json)
                response_json = await response.json()
            
            if response.status == 200 and response_json.get("code") == 0:
                print("Records created successfully.")
            else:
                print(f"Error creating records: {response.status} - {response_json}")
            
            return response
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None
        
        finally:
            if self.tenant_access_token:
                with open('tenantAccessToken_storage.txt', 'w') as file:
                    file.write(self.tenant_access_token)

# Example usage
if __name__ == "__main__":
    lark_ops = LarkBaseOperations()
    records_fields_json = {
    "records": [
        {
        "fields": {
            "user_name": "Example Text 1",
            "stt": 1
        }
        },
        {
        "fields": {
            "user_name": "Example Text 2",
                "stt": 2
            }
        }
    ]
    }
    lark_ops.create_many_records_with_checkTenantAccessToken(records_fields_json)



