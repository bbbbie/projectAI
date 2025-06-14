import cv2
import face_recognition
import os
from datetime import datetime
import numpy as np
import pandas as pd




# Tạo DataFrame để lưu trữ thông tin điểm danh
path = "pic2"
images = []
classNames = []
myList = os.listdir(path)
for cl in myList:
    curImg = cv2.imread(f"{path}/{cl}")
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

if os.path.exists("diemdanh.xlsx"):
    # Nếu file tồn tại, đọc nội dung của file vào DataFrame
    attendance_df = pd.read_excel("diemdanh.xlsx", index_col=0)
else:
    # Nếu file không tồn tại, tạo một DataFrame mới
    attendance_df = pd.DataFrame(index=classNames)

# Hỏi người dùng về ngày điểm danh
attendance_date = input("Nhập ngày điểm danh (định dạng YYYY-MM-DD): ")

def Mahoa(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

endcodeListKnow = Mahoa(images)
print("Ma Hoa thanh cong")
print(len(endcodeListKnow))

def roll_call(name):
    # Sử dụng ngày điểm danh được cung cấp bởi người dùng
    if attendance_date not in attendance_df.columns:
        # Nếu ngày này chưa có trong DataFrame, thêm cột mới với tất cả giá trị là 0
        attendance_df[attendance_date] = 0

    # Điểm danh cho học sinh
    attendance_df.loc[name, attendance_date] = 1

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    frameS = cv2.resize(frame, (0,0), None, fx=0.5, fy=0.5)
    frameS = cv2.cvtColor(frameS, cv2.COLOR_BGR2RGB)

    facecurFrame = face_recognition.face_locations(frameS)
    encodecurFrame = face_recognition.face_encodings(frameS)

    for encodeFace, faceLoc in zip(encodecurFrame, facecurFrame):
        matches = face_recognition.compare_faces(endcodeListKnow, encodeFace)
        faceDis = face_recognition.face_distance(endcodeListKnow, encodeFace)
        print(faceDis)
        matchIndex = np.argmin(faceDis)

        if faceDis[matchIndex] <0.50:
            name = classNames[matchIndex]
            roll_call(name)
        else:
            name = "Unknow"

        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, name, (x2, y2), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255), 1)

    cv2.imshow("Cua so hien thi", frame)
    key = cv2.waitKey(1)

    if key == ord("e"):
        break

cap.release()
cv2.destroyAllWindows()

# Lưu DataFrame vào file Excel
attendance_df.to_excel("diemdanh.xlsx")