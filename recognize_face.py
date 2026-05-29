import pickle
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from attendance import mark_attendance
from train_model import auto_train_if_needed


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "trainer" / "face_model.pkl"

TARGET_FPS = 60
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
RECOGNITION_FPS = 12
PROCESS_SCALE = 0.5
MATCH_THRESHOLD = 0.5

FONT_PATHS = [
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/tahoma.ttf"),
    Path("C:/Windows/Fonts/verdana.ttf"),
    Path("C:/Windows/Fonts/arialuni.ttf"),
]


def get_unicode_font(font_size):
    for font_path in FONT_PATHS:
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), font_size)
            except OSError:
                continue
    return ImageFont.load_default()


LABEL_FONT = get_unicode_font(20)
STATUS_FONT = get_unicode_font(18)
SMALL_FONT = get_unicode_font(15)


def rgb_color(bgr_color):
    blue, green, red = bgr_color
    return red, green, blue


def configure_camera(cap):
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)


def open_camera():
    camera_options = (
        (0, cv2.CAP_DSHOW),
        (0, cv2.CAP_MSMF),
        (0, cv2.CAP_ANY),
        (1, cv2.CAP_DSHOW),
        (1, cv2.CAP_ANY),
    )

    for index, backend in camera_options:
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue

        configure_camera(cap)
        ret, frame = cap.read()
        if ret and frame is not None:
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"Opened camera {index}, requested {TARGET_FPS} FPS, reported {actual_fps:.1f} FPS")
            return cap, frame

        cap.release()

    return None, None


def load_model():
    auto_train_if_needed()

    if not MODEL_PATH.exists():
        print("Error: face model not found. Run train_model.py first.")
        sys.exit(1)

    with MODEL_PATH.open("rb") as file:
        data = pickle.load(file)

    known_encodings = data.get("encodings", [])
    known_names = data.get("names", [])

    if not known_encodings:
        print("Error: trained face data is empty. Collect images, then train again.")
        sys.exit(1)

    return known_encodings, known_names


def recognize_frame(frame, known_encodings, known_names):
    small_frame = cv2.resize(frame, (0, 0), fx=PROCESS_SCALE, fy=PROCESS_SCALE)
    rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations)
    faces = []

    for face_encoding, face_location in zip(encodings, locations):
        name = "Unknown"
        distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(distances) > 0:
            best_match_index = int(np.argmin(distances))
            if distances[best_match_index] <= MATCH_THRESHOLD:
                name = known_names[best_match_index]

        top, right, bottom, left = face_location
        scale = 1 / PROCESS_SCALE
        faces.append(
            {
                "name": name,
                "location": (
                    int(top * scale),
                    int(right * scale),
                    int(bottom * scale),
                    int(left * scale),
                ),
            }
        )

    return faces


def update_attendance(faces, attendance_status):
    for face in faces:
        name = face["name"]
        if name == "Unknown" or name in attendance_status:
            continue

        marked, message = mark_attendance(name)
        if marked:
            attendance_status[name] = f"Đã điểm danh lúc {message}"
        else:
            attendance_status[name] = message


def draw_unicode_texts(frame, text_items):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)
    draw = ImageDraw.Draw(pil_img)

    for text, position, color, font in text_items:
        draw.text(position, str(text), font=font, fill=rgb_color(color))

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def draw_overlay(frame, faces, attendance_status, fps):
    text_items = []

    for face in faces:
        name = face["name"]
        top, right, bottom, left = face["location"]
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        label = name
        if name != "Unknown":
            label = f"{name} - {attendance_status.get(name, 'Đang điểm danh...')}"
        text_items.append((label, (left, max(4, top - 26)), color, LABEL_FONT))

    panel_height = 92 + 26 * max(0, len(attendance_status) - 1)
    cv2.rectangle(frame, (0, 0), (450, panel_height), (20, 20, 20), -1)

    text_items.append(
        (
            f"FPS hiển thị: {fps:.1f} / mục tiêu {TARGET_FPS}",
            (12, 10),
            (255, 255, 255),
            STATUS_FONT,
        )
    )

    if not faces:
        text_items.append(("Chưa phát hiện khuôn mặt", (12, 38), (0, 220, 255), STATUS_FONT))
    elif all(face["name"] == "Unknown" for face in faces):
        text_items.append(("Người lạ - không điểm danh", (12, 38), (0, 120, 255), STATUS_FONT))
    else:
        y = 38
        for name, status in sorted(attendance_status.items()):
            text_items.append((f"{name}: {status}", (12, y), (120, 255, 120), SMALL_FONT))
            y += 26

    text_items.append(("ESC: thoát", (12, panel_height - 24), (220, 220, 220), SMALL_FONT))
    return draw_unicode_texts(frame, text_items)


def main():
    known_encodings, known_names = load_model()
    cap, frame = open_camera()

    if cap is None:
        print("Error: cannot open webcam.")
        print("Close other apps using the camera and allow Camera access for Desktop apps in Windows Settings.")
        sys.exit(2)

    attendance_status = {}
    faces = []
    pending_recognition = None
    last_submit_at = 0.0
    recognition_interval = 1 / RECOGNITION_FPS

    fps = 0.0
    fps_frames = 0
    fps_started_at = time.perf_counter()

    with ThreadPoolExecutor(max_workers=1) as executor:
        while True:
            if pending_recognition is not None and pending_recognition.done():
                faces = pending_recognition.result()
                update_attendance(faces, attendance_status)
                pending_recognition = None

            now = time.perf_counter()
            if pending_recognition is None and now - last_submit_at >= recognition_interval:
                pending_recognition = executor.submit(
                    recognize_frame,
                    frame.copy(),
                    known_encodings,
                    known_names,
                )
                last_submit_at = now

            output = draw_overlay(frame.copy(), faces, attendance_status, fps)
            cv2.imshow("Face Recognition - Điểm danh 60 FPS", output)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break

            ret, frame = cap.read()
            if not ret:
                print("Error: lost webcam frame.")
                break

            fps_frames += 1
            elapsed = time.perf_counter() - fps_started_at
            if elapsed >= 1.0:
                fps = fps_frames / elapsed
                fps_frames = 0
                fps_started_at = time.perf_counter()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
