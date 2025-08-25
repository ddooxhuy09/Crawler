import asyncio
import json
import csv
import os
from pathlib import Path
from undetected_playwright.async_api import async_playwright


async def open_pinterest_with_keyword(keyword):
    # Get current working directory and construct relative paths
    current_dir = Path.cwd()
    user_data_dir = current_dir / "Profile"
    path_to_extension = current_dir / "1.9.9_0"

    url = f"https://www.pinterest.com/search/pins/?q={keyword}&rs=typed"

    # List to store extracted pin data
    extracted_pins = []

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=False,
                args=[
                    f"--disable-extensions-except={str(path_to_extension)}",
                    f"--load-extension={str(path_to_extension)}",
                ]
            )
        except Exception as e:
            print(f"❌ Lỗi với persistent context: {e}")
            print("🔄 Thử cách khác - sử dụng browser thường...")

        page = await browser.new_page()
        
        # Set up request interception to capture Pinterest API calls
        async def handle_request(request):
            if "pinterest.com/resource/PinResource/get/" in request.url:
                print(f"🔍 Captured PinResource API call: {request.url}")
        
        # Set up response interception to extract data
        async def handle_response(response):
            if "pinterest.com/resource/PinResource/get/" in response.url:
                try:
                    response_data = await response.json()
                    if response_data and "resource_response" in response_data:
                        pin_data = response_data["resource_response"]["data"]
                        
                        # Extract required fields
                        pin_info = {
                            "pin_url": f"https://www.pinterest.com/pin/{pin_data.get('id', '')}",
                            "canonical_pin_id": pin_data.get("pin_join", {}).get("canonical_pin", {}).get("id", ""),
                            "title": pin_data.get("seo_title", ""),
                            "description": pin_data.get("description", ""),
                            "image_url": pin_data.get("image_medium_url", ""),
                            "created_at": pin_data.get("created_at", ""),
                            "share_count": pin_data.get("share_count", 0),
                            "repin_count": pin_data.get("repin_count", 0),
                            "comment_count": pin_data.get("comment_count", 0),
                            "reaction_count": pin_data.get("reaction_counts", {}).get("1", 0),
                            "tracked_link": pin_data.get("tracked_link", ""),
                            "pinner_username": pin_data.get("pinner", {}).get("username", ""),
                            "pinner_full_name": pin_data.get("pinner", {}).get("full_name", ""),
                            "board_name": pin_data.get("board", {}).get("name", ""),
                            "board_url": f"https://www.pinterest.com{pin_data.get('board', {}).get('url', '')}",
                            "link": pin_data.get("link", ""),
                            "hashtags": ", ".join(pin_data.get("hashtags", []))
                        }
                        
                        extracted_pins.append(pin_info)
                        print(f"✅ Extracted pin: {pin_info['pin_url']}")
                        
                except Exception as e:
                    print(f"❌ Error parsing response: {e}")
        
        # Listen to all requests and responses
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print(f"🔍 Đang mở URL: {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        # Scroll down to trigger more API calls
        print("📜 Scrolling down to trigger more API calls...")
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            print(f"📜 Scroll {i+1}/5 completed")

        # Wait a bit more for any delayed API calls
        await page.wait_for_timeout(3000)

        # Save extracted data to CSV
        if extracted_pins:
            csv_filename = f"pinterest_pins_{keyword}.csv"
            with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "pin_url", "canonical_pin_id", "title", "description", "image_url",
                    "created_at", "share_count", "repin_count", "comment_count", 
                    "reaction_count", "tracked_link", "pinner_username", "pinner_full_name",
                    "board_name", "board_url", "link", "hashtags"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(extracted_pins)
            
            print(f"💾 Đã lưu {len(extracted_pins)} pins vào file {csv_filename}")
            
            # Print summary
            print("\n📊 Summary of extracted data:")
            for i, pin in enumerate(extracted_pins, 1):
                print(f"{i}. {pin['pin_url']} - {pin['title'][:50]}...")
        else:
            print("❌ Không tìm thấy pin data nào")

        await asyncio.sleep(10)

# Chạy script và lưu vào CSV
if __name__ == "__main__":
    # Get keyword from user input
    keyword = input("🔍 Nhập keyword để tìm kiếm trên Pinterest: ").strip()
    if keyword:
        print(f"🚀 Bắt đầu crawl với keyword: {keyword}")
        asyncio.run(open_pinterest_with_keyword(keyword))
    else:
        print("❌ Vui lòng nhập keyword!")