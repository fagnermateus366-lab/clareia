"""Download the curated CC BY 4.0 tracks from their composer's official host."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    from overview.music import catalog, ensure_track
    with ThreadPoolExecutor(max_workers=3) as pool:
        for title,path in pool.map(lambda t:(t['nome'],ensure_track(t['id'])),catalog()):
            print(title,path.stat().st_size,flush=True)

if __name__=='__main__':main()
