import cv2
import face_recognition
import os
from datetime import datetime
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from PIL import Image, ImageTk

# Đường dẫn đến thư mục chứa ảnh khuôn mặt
path = "pic2"
images = []
classNames = []
myList = os.listdir(path)
for cl in myList:
    curImg = cv2.imread(f"{path}/{cl}")
    if curImg is not None:
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])

# Tạo hoặc đọc DataFrame điểm danh
if os.path.exists("diemdanh.xlsx"):
    attendance_df = pd.read_excel("diemdanh.xlsx", index_col=0)
else:
    attendance_df = pd.DataFrame(index=classNames)

# Hàm mã hóa khuôn mặt
def encode_faces(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        except IndexError:
            print(f"Không tìm thấy khuôn mặt trong ảnh {img}")
    return encodeList

encodeListKnown = encode_faces(images)
print("Mã hóa thành công")
print(f"Số lượng khuôn mặt được mã hóa: {len(encodeListKnown)}")

# Biến toàn cục
attendance_date = None
running = False
cap = None
panel = None
panel_img = None  # Biến để lưu ảnh tkinter

# Hàm điểm danh và lưu ngay lập tức
def mark_attendance(name):
    global attendance_df
    if attendance_date not in attendance_df.columns:
        attendance_df[attendance_date] = 0
    attendance_df.loc[name, attendance_date] = 1
    attendance_df.to_excel("diemdanh.xlsx", index=True)
    print(f"Đã điểm danh: {name} vào ngày {attendance_date}")

# Hàm xử lý camera trong thread
def start_camera():
    global running, cap, panel, panel_img
    cap = cv2.VideoCapture(0)
    while running:
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc khung hình từ camera!")
            break
        frameS = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        frameS = cv2.cvtColor(frameS, cv2.COLOR_BGR2RGB)

        faceLocs = face_recognition.face_locations(frameS)
        encodeFaces = face_recognition.face_encodings(frameS)

        for encodeFace, faceLoc in zip(encodeFaces, faceLocs):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex] and faceDis[matchIndex] < 0.6:
                name = classNames[matchIndex].upper()
                mark_attendance(name)
            else:
                name = "UNKNOWN"

            y1, x2, y2, x1 = [i * 4 for i in faceLoc]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1, y2 - 10), cv2.FONT_HERSHEY_COMPLEX, 0.75, (255, 255, 255), 2)

        # Chuyển frame sang định dạng tkinter bằng PIL
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Quay lại BGR cho OpenCV
        img = cv2.resize(frame, (640, 480))
        img = Image.fromarray(img)
        img = ImageTk.PhotoImage(image=img)

        # Cập nhật giao diện an toàn
        if panel is not None and running:
            panel.config(image=img)
            panel.image = img  # Giữ tham chiếu để tránh bị xóa bởi garbage collector

# Hàm bắt đầu camera
def start_recognition():
    global attendance_date, running, panel
    if not attendance_date:
        messagebox.showerror("Lỗi", "Vui lòng chọn ngày điểm danh!")
        return
    if not running:
        running = True
        thread = threading.Thread(target=start_camera, daemon=True)
        thread.start()
        btn_start.config(state="disabled")
        btn_stop.config(state="normal")

# Hàm dừng camera
def stop_recognition():
    global running, cap
    running = False  # Dừng vòng lặp camera
    if cap is not None and cap.isOpened():  # Kiểm tra xem camera có đang mở không
        cap.release()  # Giải phóng camera
        cap = None  # Xóa tham chiếu
    btn_start.config(state="normal")  # Kích hoạt lại nút "Bắt đầu"
    btn_stop.config(state="disabled")  # Vô hiệu hóa nút "Dừng"
    # Xóa khung hình camera trên giao diện
    if panel is not None:
        panel.config(image='')  # Xóa ảnh hiển thị
        panel.image = None  # Xóa tham chiếu ảnh

# Tạo giao diện tkinter
root = tk.Tk()
root.title("Ứng dụng Điểm Danh Khuôn Mặt")

# Nhập ngày điểm danh
tk.Label(root, text="Nhập ngày điểm danh (YYYY-MM-DD):").pack(pady=5)
date_entry = tk.Entry(root)
date_entry.pack(pady=5)

def set_date():
    global attendance_date
    date = date_entry.get()
    try:
        datetime.strptime(date, "%Y-%m-%d")
        attendance_date = date
        messagebox.showinfo("Thành công", f"Đã đặt ngày: {date}")
    except ValueError:
        messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ! Vui lòng nhập YYYY-MM-DD.")

tk.Button(root, text="Xác nhận ngày", command=set_date).pack(pady=5)

# Nút chọn tuần
tk.Label(root, text="Chọn tuần:").pack(pady=5)
weeks = ["Tuần 1", "Tuần 2", "Tuần 3"]
week_var = tk.StringVar(value=weeks[0])
for week in weeks:
    tk.Radiobutton(root, text=week, variable=week_var, value=week).pack()

# Nút bắt đầu và dừng
btn_start = tk.Button(root, text="Bắt đầu", command=start_recognition, state="normal")
btn_start.pack(pady=5)
btn_stop = tk.Button(root, text="Dừng", command=stop_recognition, state="disabled")
btn_stop.pack(pady=5)

# Hiển thị khung hình camera
panel = tk.Label(root)
panel.pack(pady=10)

# Chạy giao diện
root.mainloop()

# Đảm bảo giải phóng tài nguyên khi thoát
if cap is not None and cap.isOpened():
    cap.release()
cv2.destroyAllWindows()