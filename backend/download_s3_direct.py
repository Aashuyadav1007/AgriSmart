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

S3_DIRECT_URL = "https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/d29ed9b2-8a5d-4663-8a82-c9174f2c7066"
TOTAL_SIZE = 868032562

def main():
    print("=" * 75)
    print("AgriMind AI - Direct Amazon S3 Dataset Stream (Resume Enabled)")
    print(f"URL: {S3_DIRECT_URL}")
    print(f"Target file: {ZIP_PATH}")
    print(f"Expected Size: {TOTAL_SIZE:,} bytes ({TOTAL_SIZE / (1024*1024):.2f} MB)")
    print("=" * 75)

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    existing_bytes = 0
    if ZIP_PATH.exists():
        existing_bytes = ZIP_PATH.stat().st_size

    if existing_bytes == TOTAL_SIZE:
        print(f"[OK] Full file already downloaded ({existing_bytes:,} bytes).")
    elif existing_bytes > TOTAL_SIZE:
        print(f"[WARN] File on disk ({existing_bytes:,} bytes) exceeds expected size. Truncating to 0...")
        ZIP_PATH.unlink()
        existing_bytes = 0

    if existing_bytes < TOTAL_SIZE:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        mode = "wb"
        if existing_bytes > 0:
            headers["Range"] = f"bytes={existing_bytes}-"
            mode = "ab"
            print(f"Resuming download from byte {existing_bytes:,} ({existing_bytes / (1024*1024):.2f} MB)...")
        else:
            print("Starting fresh download from byte 0...")

        req = urllib.request.Request(S3_DIRECT_URL, headers=headers)
        t0 = time.time()
        downloaded_session = 0
        current_total = existing_bytes

        with urllib.request.urlopen(req, timeout=60) as resp, open(ZIP_PATH, mode) as out_file:
            print(f"Connected! Response status: {resp.status}, Content-Length: {resp.headers.get('Content-Length')}")
            chunk_size = 512 * 1024  # 512 KB
            while True:
                buf = resp.read(chunk_size)
                if not buf:
                    break
                out_file.write(buf)
                out_file.flush()
                n = len(buf)
                downloaded_session += n
                current_total += n
                pct = (current_total / TOTAL_SIZE) * 100
                elapsed = time.time() - t0
                speed_mb = (downloaded_session / (1024 * 1024)) / max(elapsed, 0.001)
                remaining_mb = (TOTAL_SIZE - current_total) / (1024 * 1024)
                eta_s = (remaining_mb / max(speed_mb, 0.001))
                print(f"\rProgress: {current_total/(1024*1024):.1f}/{TOTAL_SIZE/(1024*1024):.1f} MB ({pct:.1f}%) | Speed: {speed_mb:.2f} MB/s | ETA: {eta_s:.0f}s    ", end="", flush=True)

        print(f"\n[OK] Download session completed in {time.time()-t0:.1f}s.")

    # Verify exact size
    final_size = ZIP_PATH.stat().st_size
    print(f"\nFinal file size on disk: {final_size:,} bytes")
    if final_size != TOTAL_SIZE:
        raise ValueError(f"Size mismatch: expected {TOTAL_SIZE}, got {final_size}")

    print("Computing SHA-256 checksum...")
    sha256 = hashlib.sha256()
    with open(ZIP_PATH, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    print(f"[OK] Archive SHA-256: {checksum}")
    with open(DOWNLOADS_DIR / "archive_checksum.sha256", "w") as f:
        f.write(f"{checksum}  Plant_leaf_diseases_dataset_without_augmentation.zip\n")

    # Safe extraction
    print(f"\nExtracting archive into: {EXTRACT_DIR}...")
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        namelist = zf.namelist()
        print(f"Archive entries: {len(namelist):,}")
        zf.extractall(EXTRACT_DIR)
    print("[OK] Extraction complete.")

    # Run verification pipeline
    print("\n" + "=" * 75)
    print("Executing Stage 1 Verification & Consolidation Pipeline...")
    print("=" * 75)
    import verify_and_consolidate_datasets
    verify_and_consolidate_datasets.run_verification()

if __name__ == "__main__":
    main()
