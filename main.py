from downloader import download_latest_bpdk
from downloader_pkd import run_pkd_downloader
from downloader_sk_api import download_latest_sk
from downloader_pk5l import download_latest_pk5l  # Dodane

import time

if __name__ == "__main__":
    while True:
        run_pkd_downloader()       # pobiera PKD (D-1, 14–22)
        download_latest_bpdk()     # pobiera nowy BPKD jeśli dostępny
        download_latest_sk()       # pobiera SK tylko jeśli się zmieni
        download_latest_pk5l()     # NOWOŚĆ: pobieranie planu 5-letniego
        time.sleep(300)            # odświeżanie co 5 minut
