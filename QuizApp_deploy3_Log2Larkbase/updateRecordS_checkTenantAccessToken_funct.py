import requests
import json
import os
import sys

# Add the parent directory to sys.path to import config.py
file_path = os.path.abspath(__file__)  # Absolute path to the current file
current_dir = os.path.dirname(file_path)  # Path to the current directory
parent_dir = os.path.dirname(current_dir)  # Path to the parent directory
sys.path.append(parent_dir)  # Add the parent directory to sys.path
import config  # Now we can import config from the parent directory 

# Import modules from backend_package
from get_tenantAccessToken_funct import get_tenant_access_token
from createRecordS_tenantAccessToken_funct import create_many_records

app_base_token = config.APP_BASE_TOKEN  # Your app_token
base_table_id = config.BASE_TABLE_ID  # Your table_id

records_fields_json = {
    "records": [
        {
            "fields": {
                "Multi-select column": [
                    "Option1",
                    "Option2"
                ],
                "conversation_id": "Example Text"
            }
        }
    ]
}


# records_fields_json = {'records': [{'fields': {'user_name': 'C', 'stt': 1, 'question_type': 'essay', 'question': '3. Học viên sau khóa học A1 có thể đạt được đầu ra là gì?', 'user_answer': 'a', 'point': 0.0, 'assistant_response': 'Có lỗi xảy ra khi chấm điểm: Connection error.. Vui lòng thử lại.', 'topic': 'Khoá học TOCO', 'time_start': '2024-10-17 15:23:42', 'time_end': '2024-10-17 15:24:00', 'total_score': 0.0, 'user_feedback': 'fsdfdsf'}}, {'fields': {'user_name': 'C', 'stt': 2, 'question_type': 'essay', 'question': '2. Khóa học A1 yêu cầu đầu vào của học viên như thế nào?', 'user_answer': 'b', 'point': 0.0, 'assistant_response': 'Có lỗi xảy ra khin như thế nào?', 'user_answer': 'b', 'point': 0.0, 'assistant_response': 'Có lỗi xảy ra khi chấm điểm: Connection error.. Vui lòng thử lại.', 'topic': 'Khoá học TOCO', 'time_start': '2024-10-17 15:23:42', 'time_end': '2024-10-17 15:24:00', 'total_score': 0.0, 'user_feedbac'2024-10-17 15:23:42', 'time_end': '2024-10-17 15:24:00', 'total_score': 0.0, 'user_feedback': 'fsdfdsf'}}]}

def create_many_records_with_checkTenantAccessToken(app_base_token, base_table_id, records_fields_json):
    # Lấy tenant_access_token từ bộ nhớ hoặc tạo mới
    try:
        with open('tenantAccessToken_storage.txt', 'r') as file:
            tenant_access_token = file.read().strip()
            if not tenant_access_token:
                raise FileNotFoundError
            print("Tenant token từ bộ nhớ:", tenant_access_token)
    except FileNotFoundError:
        tenant_access_token = get_tenant_access_token()
        print("Đã tạo tenant_access_token mới:", tenant_access_token)

    # Thử tạo bản ghi
    try:
        response = create_many_records(app_base_token, base_table_id, tenant_access_token, records_fields_json)
        
        # Kiểm tra nếu phản hồi cho thấy token không hợp lệ
        if response.status_code in [400, 401] or (response.json().get("code") in [99991661, 99991663] or "Invalid access token" in response.json().get("msg", "")):
            print("Token truy cập không hợp lệ hoặc đã hết hạn, đang lấy token mới...")
            tenant_access_token = get_tenant_access_token()
            print("tenant_access_token mới:", tenant_access_token)
            response = create_many_records(app_base_token, base_table_id, tenant_access_token, records_fields_json)
        
        # Kiểm tra lại phản hồi sau khi sử dụng token mới
        if response.status_code == 200 and response.json().get("code") == 0:
            print("Đã tạo bản ghi thành công.")
        else:
            print(f"Lỗi khi tạo bản ghi: {response.status_code} - {response.json()}")
    
    except requests.exceptions.RequestException as e:
        print(f"Đã xảy ra lỗi: {e}")
        raise
    
    # Lưu tenant_access_token (có thể là mới) vào bộ nhớ
    with open('tenantAccessToken_storage.txt', 'w') as file:
        file.write(tenant_access_token)

    print("tenant_access_token cuối cùng:", tenant_access_token)
    return response

create_many_records_with_checkTenantAccessToken(app_base_token, base_table_id, records_fields_json)
