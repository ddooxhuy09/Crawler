import requests
import os
from urllib.parse import urlparse


def get_thumbnail(url_thumbnail: str) -> None:
    """Download a TikTok thumbnail from the provided URL using simple working headers."""
    if not url_thumbnail:
        print("❌ Vui lòng nhập url_thumbnail hợp lệ!")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        print("🔍 Đang tải thumbnail...")
        resp = requests.get(url_thumbnail, headers=headers, timeout=15)
        print(f"📊 Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print("❌ Không thể tải thumbnail.")
            return

        # Tạo tên file từ đường dẫn URL
        parsed = urlparse(url_thumbnail)
        basename = os.path.basename(parsed.path) or "tiktok_thumbnail"
        # Đảm bảo đuôi .jpg (phần lớn thumbnail là jpeg)
        if not basename.lower().endswith((".jpg", ".jpeg")):
            basename += ".jpg"

        os.makedirs("thumbnails", exist_ok=True)
        out_path = os.path.join("thumbnails", basename)
        with open(out_path, "wb") as f:
            f.write(resp.content)

        print(f"✅ Đã lưu thumbnail: {out_path}")

    except Exception as e:
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    url = input("Nhập url_thumbnail: ").strip()
    get_thumbnail(url)
