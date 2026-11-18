import os
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image

from path_config import BACKEND_DIR

DATASET_DIR = BACKEND_DIR / "data" / "plantvillage_dataset"
HOLDOUT_TEST_DIR = BACKEND_DIR / "data" / "holdout_test_images"

# 4 verified Cotton classes to add
COTTON_CLASS_MAPPING = {
    "Bacterial Blight": "Cotton___Bacterial_blight",
    "Healthy leaf": "Cotton___healthy",
    "Powdery Mildew": "Cotton___Powdery_mildew",
    "Target spot": "Cotton___Target_spot"
}

GITHUB_BASE = "https://api.github.com/repos/AiJared/Cotton-Plant-Disease-Detection/contents/cotton-plant-disease-data"

def download_single_image(url: str, dest_path: Path) -> bool:
    if dest_path.exists() and dest_path.stat().st_size > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AgriSmart/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            with open(dest_path, 'wb') as f:
                f.write(content)
        with Image.open(dest_path) as im:
            im.verify()
        return True
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        return False

def acquire_cotton_dataset(images_per_class: int = 16):
    print("=" * 60, flush=True)
    print("AgriSmart - Step 1: Acquiring Verified Cotton Leaf Dataset", flush=True)
    print("=" * 60, flush=True)
    
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    HOLDOUT_TEST_DIR.mkdir(parents=True, exist_ok=True)
    
    tasks = []
    total_downloaded = 0
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        for remote_dir, local_cls in COTTON_CLASS_MAPPING.items():
            dest_cls_dir = DATASET_DIR / local_cls
            dest_cls_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch folder manifest from GitHub
            encoded_folder = urllib.parse.quote(remote_dir)
            api_url = f"{GITHUB_BASE}/{encoded_folder}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'AgriSmart/1.0'})
            
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    items = json.loads(resp.read().decode())
            except Exception as e:
                print(f"[ERROR] Failed fetching manifest for {remote_dir}: {e}", flush=True)
                continue
                
            img_items = [it for it in items if it['name'].lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"Found {len(img_items)} remote images for {remote_dir}. Downloading {min(images_per_class, len(img_items))}...", flush=True)
            
            # Save up to images_per_class for train/val
            for it in img_items[:images_per_class]:
                dest = dest_cls_dir / f"cotton_{it['name']}"
                tasks.append(executor.submit(download_single_image, it['download_url'], dest))
                
            # If there are extra images beyond images_per_class, save up to 4 in holdout test dir
            holdout_cls_dir = HOLDOUT_TEST_DIR / local_cls
            holdout_cls_dir.mkdir(parents=True, exist_ok=True)
            for it in img_items[images_per_class:images_per_class + 4]:
                dest = holdout_cls_dir / f"test_{it['name']}"
                tasks.append(executor.submit(download_single_image, it['download_url'], dest))
                
        # Also download repository root test images into holdout test directory
        try:
            req_root = urllib.request.Request(GITHUB_BASE, headers={'User-Agent': 'AgriSmart/1.0'})
            with urllib.request.urlopen(req_root, timeout=10) as resp:
                root_items = json.loads(resp.read().decode())
                test_files = [it for it in root_items if it['name'].startswith('test') and it['name'].endswith('.jpg')]
                print(f"Found {len(test_files)} unlabelled root test images for holdout verification...", flush=True)
                root_test_dir = HOLDOUT_TEST_DIR / "unlabelled_cotton_test"
                root_test_dir.mkdir(parents=True, exist_ok=True)
                for tf in test_files:
                    dest = root_test_dir / tf['name']
                    tasks.append(executor.submit(download_single_image, tf['download_url'], dest))
        except Exception as e:
            print(f"[WARNING] Could not fetch root test images: {e}", flush=True)

        for future in as_completed(tasks):
            if future.result():
                total_downloaded += 1

    print(f"\n[OK] Cotton dataset acquisition completed. {total_downloaded} files verified.", flush=True)
    
    # Audit all classes now in DATASET_DIR
    all_classes = sorted([d.name for d in DATASET_DIR.iterdir() if d.is_dir()])
    print(f"\nTotal classes now in {DATASET_DIR.name}: {len(all_classes)}", flush=True)
    for c in all_classes:
        cnt = len(list((DATASET_DIR / c).glob("*.*")))
        print(f"  - {c}: {cnt} images", flush=True)

if __name__ == '__main__':
    acquire_cotton_dataset(images_per_class=16)
