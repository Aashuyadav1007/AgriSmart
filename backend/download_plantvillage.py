import os
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image

from path_config import BACKEND_DIR

TARGET_CLASSES = [
    "Tomato___healthy",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Bacterial_spot",
    "Potato___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Corn_(maize)___Common_rust_"
]

DATASET_DIR = BACKEND_DIR / "data" / "plantvillage_dataset"

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

def download_plantvillage_sample(images_per_class: int = 12):
    print("=" * 60, flush=True)
    print("Downloading PlantVillage Verified Dataset (Concurrent)", flush=True)
    print("=" * 60, flush=True)
    
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    
    tasks = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for cls in TARGET_CLASSES:
            cls_dir = DATASET_DIR / cls
            cls_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch manifest
            api_url = f"https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color/{cls}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'AgriSmart/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    items = json.loads(resp.read().decode())
            except Exception as e:
                print(f"[ERROR] Failed fetching manifest for {cls}: {e}", flush=True)
                continue
            
            image_items = [it for it in items if it['name'].lower().endswith(('.jpg', '.jpeg', '.png'))][:images_per_class]
            print(f"Queueing {len(image_items)} images for {cls}...", flush=True)
            
            for item in image_items:
                dest = cls_dir / item['name']
                tasks.append(executor.submit(download_single_image, item['download_url'], dest))
        
        # Wait for all
        completed = 0
        for future in as_completed(tasks):
            if future.result():
                completed += 1
                if completed % 10 == 0 or completed == len(tasks):
                    print(f"Downloaded {completed}/{len(tasks)} images...", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print(f"PlantVillage download finished: {completed} images verified in {DATASET_DIR}", flush=True)
    print("=" * 60, flush=True)

if __name__ == '__main__':
    download_plantvillage_sample(images_per_class=12)
