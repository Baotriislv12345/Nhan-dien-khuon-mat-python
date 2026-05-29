import os
import sys
import time
from pathlib import Path

import cv2

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

try:
    import mediapipe as mp
except ImportError as exc:
    raise ImportError(
        "Thieu thu vien mediapipe. Hay chay: pip install -r requirements.txt"
    ) from exc

TARGET_IMAGES = 3
CAPTURE_COOLDOWN_SECONDS = 1.0
EXIT_SUCCESS = 0
EXIT_FAILED = 2
EXIT_CANCELLED = 130


def is_finger_extended(landmarks, tip_id, pip_id):
    return landmarks[tip_id].y < landmarks[pip_id].y


def count_extended_fingers(hand_landmarks, handedness):
    landmarks = hand_landmarks.landmark
    fingers = 0

    is_right_hand = handedness.classification[0].label == "Right"
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]

    if is_right_hand:
        thumb_extended = thumb_tip.x < thumb_ip.x
    else:
        thumb_extended = thumb_tip.x > thumb_ip.x

    if thumb_extended:
        fingers += 1

    finger_joints = (
        (8, 6),
        (12, 10),
        (16, 14),
        (20, 18),
    )

    for tip_id, pip_id in finger_joints:
        if is_finger_extended(landmarks, tip_id, pip_id):
            fingers += 1

    return fingers


def get_hand_gesture(results):
    if not results.multi_hand_landmarks or not results.multi_handedness:
        return "NO_HAND"

    fingers = count_extended_fingers(
        results.multi_hand_landmarks[0],
        results.multi_handedness[0],
    )

    if fingers >= 4:
        return "OPEN"

    if fingers <= 1:
        return "FIST"

    return "OTHER"


def save_capture(save_path, count, frame):
    file_name = save_path / f"{count}.jpg"
    success, encoded_image = cv2.imencode(".jpg", frame)

    if not success:
        print("Khong the ma hoa anh de luu. Hay thu lai.")
        return False

    try:
        file_name.write_bytes(encoded_image.tobytes())
        print(f"Da chup: {count + 1}")
        return True
    except Exception as save_error:
        print(f"Luu anh that bai: {save_error}")
        return False


def try_capture(save_path, count, frame, faces, source):
    if len(faces) == 0:
        print(f"Khong phat hien khuon mat, khong chup bang {source}.")
        return False

    return save_capture(save_path, count, frame)


if len(sys.argv) > 1:
    name = sys.argv[1].strip()
else:
    name = input("Nhap ten nguoi: ").strip()

if not name:
    raise ValueError("Ten nguoi khong duoc de trong")

save_path = BASE_DIR / "dataset" / name
save_path.mkdir(parents=True, exist_ok=True)

cascade_path = BASE_DIR / "models" / "haarcascade_frontalface_default.xml"
if not cascade_path.exists() or cascade_path.stat().st_size == 0:
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    print(f"Warning: local cascade missing or empty, dung cascade tich hop: {cascade_path}")

face_detector = cv2.CascadeClassifier(str(cascade_path))
if face_detector.empty():
    raise FileNotFoundError(
        f"Khong the tai Haar cascade. Kiem tra file: {cascade_path}"
    )

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError(
        "Khong mo duoc webcam. Hay kiem tra camera hoac thu thay so 0 bang 1 neu co nhieu thiet bi."
    )

count = 0
ready_to_capture = False
last_capture_time = 0
exit_code = EXIT_FAILED

with mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
) as hands:
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        clean_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
        )

        hand_results = hands.process(rgb)
        gesture = get_hand_gesture(hand_results)

        if gesture == "OPEN":
            ready_to_capture = True

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            exit_code = EXIT_CANCELLED
            break

        now = time.monotonic()
        gesture_capture = (
            ready_to_capture
            and gesture == "FIST"
            and now - last_capture_time >= CAPTURE_COOLDOWN_SECONDS
        )
        space_capture = key == 32 and now - last_capture_time >= CAPTURE_COOLDOWN_SECONDS

        if gesture_capture or space_capture:
            source = "cu chi" if gesture_capture else "phim Space"

            if try_capture(save_path, count, clean_frame, faces, source):
                count += 1
                last_capture_time = now
                ready_to_capture = False

            if count >= TARGET_IMAGES:
                exit_code = EXIT_SUCCESS
                break

        cv2.putText(
            frame,
            f"Captured: {count}/{TARGET_IMAGES}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            "Open hand then fist, or press SPACE",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            f"Gesture: {gesture}",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            "Press ESC to exit",
            (10, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2,
        )

        if gesture == "FIST" and len(faces) == 0:
            cv2.putText(
                frame,
                "Face required",
                (10, 160),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        for (x, y, w, h) in faces:
            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2,
            )

        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                )

        cv2.imshow("Build Dataset", frame)

cap.release()
cv2.destroyAllWindows()

if exit_code == EXIT_SUCCESS:
    print("Thu thap du lieu hoan tat")
elif exit_code == EXIT_CANCELLED:
    print("Da huy thu thap du lieu")
else:
    print(f"Thu thap that bai: moi chup duoc {count}/{TARGET_IMAGES} anh")

sys.exit(exit_code)
