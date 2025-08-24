import asyncio
from undetected_playwright.async_api import async_playwright, Playwright
import json
import requests
import urllib.parse
import csv
import random
import os
from datetime import datetime


def get_random_cookie_file():
    """Lấy random một file cookie từ thư mục cookies_instagram"""
    cookie_dir = "cookies_instagram"
    
    # Kiểm tra thư mục có tồn tại không
    if not os.path.exists(cookie_dir):
        print(f"Thư mục {cookie_dir} không tồn tại, sử dụng cookie_1.json")
        return "cookie_1.json"
    
    # Lấy danh sách các file cookie
    cookie_files = [f for f in os.listdir(cookie_dir) if f.endswith('.json')]
    
    if not cookie_files:
        print("Không tìm thấy file cookie nào, sử dụng cookie_1.json")
        return "cookie_1.json"
    
    # Random chọn một file cookie
    selected_cookie = random.choice(cookie_files)
    cookie_path = os.path.join(cookie_dir, selected_cookie)
    
    print(f"Đã chọn cookie: {selected_cookie}")
    return cookie_path


def parse_instagram_data_to_csv(data, csv_file_path: str, is_first_write: bool = False):
    try:
        # Tìm dữ liệu media trong response Instagram
        media_items = []
        
        # Kiểm tra các section có chứa media
        if 'media_grid' in data and 'sections' in data['media_grid']:
            for section in data['media_grid']['sections']:
                if 'layout_content' in section and 'medias' in section['layout_content']:
                    for media_wrapper in section['layout_content']['medias']:
                        if 'media' in media_wrapper:
                            media_items.append(media_wrapper['media'])
        
        if not media_items:
            print("Không tìm thấy dữ liệu media trong response Instagram")
            print(f"Cấu trúc data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return
        
        print(f"Tìm thấy {len(media_items)} media items")
        
        # Chuẩn bị dữ liệu cho CSV
        csv_data = []
        for media in media_items:
            try:
                # Lấy code để tạo URL
                code = media.get('code', '')
                if code:
                    # Tạo URL Instagram post
                    url = f"https://www.instagram.com/p/{code}/"
                    
                    # Lấy created_at và chuyển thành timestamp
                    created_at = media.get('taken_at', 0)
                    
                    # Lấy like_count
                    like_count = media.get('like_count', 0)
                    
                    # Lấy comment_count
                    comment_count = media.get('comment_count', 0)
                    
                    # Lấy caption text nếu có
                    caption_text = ""
                    if 'caption' in media and media['caption']:
                        caption_text = media['caption'].get('text', '')
                    
                    # Lấy thông tin user
                    username = ""
                    if 'user' in media and media['user']:
                        username = media['user'].get('username', '')
                    
                    csv_data.append({
                        'url': url,
                        'created_at': created_at,
                        'like_count': like_count,
                        'comment_count': comment_count,
                        'username': username,
                        'caption': caption_text
                    })
                
            except Exception as e:
                print(f"Lỗi khi parse media item: {e}")
                continue
        
        # Lưu vào CSV
        if csv_data:
            fieldnames = ['url', 'created_at', 'like_count', 'comment_count', 'username', 'caption']
            
            # Chọn mode ghi file
            mode = 'w' if is_first_write else 'a'
            
            with open(csv_file_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Chỉ ghi header khi tạo file mới
                if is_first_write:
                    writer.writeheader()
                
                writer.writerows(csv_data)
            
            if is_first_write:
                print(f"Đã tạo file mới và lưu {len(csv_data)} media items vào {csv_file_path}")
            else:
                print(f"Đã thêm {len(csv_data)} media items vào {csv_file_path}")
        else:
            print("Không có dữ liệu để lưu")
            
    except Exception as e:
        print(f"Lỗi khi parse dữ liệu: {e}")
        import traceback
        traceback.print_exc()


async def open_instagram_search(keyword: str):
    """Mở URL Instagram search với keyword và bắt API"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load cookies từ file random
        try:
            cookie_file = get_random_cookie_file()
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # Đặt cookies vào browser
            await page.context.add_cookies(cookies)
            print(f"Đã load cookies thành công từ {cookie_file}")
        except Exception as e:
            print(f"Lỗi khi load cookies: {e}")
        
        # Tạo URL search
        search_url = f"https://www.instagram.com/explore/search/keyword/?q={keyword}"
        
        # Mở trang
        await page.goto(search_url)
        
        # Refresh trang
        await page.reload()
        
        # Bắt API calls và headers
        api_responses = []
        api_headers = {}
        api_url = ""
        total_items_collected = 0  # Đếm tổng số items đã thu thập
        
        async def handle_request(request):
            if "api/v1/fbsearch/web/top_serp" in request.url:
                nonlocal api_url, api_headers
                api_url = request.url
                api_headers = request.headers
                print(f"Bắt được API request: {request.url}")
        
        async def handle_response(response):
            if "api/v1/fbsearch/web/top_serp" in response.url:
                try:
                    nonlocal total_items_collected
                    
                    response_data = await response.json()
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'data': response_data
                    })
                    print(f"Bắt được API response: {response.url}")
                    print(f"Status: {response.status}")
                    
                    # Parse và lưu thành CSV trực tiếp từ dữ liệu
                    csv_file = f'instagram_search_{keyword}.csv'
                    # Kiểm tra xem file đã tồn tại chưa để quyết định ghi mới hay ghi tiếp
                    import os
                    is_first = not os.path.exists(csv_file)
                    
                    # Đếm số media items trong response này
                    items_in_response = 0
                    if 'media_grid' in response_data and 'sections' in response_data['media_grid']:
                        for section in response_data['media_grid']['sections']:
                            if 'layout_content' in section and 'medias' in section['layout_content']:
                                items_in_response += len(section['layout_content']['medias'])
                    
                    # Kiểm tra xem có vượt quá 50 items không
                    if total_items_collected + items_in_response > 50:
                        print(f"Đã thu thập {total_items_collected} items, response này có {items_in_response} items")
                        print("Sẽ lấy toàn bộ response này và dừng thu thập")
                        
                        # Lấy toàn bộ response data
                        parse_instagram_data_to_csv(response_data, csv_file, is_first_write=is_first)
                        total_items_collected += items_in_response
                        print(f"Đã thu thập tổng cộng {total_items_collected} items, dừng thu thập")
                        return  # Dừng xử lý response này
                    else:
                        parse_instagram_data_to_csv(response_data, csv_file, is_first_write=is_first)
                        total_items_collected += items_in_response
                        print(f"Đã thu thập tổng cộng {total_items_collected} items")
                    
                    # Kiểm tra nếu đã đủ 50 items thì dừng
                    if total_items_collected >= 50:
                        print(f"Đã thu thập đủ {total_items_collected} items, dừng thu thập")
                        return
                    
                except Exception as e:
                    print(f"Lỗi khi xử lý response: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Lắng nghe request và response
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # Cuộn trang để bắt được nhiều API calls hơn
        print("Bắt đầu cuộn trang để lấy thêm dữ liệu...")
        scroll_count = 0
        max_scrolls = 3
        
        for i in range(max_scrolls):
            # Kiểm tra nếu đã đủ 50 items thì dừng cuộn
            if total_items_collected >= 50:
                print(f"Đã đủ {total_items_collected} items, dừng cuộn trang")
                break
                
            try:
                # Cuộn xuống cuối trang
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                scroll_count += 1
                print(f"Đã cuộn lần {scroll_count}")
                
                # Đợi để trang load thêm nội dung
                await asyncio.sleep(5)
                
                # Đợi thêm để đảm bảo nội dung đã load xong
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                
                # Kiểm tra xem có cuộn được thêm không
                previous_height = await page.evaluate("document.body.scrollHeight")
                await asyncio.sleep(3)
                new_height = await page.evaluate("document.body.scrollHeight")
                
                print(f"Chiều cao trang: {previous_height} -> {new_height}")
                
                # Nếu không cuộn được thêm thì thử cuộn thêm vài lần nữa
                if new_height == previous_height:
                    for retry in range(2):
                        await asyncio.sleep(2)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(3)
                        final_height = await page.evaluate("document.body.scrollHeight")
                        if final_height > new_height:
                            new_height = final_height
                            print(f"Cuộn thêm được sau retry: {final_height}")
                            break
                    
                    if new_height == previous_height:
                        print("Đã cuộn đến cuối trang, không thể cuộn thêm")
                        break
                    
            except Exception as e:
                print(f"Lỗi khi cuộn trang lần {i+1}: {e}")
                break
        
        print(f"Hoàn thành cuộn trang, đã cuộn {scroll_count} lần")
        print(f"Tổng cộng đã thu thập {total_items_collected} items")
        
        # Nếu chưa đủ 50 items và có API URL, thực hiện request trực tiếp
        if total_items_collected < 50 and api_url and api_headers:
            try:
                print("\nThực hiện request trực tiếp để lấy thêm dữ liệu...")
                response = requests.get(api_url, headers=api_headers)
                
                if response.status_code == 200:
                    direct_response_data = response.json()
                    
                    if total_items_collected < 50:
                        csv_file = f'instagram_search_{keyword}.csv'
                        parse_instagram_data_to_csv(direct_response_data, csv_file, is_first_write=False)
                        
                        # Cập nhật số items đã thu thập
                        items_in_direct = 0
                        if 'media_grid' in direct_response_data and 'sections' in direct_response_data['media_grid']:
                            for section in direct_response_data['media_grid']['sections']:
                                if 'layout_content' in section and 'medias' in section['layout_content']:
                                    items_in_direct += len(section['layout_content']['medias'])
                        
                        total_items_collected += items_in_direct
                        print(f"Sau request trực tiếp: tổng cộng {total_items_collected} items")
                    else:
                        print("Đã đủ 50 items, không cần request trực tiếp")
                    
                else:
                    print(f"Request trực tiếp thất bại: {response.status_code}")
                    
            except Exception as e:
                print(f"Lỗi khi thực hiện request trực tiếp: {e}")
        
        # Hiển thị kết quả cuối cùng
        print(f"\n=== KẾT QUẢ CUỐI CÙNG ===")
        print(f"Tổng số items đã thu thập: {total_items_collected}")
        print(f"File CSV: instagram_search_{keyword}.csv")
        
        # Giữ browser mở
        await page.wait_for_timeout(30000)
        await browser.close()


async def main():
    """Hàm main để chạy chương trình"""
    keyword = input("Nhập từ khóa tìm kiếm: ")
    await open_instagram_search(keyword)


if __name__ == "__main__":
    asyncio.run(main())