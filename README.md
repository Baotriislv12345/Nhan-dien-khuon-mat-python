# Nhận diện khuôn mặt nhóm 4

Ứng dụng nhận diện khuôn mặt bằng webcam, dùng `face_recognition` để tạo encoding khuôn mặt, `OpenCV` để đọc camera và `CustomTkinter` để chạy giao diện.

## Tính năng

- Thu thập dữ liệu khuôn mặt bằng webcam.
- Mỗi người cần 3 ảnh để train.
- Có 2 cách chụp ảnh khi thu thập dữ liệu:
  - Mở bàn tay rồi nắm tay lại.
  - Bấm phím `Space`.
- Nếu thu thập thất bại khi chưa đủ 3 ảnh, GUI tự mở lại camera với tên cũ, không cần nhập lại tên.
- Sau khi thu thập xong, chương trình tự train model nếu dữ liệu mới hơn model hiện tại.
- Khi nhận diện, chương trình cũng tự kiểm tra và train lại nếu dataset đã thay đổi.
- Hiển thị tên người nhận diện được, người lạ sẽ hiển thị `Unknown`.

## Cấu trúc chính

```text
FaceRecognitionProject/
├── build_dataset.py        # Thu thập ảnh khuôn mặt
├── train_model.py          # Train model từ dataset
├── recognize_face.py       # Nhận diện khuôn mặt realtime
├── gui/
│   └── main_gui.py         # Giao diện chính
├── dataset/                # Ảnh khuôn mặt theo từng người
├── trainer/
│   └── face_model.pkl      # Model đã train
├── models/
│   └── haarcascade_frontalface_default.xml
└── requirements.txt
```

## Cài đặt

Khuyến nghị dùng Python 3.11 trên Windows.

Tại thư mục dự án, chạy:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu cài `face_recognition` hoặc `dlib` lỗi, cần cài thêm:

- CMake
- Visual Studio Build Tools hoặc Visual Studio Community với workload `Desktop development with C++`

## Chạy chương trình

Chạy GUI:

```powershell
python gui/main_gui.py
```

Trong giao diện có các nút chính:

- `Thu thập dữ liệu`: nhập tên người, mở webcam để chụp 3 ảnh.
- `Nhận diện khuôn mặt`: mở webcam để nhận diện realtime.
- `Xóa dữ liệu`: xóa toàn bộ thư mục `dataset/`.

## Thu thập dữ liệu

Sau khi nhập tên, cửa sổ webcam sẽ mở ra.

Cách chụp ảnh:

1. Đưa mặt vào camera.
2. Dùng một trong hai cách:
   - Mở bàn tay rồi nắm tay lại.
   - Bấm `Space`.
3. Chương trình chỉ lưu ảnh nếu phát hiện khuôn mặt.
4. Khi đủ 3 ảnh, cửa sổ tự đóng và GUI tự train model.

Bấm `ESC` để hủy thu thập. Nếu bấm `ESC`, GUI không tự chạy lại.

Nếu quá trình thu thập bị lỗi hoặc dừng khi chưa đủ 3 ảnh, GUI sẽ tự mở lại cửa sổ thu thập với đúng tên vừa nhập.

## Nhận diện khuôn mặt

Chạy từ GUI bằng nút `Nhận diện khuôn mặt`, hoặc chạy trực tiếp:

```powershell
python recognize_face.py
```

Khi mở nhận diện, chương trình sẽ:

1. Kiểm tra `dataset/` có thay đổi không.
2. Tự train lại nếu cần.
3. Load `trainer/face_model.pkl`.
4. Mở webcam và nhận diện khuôn mặt realtime.

Bấm `ESC` để thoát cửa sổ nhận diện.

## Train thủ công

Bình thường không cần train thủ công nữa. Nếu vẫn muốn train lại toàn bộ:

```powershell
python train_model.py
```

Nếu chỉ muốn train khi dataset mới hơn model:

```powershell
python train_model.py --if-needed
```

## Lưu ý khi sử dụng

- Camera cần đủ sáng, mặt nhìn rõ và không bị che.
- Khi dùng cử chỉ tay, đưa tay vào khung hình đủ rõ để `mediapipe` nhận diện.
- Nếu camera không mở được, kiểm tra Zoom, Teams, Zalo, Discord hoặc app khác có đang chiếm webcam không.
- Nếu nhận diện sai người, hãy chụp lại ảnh rõ hơn và train lại.
- Không nên public thư mục `dataset/` và `trainer/` nếu dữ liệu có thông tin cá nhân.

## Lỗi thường gặp

### Không tìm thấy model

Chạy thu thập dữ liệu trước, hoặc chạy:

```powershell
python train_model.py
```

### Thiếu mediapipe

Chạy:

```powershell
pip install -r requirements.txt
```

Project đang pin:

```text
mediapipe==0.10.21
numpy<2
opencv-contrib-python==4.11.0.86
```

Không nên tự nâng `mediapipe` lên bản mới nếu chưa sửa code, vì một số bản mới không còn `mp.solutions.hands`.

### Không chụp được ảnh

- Đảm bảo camera thấy rõ khuôn mặt.
- Bấm `Space` để thử cách chụp thủ công.
- Nếu dùng cử chỉ, hãy mở bàn tay rõ trước rồi mới nắm tay.

## Tác giả

Nguyễn Bảo Trí
