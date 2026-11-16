import os
import requests
from pathlib import Path
from PIL import Image

from path_config import BACKEND_DIR

DATASET_DIR = BACKEND_DIR / "data" / "plantvillage_dataset"
HOLDOUT_TEST_DIR = BACKEND_DIR / "data" / "holdout_test_images"

COTTON_CLASSES = {
    "Bacterial Blight": "Cotton___Bacterial_blight",
    "Healthy leaf": "Cotton___healthy",
    "Powdery Mildew": "Cotton___Powdery_mildew",
    "Target spot": "Cotton___Target_spot"
}

RAW_BASE = "https://raw.githubusercontent.com/AiJared/Cotton-Plant-Disease-Detection/main/cotton-plant-disease-data"

def download_cotton_dataset(images_per_class: int = 16):
    print("=" * 60, flush=True)
    print("AgriMind AI - Direct Raw Acquisition of Cotton Leaf Dataset", flush=True)
    print("=" * 60, flush=True)
    
    session = requests.Session()
    session.headers.update({"User-Agent": "AgriMind-AI/1.0"})
    
    total_downloaded = 0
    
    for remote_folder, local_class in COTTON_CLASSES.items():
        cls_dir = DATASET_DIR / local_class
        cls_dir.mkdir(parents=True, exist_ok=True)
        
        holdout_dir = HOLDOUT_TEST_DIR / local_class
        holdout_dir.mkdir(parents=True, exist_ok=True)
        
        encoded_folder = remote_folder.replace(" ", "%20")
        print(f"\nProcessing {local_class}...", flush=True)
        
        # 1. Download training/validation images (1 to images_per_class)
        for i in range(1, images_per_class + 1):
            dest = cls_dir / f"cotton_{i}.jpg"
            if dest.exists() and dest.stat().st_size > 1000:
                total_downloaded += 1
                continue
                
            img_url = f"{RAW_BASE}/{encoded_folder}/{i}.jpg"
            try:
                resp = session.get(img_url, timeout=10)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(dest, "wb") as f:
                        f.write(resp.content)
                    with Image.open(dest) as im:
                        im.verify()
                    total_downloaded += 1
                    print(f"  [OK] Downloaded {dest.name} ({len(resp.content)} bytes)", flush=True)
                else:
                    print(f"  [SKIP] {img_url} returned status {resp.status_code}", flush=True)
            except Exception as e:
                print(f"  [ERROR] {img_url}: {e}", flush=True)
                if dest.exists():
                    dest.unlink()
                    
        # 2. Download separate holdout test images (images_per_class+1 to images_per_class+4)
        for i in range(images_per_class + 1, images_per_class + 5):
            dest = holdout_dir / f"holdout_{i}.jpg"
            if dest.exists() and dest.stat().st_size > 1000:
                continue
            img_url = f"{RAW_BASE}/{encoded_folder}/{i}.jpg"
            try:
                resp = session.get(img_url, timeout=10)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(dest, "wb") as f:
                        f.write(resp.content)
                    with Image.open(dest) as im:
                        im.verify()
                    print(f"  [HOLDOUT TEST] Saved {dest.name}", flush=True)
            except Exception:
                pass

    # 3. Download unlabelled test images from repo root
    unlabelled_dir = HOLDOUT_TEST_DIR / "unlabelled_cotton_test"
    unlabelled_dir.mkdir(parents=True, exist_ok=True)
    for name in ["test.jpg", "test_1.jpg", "test_2.jpg", "test_3.jpg", "test_4.jpg"]:
        dest = unlabelled_dir / name
        if not dest.exists():
            try:
                resp = session.get(f"{RAW_BASE}/{name}", timeout=10)
                if resp.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(resp.content)
                    print(f"  [UNLABELLED TEST] Saved {name}", flush=True)
            except Exception:
                pass

    print(f"\n[SUMMARY] Total Cotton images acquired: {total_downloaded}", flush=True)
    all_classes = sorted([d.name for d in DATASET_DIR.iterdir() if d.is_dir()])
    print(f"Total dataset classes now: {len(all_classes)}", flush=True)
    for c in all_classes:
        cnt = len(list((DATASET_DIR / c).glob("*.*")))
        print(f"  - {c}: {cnt} images", flush=True)

if __name__ == "__main__":
    download_cotton_dataset(images_per_class=16)
