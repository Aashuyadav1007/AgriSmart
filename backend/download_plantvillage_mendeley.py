import os
import sys
import time
import zipfile
import hashlib
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend")
DOWNLOADS_DIR = BACKEND_DIR / "data" / "downloads"
EXTRACT_DIR = BACKEND_DIR / "data" / "plantvillage_mendeley_extracted"
ZIP_PATH = DOWNLOADS_DIR / "Plant_leaf_diseases_dataset_without_augmentation.zip"

URL = "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded"
EXPECTED_SIZE = 868032562

def download_and_verify():
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Download if not already present or incomplete
    if ZIP_PATH.exists() and ZIP_PATH.stat().st_size == EXPECTED_SIZE:
        print(f"[OK] Archive already exists and matches expected size ({EXPECTED_SIZE:,} bytes): {ZIP_PATH}")
    else:
        print(f"Downloading PlantVillage Mendeley archive from:\n  {URL}")
        print(f"Destination: {ZIP_PATH}")
        print(f"Expected Size: {EXPECTED_SIZE / (1024*1024):.2f} MB")
        
        req = urllib.request.Request(URL, headers={"User-Agent": "AgriMind-AI-Verification/1.0"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as resp, open(ZIP_PATH, "wb") as out_file:
            downloaded = 0
            chunk_size = 1024 * 1024 # 1 MB chunks
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                pct = (downloaded / EXPECTED_SIZE) * 100
                elapsed = time.time() - t0
                speed_mb = (downloaded / (1024*1024)) / max(elapsed, 0.001)
                print(f"\rDownloaded: {downloaded / (1024*1024):.2f} / {EXPECTED_SIZE / (1024*1024):.2f} MB ({pct:.1f}%) - Speed: {speed_mb:.2f} MB/s", end="", flush=True)
        print(f"\n[OK] Download finished in {time.time()-t0:.1f}s.")

    # 2. Verify file size & SHA-256
    actual_size = ZIP_PATH.stat().st_size
    print(f"Verifying archive size: {actual_size:,} bytes...")
    if actual_size != EXPECTED_SIZE:
        raise ValueError(f"Size mismatch: expected {EXPECTED_SIZE}, got {actual_size}")

    print("Computing SHA-256 checksum...")
    sha256 = hashlib.sha256()
    with open(ZIP_PATH, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    print(f"[OK] Archive SHA-256: {checksum}")
    
    # Save checksum manifest
    with open(DOWNLOADS_DIR / "archive_checksum.sha256", "w") as f:
        f.write(f"{checksum}  Plant_leaf_diseases_dataset_without_augmentation.zip\n")

    # 3. Extract to EXTRACT_DIR
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Inspecting zip contents and extracting to: {EXTRACT_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        file_list = zf.namelist()
        print(f"Total entries in archive: {len(file_list):,}")
        zf.extractall(EXTRACT_DIR)
    print("[OK] Extraction complete.")

if __name__ == "__main__":
    download_and_verify()
