import argparse
import pickle
import sys
from pathlib import Path

import cv2
import face_recognition

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset"
MODEL_PATH = BASE_DIR / "trainer" / "face_model.pkl"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CASCADE_PATH = BASE_DIR / "models" / "haarcascade_frontalface_default.xml"


def iter_image_paths(dataset_path=DATASET_PATH):
    if not dataset_path.exists():
        return

    for person_path in dataset_path.iterdir():
        if not person_path.is_dir():
            continue

        for image_path in person_path.iterdir():
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                yield person_path.name, image_path


def get_latest_dataset_mtime(dataset_path=DATASET_PATH):
    latest_mtime = None

    for _, image_path in iter_image_paths(dataset_path):
        image_mtime = image_path.stat().st_mtime
        if latest_mtime is None or image_mtime > latest_mtime:
            latest_mtime = image_mtime

    return latest_mtime


def should_train_model(dataset_path=DATASET_PATH, model_path=MODEL_PATH):
    latest_dataset_mtime = get_latest_dataset_mtime(dataset_path)

    if latest_dataset_mtime is None:
        return False

    if not model_path.exists():
        return True

    return latest_dataset_mtime > model_path.stat().st_mtime


def get_face_locations(image):
    locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
    if locations:
        return locations

    cascade_path = CASCADE_PATH
    if not cascade_path.exists() or cascade_path.stat().st_size == 0:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"

    face_detector = cv2.CascadeClassifier(str(cascade_path))
    if face_detector.empty():
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4)

    locations = []
    height, width = image.shape[:2]
    for x, y, w, h in faces:
        padding = int(max(w, h) * 0.15)
        top = max(0, y - padding)
        right = min(width, x + w + padding)
        bottom = min(height, y + h + padding)
        left = max(0, x - padding)
        locations.append((top, right, bottom, left))

    return locations


def train_model(dataset_path=DATASET_PATH, model_path=MODEL_PATH):
    known_encodings = []
    known_names = []
    total_images = 0

    if not dataset_path.exists():
        raise FileNotFoundError(f"Khong tim thay thu muc dataset: {dataset_path}")

    for person_name, image_path in iter_image_paths(dataset_path):
        image = face_recognition.load_image_file(str(image_path))
        total_images += 1

        locations = get_face_locations(image)
        encodings = face_recognition.face_encodings(image, known_face_locations=locations)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(person_name)
        else:
            print(f"Khong tim thay khuon mat trong anh: {image_path}")

    data = {
        "encodings": known_encodings,
        "names": known_names,
    }

    print(f"So anh trong dataset: {total_images}")
    print(f"So anh co khuon mat duoc dung de train: {len(known_encodings)}")

    if not known_encodings:
        print("Canh bao: Khong tim thay khuon mat nao trong dataset.")
        print("Hay kiem tra lai thu muc dataset va dam bao anh chua khuon mat ro rang.")

    model_path.parent.mkdir(parents=True, exist_ok=True)

    with model_path.open("wb") as file:
        pickle.dump(data, file)

    print("Train model thanh cong")
    return data


def auto_train_if_needed(dataset_path=DATASET_PATH, model_path=MODEL_PATH):
    if should_train_model(dataset_path, model_path):
        print("Dataset co thay doi. Dang tu dong train model...")
        return train_model(dataset_path, model_path)

    print("Model dang moi nhat, bo qua train.")
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--if-needed",
        action="store_true",
        help="Chi train khi dataset moi hon model hoac model chua ton tai.",
    )
    args = parser.parse_args()

    if args.if_needed:
        auto_train_if_needed()
    else:
        train_model()


if __name__ == "__main__":
    main()
