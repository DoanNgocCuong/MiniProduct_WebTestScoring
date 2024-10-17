from dotenv import load_dotenv
import os

# Load biến môi trường từ file .env
load_dotenv()

app_id = os.getenv("APP_DOANNGOCCUONG_ID")
app_secret = os.getenv("APP_DOANNGOCCUONG_SECRET")

print(app_id)
print(app_secret)