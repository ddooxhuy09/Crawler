import asyncio
from undetected_playwright.async_api import async_playwright, Playwright
import json
import requests
import urllib.parse
import csv
from datetime import datetime


def parse_tiktok_data_to_csv(data, csv_file_path: str, is_first_write: bool = False):
    try:
        # Tìm dữ liệu video trong response
        videos = []
        if 'data' in data:
            for item in data['data']:
                if item.get('type') == 1 and 'item' in item:
                    videos.append(item['item'])
        
        if not videos:
            print("Không tìm thấy dữ liệu video trong response")
            print(f"Cấu trúc data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if 'data' in data:
                print(f"Số lượng items trong data: {len(data['data'])}")
                if len(data['data']) > 0:
                    print(f"Item đầu tiên keys: {list(data['data'][0].keys())}")
            return
        
        print(f"Tìm thấy {len(videos)} videos")
        
        # Chuẩn bị dữ liệu cho CSV
        csv_data = []
        for video in videos:
            try:
                # Lấy thông tin author
                author_id = video.get('author', {}).get('id', '')
                
                # Lấy thông tin video
                video_id = video.get('id', '')
                
                # Tạo URL
                video_url = f"https://www.tiktok.com/@{author_id}/video/{video_id}"
                
                # Chuyển đổi createTime thành datetime
                create_time = video.get('createTime', 0)
                if create_time:
                    # TikTok sử dụng timestamp Unix (giây)
                    create_datetime = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    create_datetime = ''
                
                # Lấy các metrics từ stats
                stats = video.get('stats', {})
                share_count = stats.get('shareCount', 0)
                comment_count = stats.get('commentCount', 0)
                play_count = stats.get('playCount', 0)
                digg_count = stats.get('diggCount', 0)
                collect_count = stats.get('collectCount', 0)
                
                # Lấy mô tả video
                desc = video.get('desc', '')
                
                # Lấy thông tin author
                author_nickname = video.get('author', {}).get('nickname', '')
                author_unique_id = video.get('author', {}).get('uniqueId', '')

                thumnail_url = video.get('video', {}).get('cover', '')
                
                csv_data.append({
                    'createTime': create_datetime,
                    'url': video_url,
                    'author_id': author_id,
                    'video_id': video_id,
                    'author_nickname': author_nickname,
                    'author_unique_id': author_unique_id,
                    'desc': desc,
                    'shareCount': share_count,
                    'commentCount': comment_count,
                    'playCount': play_count,
                    'diggCount': digg_count,
                    'collectCount': collect_count,
                    'thumnail_url': thumnail_url
                })
                
            except Exception as e:
                print(f"Lỗi khi parse video: {e}")
                continue
        
        # Lưu vào CSV
        if csv_data:
            fieldnames = [
                'createTime', 'url', 'author_id', 'video_id', 'author_nickname', 
                'author_unique_id', 'desc', 'shareCount', 'commentCount', 
                'playCount', 'diggCount', 'collectCount', 'thumnail_url'
            ]
            
            # Chọn mode ghi file
            mode = 'w' if is_first_write else 'a'
            newline_param = '' if is_first_write else '\n'
            
            with open(csv_file_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Chỉ ghi header khi tạo file mới
                if is_first_write:
                    writer.writeheader()
                
                writer.writerows(csv_data)
            
            if is_first_write:
                print(f"Đã tạo file mới và lưu {len(csv_data)} videos vào {csv_file_path}")
            else:
                print(f"Đã thêm {len(csv_data)} videos vào {csv_file_path}")
        else:
            print("Không có dữ liệu để lưu")
            
    except Exception as e:
        print(f"Lỗi khi parse dữ liệu: {e}")
        import traceback
        traceback.print_exc()


async def open_tiktok_search(keyword: str):
    """Mở URL TikTok search với keyword và bắt API"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Tạo URL search
        search_url = f"https://www.tiktok.com/search?q={keyword}"
        
        # Mở trang
        await page.goto(search_url)
        
        # Refresh trang
        await page.reload()
        
        # Bắt API calls và headers
        api_responses = []
        api_headers = {}
        api_url = ""
        total_videos_collected = 0  # Đếm tổng số videos đã thu thập
        
        async def handle_request(request):
            if "api/search/general/full" in request.url:
                nonlocal api_url, api_headers
                api_url = request.url
                api_headers = request.headers
        
        async def handle_response(response):
            if "api/search/general/full" in response.url:
                try:
                    nonlocal total_videos_collected  # Thêm nonlocal để truy cập biến từ outer scope
                    
                    response_data = await response.json()
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'data': response_data
                    })
                    print(f"Bắt được API response: {response.url}")
                    print(f"Status: {response.status}")
                    
                    # Parse và lưu thành CSV trực tiếp từ dữ liệu
                    csv_file = f'tiktok_videos_{keyword}.csv'
                    # Kiểm tra xem file đã tồn tại chưa để quyết định ghi mới hay ghi tiếp
                    import os
                    is_first = not os.path.exists(csv_file)
                    
                    # Đếm số videos trong response này
                    videos_in_response = 0
                    if 'data' in response_data:
                        for item in response_data['data']:
                            if item.get('type') == 1 and 'item' in item:
                                videos_in_response += 1
                    
                    # Kiểm tra xem có vượt quá 50 videos không
                    if total_videos_collected + videos_in_response > 50:
                        print(f"Đã thu thập {total_videos_collected} videos, response này có {videos_in_response} videos")
                        print("Sẽ lấy toàn bộ response này và dừng thu thập")
                        
                        # Lấy toàn bộ response data
                        parse_tiktok_data_to_csv(response_data, csv_file, is_first_write=is_first)
                        total_videos_collected += videos_in_response
                        print(f"Đã thu thập tổng cộng {total_videos_collected} videos, dừng thu thập")
                        return  # Dừng xử lý response này
                    else:
                        parse_tiktok_data_to_csv(response_data, csv_file, is_first_write=is_first)
                        total_videos_collected += videos_in_response
                        print(f"Đã thu thập tổng cộng {total_videos_collected} videos")
                    
                    # Kiểm tra nếu đã đủ 50 videos thì dừng
                    if total_videos_collected >= 50:
                        print(f"Đã thu thập đủ {total_videos_collected} videos, dừng thu thập")
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
            # Kiểm tra nếu đã đủ 50 videos thì dừng cuộn
            if total_videos_collected >= 50:
                print(f"Đã đủ {total_videos_collected} videos, dừng cuộn trang")
                break
                
            try:
                # Cuộn xuống cuối trang
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                scroll_count += 1
                print(f"Đã cuộn lần {scroll_count}")
                
                # Đợi để trang load thêm nội dung - tăng thời gian chờ
                await asyncio.sleep(5)
                
                # Đợi thêm để đảm bảo nội dung đã load xong
                try:
                    # Đợi cho đến khi không còn network activity
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass  # Nếu timeout thì tiếp tục
                
                # Kiểm tra xem có cuộn được thêm không
                previous_height = await page.evaluate("document.body.scrollHeight")
                
                # Đợi thêm một chút để đảm bảo nội dung mới đã được render
                await asyncio.sleep(3)
                
                new_height = await page.evaluate("document.body.scrollHeight")
                
                print(f"Chiều cao trang: {previous_height} -> {new_height}")
                
                # Nếu không cuộn được thêm thì thử cuộn thêm vài lần nữa
                if new_height == previous_height:
                    # Thử cuộn thêm 2-3 lần nữa để đảm bảo
                    for retry in range(2):
                        await asyncio.sleep(2)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(3)
                        final_height = await page.evaluate("document.body.scrollHeight")
                        if final_height > new_height:
                            new_height = final_height
                            print(f"Cuộn thêm được sau retry: {final_height}")
                            break
                    
                    # Nếu vẫn không cuộn được thì dừng
                    if new_height == previous_height:
                        print("Đã cuộn đến cuối trang, không thể cuộn thêm")
                        break
                    
            except Exception as e:
                print(f"Lỗi khi cuộn trang lần {i+1}: {e}")
                break
        
        print(f"Hoàn thành cuộn trang, đã cuộn {scroll_count} lần")
        print(f"Tổng cộng đã thu thập {total_videos_collected} videos")
        
        # Nếu chưa đủ 50 videos và có API URL, thực hiện request trực tiếp
        if total_videos_collected < 50 and api_url and api_headers:
            try:
                print("\nThực hiện request trực tiếp để lấy thêm dữ liệu...")
                response = requests.get(api_url, headers=api_headers)
                
                if response.status_code == 200:
                    direct_response_data = response.json()
                    
                    # Kiểm tra xem có cần lấy thêm không
                    if total_videos_collected < 50:
                        csv_file = f'tiktok_videos_{keyword}.csv'
                        parse_tiktok_data_to_csv(direct_response_data, csv_file, is_first_write=False)
                        
                        # Cập nhật số videos đã thu thập
                        videos_in_direct = 0
                        if 'data' in direct_response_data:
                            for item in direct_response_data['data']:
                                if item.get('type') == 1 and 'item' in item:
                                    videos_in_direct += 1
                        
                        total_videos_collected += videos_in_direct
                        print(f"Sau request trực tiếp: tổng cộng {total_videos_collected} videos")
                    else:
                        print("Đã đủ 50 videos, không cần request trực tiếp")
                    
                else:
                    print(f"Request trực tiếp thất bại: {response.status_code}")
                    
            except Exception as e:
                print(f"Lỗi khi thực hiện request trực tiếp: {e}")
        
        # Hiển thị kết quả cuối cùng
        print(f"\n=== KẾT QUẢ CUỐI CÙNG ===")
        print(f"Tổng số videos đã thu thập: {total_videos_collected}")
        print(f"File CSV: tiktok_videos_{keyword}.csv")
        
        # Giữ browser mở
        await page.wait_for_timeout(30000)
        await browser.close()