<img src="https://skillicons.dev/icons?i=all" alt="Skill Icons">
# Hệ thống nhận diện khuôn mặt và điểm danh

Ứng dụng nhận diện khuôn mặt bằng webcam, hỗ trợ thu thập dữ liệu khuôn mặt, train model, nhận diện realtime và ghi nhận điểm danh vào SQLite.

Project sử dụng:

- `OpenCV` để đọc webcam và xử lý khung hình.
- `face_recognition` để mã hóa và so khớp khuôn mặt.
- `mediapipe` để nhận diện cử chỉ bàn tay khi chụp dữ liệu.
- `CustomTkinter` để xây dựng giao diện.
- `SQLite` để lưu lịch sử điểm danh.

## Tính năng

- Thu thập ảnh khuôn mặt bằng webcam.
- Mỗi người cần 3 ảnh để train.
- Chụp ảnh bằng 2 cách:
  - Mở bàn tay rồi nắm tay lại.
  - Bấm phím `Space`.
- Chỉ lưu ảnh khi camera phát hiện khuôn mặt.
- Tự train model sau khi thu thập dữ liệu thành công.
- Tự kiểm tra và train lại nếu dataset mới hơn model hiện tại.
- Nhận diện khuôn mặt realtime qua webcam.
- Người chưa có trong dữ liệu sẽ hiển thị là `Unknown`.
- Tự động điểm danh người đã nhận diện, mỗi người chỉ được ghi 1 lần trong ngày.
- Xem bảng điểm danh theo ngày hoặc toàn bộ lịch sử.
- Xóa riêng dữ liệu ảnh/model hoặc dữ liệu điểm danh.

## Cấu trúc thư mục

```text
.
├── attendance.py                         # Xử lý SQLite và dữ liệu điểm danh
├── attendance.db                         # Database điểm danh
├── build_dataset.py                      # Thu thập ảnh khuôn mặt
├── recognize_face.py                     # Nhận diện khuôn mặt và điểm danh
├── train_model.py                        # Train model từ dataset
├── gui/
│   └── main_gui.py                       # Giao diện chính
├── dataset/                              # Ảnh khuôn mặt theo từng người
├── trainer/
│   └── face_model.pkl                    # Model đã train
├── models/
│   └── haarcascade_frontalface_default.xml
└── requirements.txt
```

## Yêu cầu

Khuyến nghị chạy trên Windows với Python 3.11.

Webcam cần hoạt động bình thường và không bị ứng dụng khác chiếm dụng như Zoom, Teams, Zalo, Discord hoặc trình duyệt.

## Cài đặt

Tại thư mục project, chạy:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu cài `face_recognition` hoặc `dlib` bị lỗi, hãy cài thêm:

- CMake
- Visual Studio Build Tools hoặc Visual Studio Community với workload `Desktop development with C++`

Các thư viện chính đang dùng:

```text
opencv-contrib-python==4.11.0.86
face_recognition
numpy<2
customtkinter
pillow
mediapipe==0.10.21
```

## Chạy chương trình

Chạy giao diện chính:

```powershell
python gui/main_gui.py
```

Trong giao diện có 2 tab chính:

- `Chức năng`: thu thập dữ liệu, nhận diện và xóa dữ liệu.
- `Bảng điểm danh`: xem danh sách điểm danh theo ngày hoặc tất cả ngày.

## Quy trình sử dụng

### 1. Thu thập dữ liệu

Trong tab `Chức năng`, chọn `Thu thập dữ liệu`, nhập tên người cần thêm, sau đó cửa sổ webcam sẽ mở.

Cách chụp ảnh:

1. Đưa mặt vào khung hình rõ ràng.
2. Mở bàn tay rồi nắm tay lại, hoặc bấm `Space`.
3. Chương trình chỉ lưu ảnh nếu phát hiện khuôn mặt.
4. Khi đủ 3 ảnh, cửa sổ tự đóng và GUI tự train model nếu cần.

Bấm `ESC` để hủy thu thập. Nếu quá trình bị lỗi hoặc dừng khi chưa đủ 3 ảnh, GUI sẽ tự mở lại camera với tên vừa nhập.

### 2. Nhận diện và điểm danh

Trong tab `Chức năng`, chọn `Nhận diện & Điểm danh`.

Khi bắt đầu nhận diện, chương trình sẽ:

1. Kiểm tra `dataset/` có mới hơn `trainer/face_model.pkl` không.
2. Tự train lại nếu cần.
3. Load model khuôn mặt.
4. Mở webcam để nhận diện realtime.
5. Ghi điểm danh vào `attendance.db` khi nhận diện được người hợp lệ.

Bấm `ESC` để thoát cửa sổ nhận diện.

### 3. Xem điểm danh

Mở tab `Bảng điểm danh` để xem danh sách điểm danh.

Bạn có thể:

- Chọn ngày cụ thể.
- Chọn `Tất cả ngày`.
- Bấm `Làm mới` để tải lại dữ liệu mới nhất.

### 4. Xóa dữ liệu

Trong tab `Chức năng`, chọn `Xóa dữ liệu`.

Chương trình cho phép chọn:

- `Xóa ảnh`: xóa ảnh trong `dataset/` và model trong `trainer/`.
- `Xóa dữ liệu điểm danh`: xóa toàn bộ bản ghi trong `attendance.db`.

Các thao tác xóa không thể hoàn tác.

## Chạy bằng dòng lệnh

Thu thập dữ liệu cho một người:

```powershell
python build_dataset.py "Nguyen Van A"
```

Train model thủ công:

```powershell
python train_model.py
```

Chỉ train khi dataset mới hơn model:

```powershell
python train_model.py --if-needed
```

Chạy nhận diện trực tiếp:

```powershell
python recognize_face.py
```

## Lưu ý khi sử dụng

- Camera cần đủ sáng, mặt nhìn rõ và không bị che.
- Khi dùng cử chỉ tay, đưa bàn tay vào khung hình đủ rõ để `mediapipe` nhận diện.
- Nếu nhận diện sai, hãy xóa ảnh cũ, chụp lại ảnh rõ hơn và train lại.
- Không nên public thư mục `dataset/`, `trainer/` hoặc file `attendance.db` nếu dữ liệu có thông tin cá nhân.
- Tên người được dùng làm tên thư mục trong `dataset/`, nên tránh ký tự đặc biệt khó xử lý trên Windows.

## Lỗi thường gặp

### Không mở được webcam

Đóng các ứng dụng đang dùng camera, sau đó chạy lại chương trình. Nếu máy có nhiều camera, có thể cần chỉnh lại index camera trong code.

### Không tìm thấy model

Hãy thu thập dữ liệu trước, hoặc train model thủ công:

```powershell
python train_model.py
```

### Thiếu `mediapipe`

Cài lại dependencies:

```powershell
pip install -r requirements.txt
```

Không nên tự nâng `mediapipe` nếu chưa kiểm tra code, vì project đang pin `mediapipe==0.10.21`.

### Không chụp được ảnh

- Đảm bảo camera nhìn rõ khuôn mặt.
- Bấm `Space` để thử chụp thủ công.
- Nếu dùng cử chỉ, hãy mở bàn tay rõ trước rồi mới nắm tay.

### Điểm danh không ghi thêm lần thứ hai trong ngày

Đây là hành vi mặc định. Database có ràng buộc mỗi tên chỉ có một bản ghi cho mỗi ngày.

## Tác giả

Nguyễn Bảo Trí
