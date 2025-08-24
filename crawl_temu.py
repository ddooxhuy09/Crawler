import asyncio
import undetected_playwright as playwright
from playwright.async_api import async_playwright
import time
import re
import json
import requests
import csv
import os

async def open_temu():
    async with async_playwright() as p:
        # Khởi tạo browser với undetected mode
        browser = await p.chromium.launch(
            headless=False,  # Hiển thị browser
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-popup-blocking',
                '--disable-notifications',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        # Tạo context mới
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
        )
        
        # Tạo page mới
        page = await context.new_page()
        
        # Bắt đầu theo dõi network requests TRƯỚC KHI cuộn
        print("🔄 Bắt đầu theo dõi network requests...")
        network_monitor = await start_network_monitoring(page)
        
        try:
            print("Đang mở trang Temu...")
            
            # Mở trang Temu
            await page.goto('https://www.temu.com/', wait_until='networkidle')
            
            print("Đã mở thành công trang Temu!")
            print("URL hiện tại:", page.url)
            print("Tiêu đề trang:", await page.title())
            
            # Chờ một chút để trang load hoàn toàn
            await asyncio.sleep(5)
            
            # Theo dõi URL changes
            print("Đang theo dõi URL changes...")
            
            # Chờ và xử lý khi URL chuyển thành search result
            await wait_for_search_result_and_click_seemore(page)
            
            # SAU KHI cuộn xong, xử lý API calls đã bắt được
            print("🎯 Cuộn xong! Bây giờ xử lý API calls đã bắt được...")
            # await process_captured_api_calls(network_monitor) # This line is removed as per the new_code
            
            # Giữ browser mở để người dùng có thể xem
            print("Browser sẽ giữ mở. Nhấn Ctrl+C để đóng...")
            
            # Chờ người dùng đóng
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Lỗi khi mở trang Temu: {e}")
        
        finally:
            # Đóng browser
            await browser.close()

async def start_network_monitoring(page):
    api_calls = []
    
    async def handle_request(request):
        nonlocal api_calls  # Khai báo nonlocal để truy cập biến bên ngoài
        
        # Bắt tất cả API calls có offset (bỏ qua search_suggest)
        if "api/poppy/v1/search" in request.url:
            print(f"🔍 Đã bắt được API call: {request.url}")
            
            headers = request.headers
            
            # Lấy post data nếu có
            post_data = request.post_data
            if post_data:
                try:
                    post_json = json.loads(post_data)
                    offset = post_json.get('offset', 0)  # Sử dụng default value 0
                    print(f"📍 Offset: {offset}")
                except:
                    offset = 0
            else:
                offset = 0
            
            # Lưu tất cả API calls có offset > 0
            if offset > 0:
                # Lưu thông tin API call
                api_info = {
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(headers),
                    "post_data": post_data,
                    "offset": offset,
                    "timestamp": time.time()
                }
                api_calls.append(api_info)
                print(f"💾 Đã lưu API call với offset: {offset}")
                
                # Request ngay lập tức để lấy response
                try:
                    await request_and_save_api_response(api_info, page)
                except Exception as e:
                    print(f"❌ Lỗi khi request API offset {offset}: {e}")
    
    page.on("request", handle_request)
    
    print("✅ Đã bắt đầu theo dõi network requests")
    
    # Trả về object để có thể truy cập api_calls từ bên ngoài
    return {"api_calls": api_calls, "page": page}

async def process_captured_api_calls(network_monitor):
    api_calls = network_monitor["api_calls"]
    
    if not api_calls:
        print("⚠️ Không có API call nào được bắt được")
        return
    
    print(f"📊 Tổng số API calls đã bắt: {len(api_calls)}")
    
    # Lọc ra các API calls có offset > 0
    valid_api_calls = [api for api in api_calls if api.get('offset', 0) > 0]
    
    if not valid_api_calls:
        print("⚠️ Không có API call nào có offset hợp lệ")
        return
    
    print("✅ Tất cả API calls đã được xử lý trong quá trình scroll!")
    print("💾 Dữ liệu đã được append vào file products_temu.csv")
    
    # Dừng code sau khi hoàn thành
    print("🎯 Đang thoát...")
    import os
    os._exit(0)

async def parse_cookies(cookies):
    return '; '.join(f"{cookie['name']}={cookie['value']}" for cookie in cookies)

def extract_product_data(response_json):

    products = []
    
    try:
        # Lấy danh sách sản phẩm từ response
        if 'result' in response_json and 'data' in response_json['result']:
            data = response_json['result']['data']
            
            # Kiểm tra goods_list
            if 'goods_list' in data and isinstance(data['goods_list'], list):
                goods_list = data['goods_list']
                
                for product in goods_list:
                    try:
                        # Trích xuất các trường cần thiết
                        product_data = {
                            'url': f"https://www.temu.com/{product.get('link_url', '')}",
                            'price': product.get('price_info', {}).get('price', ''),
                            'market_price': product.get('price_info', {}).get('market_price', ''),
                            'currency': product.get('price_info', {}).get('currency', ''),
                            'sales_tip': product.get('sales_tip', ''),
                            'goods_score': product.get('comment', {}).get('goods_score', ''),
                            'comment_num_tips': product.get('comment', {}).get('comment_num_tips', '')
                        }
                        products.append(product_data)
                        
                    except Exception as e:
                        print(f"❌ Lỗi khi xử lý sản phẩm: {e}")
                        continue
                        
        print(f"📊 Đã trích xuất {len(products)} sản phẩm")
        return products
        
    except Exception as e:
        print(f"❌ Lỗi khi trích xuất dữ liệu: {e}")
        return []

def save_to_csv(products, filename="products_temu.csv"):
    try:
        if not products:
            print("⚠️ Không có dữ liệu để lưu CSV")
            return
        
        # Định nghĩa các cột
        fieldnames = ['url', 'price', 'market_price', 'currency', 'sales_tip', 'goods_score', 'comment_num_tips']
        
        # Kiểm tra file có tồn tại không
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Ghi header chỉ khi file là mới
            if not file_exists:
                writer.writeheader()
                print(f"📝 Tạo file CSV mới: {filename}")
            
            # Ghi dữ liệu
            for product in products:
                writer.writerow(product)
        
        print(f"💾 Đã append {len(products)} sản phẩm vào file: {filename}")
        
    except Exception as e:
        print(f"❌ Lỗi khi lưu CSV: {e}")

async def request_and_save_api_response(api_info, page):
    try:
        print(f"🚀 Đang request tới API (offset: {api_info.get('offset', 0)})...")
        
        # Chuẩn bị request
        url = api_info['url']
        method = api_info['method']
        headers = api_info['headers']
        post_data = api_info.get('post_data')

        cookies = await page.context.cookies()
        cookie_string = await parse_cookies(cookies)
        headers['cookie'] = cookie_string
        
        # Thực hiện request
        if method.upper() == 'POST' and post_data:
            # Parse JSON post data
            try:
                post_json = json.loads(post_data)
                print("📝 Sử dụng JSON post data")
                response = requests.post(url, headers=headers, json=post_json, timeout=30)
            except:
                print("📝 Sử dụng raw post data")
                response = requests.post(url, headers=headers, data=post_data, timeout=30)
        else:
            print("📝 Sử dụng GET request")
            response = requests.get(url, headers=headers)
        
        # Lấy response
        response_text = response.text
        response_status = response.status_code
        response_headers = dict(response.headers)
        
        try:
            response_json = json.loads(response_text)
            print("🎯 Response là JSON hợp lệ")
            
            # Lưu response JSON
            response_filename = f"temu_api_response_offset_{api_info.get('offset', 0)}.json"
            response_data = {
                "request_info": api_info,
                "response_status": response_status,
                "response_headers": response_headers,
                "response_data": response_json,
                "timestamp": time.time()
            }            
            # Trích xuất dữ liệu sản phẩm và append vào CSV
            products = extract_product_data(response_json)
            save_to_csv(products)
            
        except json.JSONDecodeError:
            print("⚠️ Response không phải JSON hợp lệ, lưu dưới dạng text")
        
        print(f"✅ Hoàn thành request API offset {api_info.get('offset', 0)}!")
        
    except Exception as e:
        print(f"❌ Lỗi khi request API: {e}")
        import traceback
        traceback.print_exc()

async def wait_for_search_result_and_click_seemore(page):
    max_attempts = 3
    current_attempts = 0
    
    while current_attempts < max_attempts:
        try:
            # Kiểm tra URL hiện tại
            current_url = page.url
            print(f"URL hiện tại: {current_url}")
            
            # Kiểm tra xem có phải search result page không
            if "search_result.html?search_key=" in current_url:
                print("Đã phát hiện trang search result!")
                
                # Cuộn xuống để tìm button See more
                await scroll_and_click_seemore(page)
                current_attempts += 1
                
                if current_attempts < max_attempts:
                    print(f"Đã click See more {current_attempts} lần. Chờ 3 giây trước khi tiếp tục...")
                    await asyncio.sleep(3)
                else:
                    print("Đã hoàn thành 3 lần click See more!")
                    print("🎯 Bây giờ script sẽ bắt API call và xét offset lớn nhất...")
                    print("💡 Hãy cuộn xuống hoặc thực hiện thao tác để trigger API calls!")
                    break
            else:
                print("Chưa phải trang search result, chờ 2 giây...")
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"Lỗi trong quá trình xử lý: {e}")
            await asyncio.sleep(2)

async def scroll_and_click_seemore(page):
    try:
        # Cuộn xuống từ từ để load content
        print("Đang cuộn xuống để tìm button See more...")
        
        # Cuộn xuống từng phần
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(1)
        
        # Tìm button See more
        see_more_button = None
        
        # Thử nhiều selector khác nhau
        selectors = [
            'div[role="button"] span:has-text("See more")',
            'span:has-text("See more")',
            'div[class*="See more"]',
            'button:has-text("See more")',
            '[class*="See more"]'
        ]
        
        for selector in selectors:
            try:
                see_more_button = await page.wait_for_selector(selector, timeout=5000)
                if see_more_button:
                    print(f"Đã tìm thấy button See more với selector: {selector}")
                    break
            except:
                continue
        
        if see_more_button:
            # Click vào button
            await see_more_button.click()
            print("Đã click button See more thành công!")
            
            # Chờ content load
            await asyncio.sleep(3)
            
            # Cuộn xuống thêm để load thêm content
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(2)
            
        else:
            print("Không tìm thấy button See more")
            
    except Exception as e:
        print(f"Lỗi khi cuộn và click See more: {e}")

def main():
    print("Bắt đầu mở trang Temu với undetected playwright...")
    
    try:
        # Chạy async function
        asyncio.run(open_temu())
    except KeyboardInterrupt:
        print("\nĐã nhận tín hiệu dừng. Đang đóng...")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    main()
