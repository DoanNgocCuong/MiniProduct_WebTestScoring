import gradio as gr
import gdown
import shutil
import os
import requests
import random
import openpyxl

def sync_data(button):
    drive_file_url = "https://docs.google.com/spreadsheets/d/1WEyCrPIZECFuFANfwgCNZiiRdEJcoHMV/export?format=xlsx"
    server_file_path = r"D:\OneDrive - Hanoi University of Science and Technology\ITE10-DS&AI-HUST\Learn&Task\PRODUCT_THECOACH\TASK5_GPTschatbot_TestingSale\deploy\QuizApp_deploy1\Data_MarketingKit.xlsx"

    try:
        # Simulate a server restart (1 in 10 chance)
        if random.random() < 0.1:
            raise Exception("Server đang khởi động lại. Vui lòng thử lại sau vài phút.")

        # Check internet connection
        requests.get("https://www.google.com", timeout=5)
        
        # Download file from Google Drive
        temp_file = "temp_file.xlsx"
        gdown.download(drive_file_url, temp_file, quiet=False)
        
        if not os.path.exists(temp_file):
            raise FileNotFoundError("Không thể tải file từ Google Drive")
        
        # Check write permissions
        if not os.access(os.path.dirname(server_file_path), os.W_OK):
            raise PermissionError(f"Không có quyền ghi vào thư mục {os.path.dirname(server_file_path)}")
        
        # Sync with server file
        try:
            workbook = openpyxl.load_workbook(temp_file)
            workbook.close()
        except Exception as e:
            return f"File tải xuống không hợp lệ: {str(e)}"
        
        shutil.copy(temp_file, server_file_path)
        
        # Remove temp file
        os.remove(temp_file)
        
        return f"Đã đồng bộ dữ liệu từ Google Drive với file trên server ({server_file_path})"
    except requests.ConnectionError:
        return "Lỗi: Không thể kết nối internet. Vui lòng kiểm tra kết nối mạng."
    except Exception as e:
        if "gdown" in str(e).lower():
            return f"Lỗi khi tải file từ Google Drive: {str(e)}"
        return f"Lỗi: {str(e)}"

# Tạo một giao diện Gradio sử dụng Blocks với chủ đề Soft
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("<h1 style='text-align: center;'>Ứng dụng Đồng bộ Dữ liệu</h1>")

    gr.Button("Ấn vào đây => Chỉnh sửa trực tiếp `link google sheet`", link="https://docs.google.com/spreadsheets/d/1WEyCrPIZECFuFANfwgCNZiiRdEJcoHMV/edit")
    # Thêm ghi chú nhắc nhở người dùng
    gr.Markdown("**Lưu ý:** Sau khi chỉnh sửa xong trên Google Sheet. Hãy ấn nút bên dưới để đồng bộ dữ liệu lên server.")

    # Tạo một hàng chứa các nút điều khiển
    with gr.Row():
        sync_button = gr.Button("Bắt đầu Đồng bộ", variant="primary") # Tạo nút "Bắt đầu Đồng bộ" với kiểu primary

    # Tạo một hộp văn bản để hiển thị trạng thái, có 5 dòng
    output = gr.Textbox(label="Trạng thái", lines=5)

    # Khi nút đồng bộ được nhấn, gọi hàm sync_data và hiển thị kết quả trong output
    sync_button.click(sync_data, outputs=output)

# Khởi chạy ứng dụng Gradio
demo.launch(share=True, server_name="0.0.0.0", server_port=25018)
