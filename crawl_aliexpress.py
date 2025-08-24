import asyncio
from undetected_playwright.async_api import async_playwright
import json
import csv
import re
from datetime import datetime
from bs4 import BeautifulSoup


async def capture_aliexpress_api():
    """Mở trang chính AliExpress và bắt API khi URL thay đổi"""
    async with async_playwright() as p:
        browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
        ]
        browser = await p.chromium.launch(headless=False, args=browser_args)
        page = await browser.new_page()
        
        # Mở trang chính AliExpress
        main_url = "https://vi.aliexpress.com/"
        await page.goto(main_url)
        
        print("Đã mở trang chính AliExpress")
        print("Bây giờ bạn có thể nhập keyword vào ô tìm kiếm trên trang web")
        print("Script sẽ tự động bắt API khi URL thay đổi thành trang search")
        
        # Đợi để trang load xong
        await asyncio.sleep(5)
        
        # Bắt API calls và headers
        api_responses = []
        api_headers = {}
        api_url = ""
        search_detected = False
        
        # Lắng nghe request và response NGAY LẬP TỨC
        page.on("request", lambda request: asyncio.create_task(handle_request(request)))

        async def handle_request(request):
            # Bắt tất cả các API calls của AliExpress
            if any(domain in request.url for domain in [
                "recom-acs.aliexpress.com",
                "acs.aliexpress.com", 
                "api.aliexpress.com",
                "mtop.aliexpress.com"
            ]):
                nonlocal api_url, api_headers
                api_url = request.url
                api_headers = request.headers
        
        async def handle_url_change():
            nonlocal search_detected
            current_url = page.url
            if "/w/wholesale-" in current_url and ".html?" in current_url:
                if not search_detected:
                    search_detected = True
                    print(f"\n=== PHÁT HIỆN TRANG SEARCH ===")
                    print(f"URL hiện tại: {current_url}")
                    print("Reload trang để bắt đầu bắt API calls...")
                    
                    # Reload trang search
                    await page.reload()
                    print("Đã reload trang search")
                    
                    # Đợi để trang reload xong
                    await asyncio.sleep(5)
                    
                    try:
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        print("Trang search đã load xong sau khi reload")
                    except:
                        print("Timeout khi đợi trang load, tiếp tục...")
                    
                    # Đợi thêm để đảm bảo API calls được thực hiện
                    print("Đợi thêm để bắt API calls...")
                    await asyncio.sleep(5)
                    
                    # Kiểm tra xem có bắt được API không
                    if api_url:
                        print(f"Đã bắt được API: {api_url}")
                    else:
                        print("Chưa bắt được API")
        
        # Kiểm tra URL định kỳ
        async def monitor_url():
            while True:
                await handle_url_change()
                await asyncio.sleep(2)  # Kiểm tra mỗi 2 giây
        
        # Đợi để trang load xong
        print("Đang đợi trang load xong...")
        await asyncio.sleep(5)
        
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        print("Trang đã load xong")
        
        # Bắt đầu monitor URL
        print("Bắt đầu monitor thay đổi URL...")
        url_monitor_task = asyncio.create_task(monitor_url())
        
        # Nếu có API URL, thực hiện request trực tiếp
        if api_url:
            try:
                print("\nThực hiện request trực tiếp đến trang search hiện tại...")
                import requests
                
                # Tạo session với headers và cookies từ API call
                session = requests.Session()
                
                # Thêm headers từ API call
                for key, value in api_headers.items():
                    if key.lower() not in ['host', 'content-length']:
                        session.headers[key] = value
                
                # Lấy cookies từ page context
                try:
                    cookies = await page.context.cookies()
                    for cookie in cookies:
                        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
                    print(f"Đã thêm {len(cookies)} cookies")
                except Exception as e:
                    print(f"Không thể lấy cookies: {e}")
                
                # Request đến trang search hiện tại
                current_search_url = page.url
                
                response = session.get(current_search_url)
                
                if response.status_code == 200:
                    
                    # Trích xuất sản phẩm từ trang đầu tiên
                    all_products = []
                    first_page_products = await extract_products_from_html(response.text)
                    if first_page_products:
                        all_products.extend(first_page_products)
                        print(f"Trang 1: {len(first_page_products)} sản phẩm")
                    
                    # Tiếp tục request các trang tiếp theo (page 2-10)
                    for page_num in range(2, 11):  # page 2-10
                        try:
                            # Tạo URL cho trang tiếp theo
                            if current_search_url.endswith('.html'):
                                next_page_url = current_search_url + f'?page={page_num}'
                            else:
                                next_page_url = current_search_url + f'&page={page_num}'
                            
                            # Request trang tiếp theo
                            next_page_response = session.get(next_page_url)
                            
                            if next_page_response.status_code == 200:
                                
                                # Trích xuất sản phẩm từ trang này
                                next_page_products = await extract_products_from_html(next_page_response.text)
                                
                                if next_page_products:
                                    all_products.extend(next_page_products)
                                    print(f"Trang {page_num}: {len(next_page_products)} sản phẩm")
                                else:
                                    print(f"Trang {page_num}: Không có sản phẩm mới")
                                    break  # Dừng nếu không có sản phẩm mới
                                
                                # Đợi một chút giữa các request để tránh bị block
                                await asyncio.sleep(2)
                                
                            else:
                                print(f"Trang {page_num} thất bại: {next_page_response.status_code}")
                                break  # Dừng nếu request thất bại
                                
                        except Exception as e:
                            print(f"Lỗi khi request trang {page_num}: {e}")
                            break
                    
                    # Lưu tất cả sản phẩm vào CSV
                    if all_products:
                        print(f"Tổng cộng: {len(all_products)} sản phẩm từ tất cả các trang")
                        await save_all_products_to_csv(all_products, "product_aliexpress.csv")
                    else:
                        print("Không có sản phẩm nào để lưu")
                    
                else:
                    print(f"Request trực tiếp thất bại: {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"Lỗi khi thực hiện request trực tiếp: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Không tìm thấy API call, đợi thêm...")
            # Đợi thêm để có thể bắt được API
            await asyncio.sleep(15)
            
            # Kiểm tra lại xem có bắt được API không
            if api_url:
                print(f"Đã bắt được API sau khi đợi: {api_url}")
                # Thực hiện request trực tiếp
                try:
                    print("\nThực hiện request trực tiếp đến trang search hiện tại...")
                    import requests
                    
                    session = requests.Session()
                    for key, value in api_headers.items():
                        if key.lower() not in ['host', 'content-length']:
                            session.headers[key] = value
                    
                    # Lấy cookies từ page context
                    try:
                        cookies = await page.context.cookies()
                        for cookie in cookies:
                            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
                        print(f"Đã thêm {len(cookies)} cookies")
                    except Exception as e:
                        print(f"Không thể lấy cookies: {e}")
                    
                    # Request đến trang search hiện tại
                    current_search_url = page.url
                    
                    response = session.get(current_search_url)
                    
                    if response.status_code == 200:
                        print("Request trực tiếp thành công!")
                        
                        # Trích xuất sản phẩm từ trang đầu tiên
                        all_products = []
                        first_page_products = await extract_products_from_html(response.text)
                        if first_page_products:
                            all_products.extend(first_page_products)
                            print(f"Trang 1: {len(first_page_products)} sản phẩm")
                        
                        # Tiếp tục request các trang tiếp theo (page 2-10)
                        for page_num in range(2, 11):  # page 2-10
                            try:
                                # Tạo URL cho trang tiếp theo
                                if current_search_url.endswith('.html'):
                                    next_page_url = current_search_url + f'?page={page_num}'
                                else:
                                    next_page_url = current_search_url + f'&page={page_num}'
                                
                                print(f"Đang request trang {page_num}: {next_page_url}")
                                
                                # Request trang tiếp theo
                                next_page_response = session.get(next_page_url)
                                
                                if next_page_response.status_code == 200:
                                    print(f"Trang {page_num} thành công! Response length: {len(next_page_response.text)} bytes")
                                    
                                    # Trích xuất sản phẩm từ trang này
                                    next_page_products = await extract_products_from_html(next_page_response.text)
                                    
                                    if next_page_products:
                                        all_products.extend(next_page_products)
                                        print(f"Trang {page_num}: {len(next_page_products)} sản phẩm")
                                    else:
                                        print(f"Trang {page_num}: Không có sản phẩm mới")
                                        break  # Dừng nếu không có sản phẩm mới
                                    
                                    # Đợi một chút giữa các request để tránh bị block
                                    await asyncio.sleep(2)
                                    
                                else:
                                    print(f"Trang {page_num} thất bại: {next_page_response.status_code}")
                                    break  # Dừng nếu request thất bại
                                    
                            except Exception as e:
                                print(f"Lỗi khi request trang {page_num}: {e}")
                                break
                        
                        # Lưu tất cả sản phẩm vào CSV
                        if all_products:
                            print(f"Tổng cộng: {len(all_products)} sản phẩm từ tất cả các trang")
                            await save_all_products_to_csv(all_products, "product.csv")
                        else:
                            print("Không có sản phẩm nào để lưu")
                    else:
                        print(f"Request trực tiếp thất bại: {response.status_code}")
                        
                except Exception as e:
                    print(f"Lỗi khi thực hiện request trực tiếp: {e}")
            else:
                print("Vẫn không bắt được API call")
        
        # Giữ browser mở lâu hơn để đảm bảo có thể bắt được API
        print("Đợi thêm để đảm bảo bắt được API...")
        await page.wait_for_timeout(30000)  # Đợi 30 giây
        await browser.close()

async def extract_products_from_html(html_content):
    """Trích xuất danh sách sản phẩm từ HTML content"""
    try:
        # Tìm tất cả các productId trong HTML
        product_ids = re.findall(r'"productId":"(\d+)"', html_content)
        print(f"Tìm thấy {len(product_ids)} productId")
        
        if not product_ids:
            return []
        
        # Trích xuất thông tin sản phẩm cho từng productId
        extracted_products = []
        for product_id in product_ids:
            try:
                print(f"\nĐang xử lý productId: {product_id}")
                
                # Tìm tất cả các trường dữ liệu cho productId này trong toàn bộ HTML
                product_info = {
                    'productId': product_id,
                    'url': f"https://vi.aliexpress.com/item/{product_id}.html",
                    'priceOriginal': '',
                    'salePrice': '',
                    'discount': '',
                    'tradeDesc': '',
                    'starRating': '',
                    'title': ''
                }
                
                # Tìm priceOriginal - tìm trong toàn bộ HTML
                price_original_pattern = rf'"productId":"{product_id}".*?"cent":(\d+)'
                price_original_match = re.search(price_original_pattern, html_content, re.DOTALL)
                if price_original_match:
                    product_info['priceOriginal'] = price_original_match.group(1)
                
                # Tìm salePrice - tìm trong toàn bộ HTML
                sale_price_pattern = rf'"productId":"{product_id}".*?"minPrice":(\d+)'
                sale_price_match = re.search(sale_price_pattern, html_content, re.DOTALL)
                if sale_price_match:
                    product_info['salePrice'] = sale_price_match.group(1)
                
                # Tìm discount - tìm trong toàn bộ HTML
                discount_pattern = rf'"productId":"{product_id}".*?"discount":(\d+)'
                discount_match = re.search(discount_pattern, html_content, re.DOTALL)
                if discount_match:
                    product_info['discount'] = discount_match.group(1)
                
                # Tìm tradeDesc - tìm trong toàn bộ HTML
                trade_desc_pattern = rf'"productId":"{product_id}".*?"tradeDesc":"([^"]+)"'
                trade_desc_match = re.search(trade_desc_pattern, html_content, re.DOTALL)
                if trade_desc_match:
                    product_info['tradeDesc'] = trade_desc_match.group(1)
                
                # Tìm starRating - tìm trong toàn bộ HTML
                star_rating_pattern = rf'"productId":"{product_id}".*?"starRating":(\d+(?:\.\d+)?)'
                star_rating_match = re.search(star_rating_pattern, html_content, re.DOTALL)
                if star_rating_match:
                    product_info['starRating'] = star_rating_match.group(1)
                
                # Tìm title - tìm trong toàn bộ HTML
                title_pattern = rf'"productId":"{product_id}".*?"displayTitle":"([^"]+)"'
                title_match = re.search(title_pattern, html_content, re.DOTALL)
                if title_match:
                    product_info['title'] = title_match.group(1)
                
                # Nếu không tìm thấy displayTitle, thử tìm title
                if not product_info['title']:
                    title_pattern_fallback = rf'"productId":"{product_id}".*?"title":"([^"]+)"'
                    title_match_fallback = re.search(title_pattern_fallback, html_content, re.DOTALL)
                    if title_match_fallback:
                        product_info['title'] = title_match_fallback.group(1)
                
                # Kiểm tra xem có tìm thấy dữ liệu gì không
                data_found = sum(1 for value in product_info.values() if value != '' and value != product_id)
                print(f"  Tổng cộng tìm thấy {data_found} trường dữ liệu")
                
                extracted_products.append(product_info)
                
            except Exception as e:
                print(f"  ❌ Lỗi khi parse sản phẩm {product_id}: {e}")
                continue
        
        return extracted_products
        
    except Exception as e:
        print(f"Lỗi khi trích xuất sản phẩm từ HTML: {e}")
        import traceback
        traceback.print_exc()
        return []

async def save_all_products_to_csv(all_products, csv_file):
    """Lưu tất cả sản phẩm vào CSV file"""
    try:
        print(f"Đang lưu {len(all_products)} sản phẩm vào CSV...")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['productId', 'url', 'priceOriginal', 'salePrice', 'discount', 'tradeDesc', 'starRating', 'title']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in all_products:
                writer.writerow(product)
        
        print(f"Đã lưu dữ liệu sản phẩm vào file {csv_file}")
        
    except Exception as e:
        print(f"Lỗi khi lưu CSV: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Hàm main để chạy crawler AliExpress"""
    print("=== ALIEXPRESS CRAWLER ===")
    print("Bắt đầu crawl AliExpress...")
    print("Script sẽ mở trang chính và chờ bạn nhập keyword")
    print("Sau khi nhập keyword và chuyển trang, script sẽ tự động bắt API calls")
    print("=" * 50)
    
    try:
        # Chạy async function
        asyncio.run(capture_aliexpress_api())
    except KeyboardInterrupt:
        print("\nĐã nhận tín hiệu dừng. Đang đóng...")
    except Exception as e:
        print(f"Lỗi khi chạy crawler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()