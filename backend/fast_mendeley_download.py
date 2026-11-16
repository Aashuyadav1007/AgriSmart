import os
import sys
import time
import zipfile
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BACKEND_DIR = Path(r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend")
DOWNLOADS_DIR = BACKEND_DIR / "data" / "downloads"
EXTRACT_DIR = BACKEND_DIR / "data" / "plantvillage_mendeley_extracted"
ZIP_PATH = DOWNLOADS_DIR / "Plant_leaf_diseases_dataset_without_augmentation.zip"

URL = "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded"
TOTAL_SIZE = 868032562
NUM_WORKERS = 16

def download_range(part_id: int, start: int, end: int, part_path: Path):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            if part_path.exists() and part_path.stat().st_size == (end - start + 1):
                return part_id, (end - start + 1)
            
            req = urllib.request.Request(URL, headers={
                "User-Agent": f"AgriMind-Downloader/{part_id}",
                "Range": f"bytes={start}-{end}"
            })
            with urllib.request.urlopen(req, timeout=30) as resp, open(part_path, "wb") as f:
                while True:
                    buf = resp.read(256 * 1024)
                    if not buf:
                        break
                    f.write(buf)
            
            if part_path.stat().st_size == (end - start + 1):
                return part_id, (end - start + 1)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
    raise RuntimeError(f"Part {part_id} failed after {max_retries} attempts")

def main():
    print("=" * 75)
    print("AgriMind AI - High-Speed Multi-Threaded Mendeley Archive Downloader")
    print(f"Target: {URL}")
    print(f"Total Size: {TOTAL_SIZE / (1024*1024):.2f} MB ({TOTAL_SIZE:,} bytes)")
    print(f"Parallel Workers: {NUM_WORKERS}")
    print("=" * 75)

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    chunk_size = (TOTAL_SIZE + NUM_WORKERS - 1) // NUM_WORKERS
    tasks = []
    part_files = []

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        for i in range(NUM_WORKERS):
            start = i * chunk_size
            end = min(start + chunk_size - 1, TOTAL_SIZE - 1)
            part_path = DOWNLOADS_DIR / f"chunk_{i:02d}.part"
            part_files.append(part_path)
            tasks.append(executor.submit(download_range, i, start, end, part_path))

        completed_bytes = 0
        for future in as_completed(tasks):
            part_id, nbytes = future.result()
            completed_bytes += nbytes
            elapsed = time.time() - t0
            pct = (completed_bytes / TOTAL_SIZE) * 100
            speed = (completed_bytes / (1024*1024)) / max(elapsed, 0.001)
            print(f"Part {part_id:02d} completed ({nbytes/(1024*1024):.1f} MB) | Total: {completed_bytes/(1024*1024):.1f}/{TOTAL_SIZE/(1024*1024):.1f} MB ({pct:.1f}%) - Speed: {speed:.2f} MB/s", flush=True)

    print(f"\nAll {NUM_WORKERS} parts downloaded in {time.time()-t0:.1f}s.")
    print("Assembling parts into final ZIP file...")
    
    with open(ZIP_PATH, "wb") as outfile:
        for pf in part_files:
            with open(pf, "rb") as infile:
                while True:
                    block = infile.read(4 * 1024 * 1024)
                    if not block:
                        break
                    outfile.write(block)
            # Remove part file after assembling
            pf.unlink(missing_ok=True)

    actual_size = ZIP_PATH.stat().st_size
    print(f"Assembled file size: {actual_size:,} bytes")
    if actual_size != TOTAL_SIZE:
        raise ValueError(f"Size mismatch: expected {TOTAL_SIZE}, got {actual_size}")

    print("Computing SHA-256 checksum...")
    sha256 = hashlib.sha256()
    with open(ZIP_PATH, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    print(f"[OK] Archive SHA-256: {checksum}")
    with open(DOWNLOADS_DIR / "archive_checksum.sha256", "w") as f:
        f.write(f"{checksum}  Plant_leaf_diseases_dataset_without_augmentation.zip\n")

    print(f"\nExtracting archive safely into: {EXTRACT_DIR}...")
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        namelist = zf.namelist()
        print(f"Archive contains {len(namelist):,} entries.")
        zf.extractall(EXTRACT_DIR)
    print("[OK] Extraction complete.")

    # Now execute verification pipeline
    print("\n" + "=" * 75)
    print("Launching Verification & Consolidation Pipeline...")
    print("=" * 75)
    from verify_and_consolidate_datasets import run_verification
    run_verification()

if __name__ == "__main__":
    main()
