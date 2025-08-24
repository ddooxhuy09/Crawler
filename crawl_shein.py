import asyncio
from playwright.async_api import async_playwright
import json
import csv
import requests
from random import choice, randint
from user_agents import USER_AGENTS
import random
import time

def get_hardware_concurrency():
    """Get a realistic number of CPU cores."""
    return choice([2, 4, 6, 8, 12, 16])

def get_device_memory():
    """Get a realistic amount of device memory in GB."""
    return choice([4, 8, 16, 32])

def get_platform():
    """Get consistent platform info based on user agent."""
    platforms = {
        'Windows': {
            'platform': 'Win32',
            'oscpu': 'Windows NT 10.0',
            'vendor': 'Google Inc.',
            'renderer': 'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'languages': ['de-DE', 'de', 'en-US', 'en']
        },
        'Macintosh': {
            'platform': 'MacIntel',
            'oscpu': 'Intel Mac OS X 10_15_7',
            'vendor': 'Apple Computer, Inc.',
            'renderer': 'Apple GPU',
            'languages': ['de-DE', 'de', 'en-US', 'en']
        }
    }
    return platforms['Windows'] if 'Windows' in choice(USER_AGENTS) else platforms['Macintosh']

async def get_browser_context():
    """Get a configured browser context with realistic fingerprinting."""
    
    platform_info = get_platform()
    
    launch_options = {
        'headless': False,  # Keep False as in your original code
        'args': [
            '--disable-application-cache',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-extensions',
            '--disable-sync',
            '--metrics-recording-only',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-popup-blocking',
            '--disable-notifications',
            '--disable-translate',
            '--disable-web-security',
            f'--lang={platform_info["languages"][0]}',
            '--disable-blink-features=AutomationControlled',
            f'--hardware-concurrency={get_hardware_concurrency()}',
            f'--device-memory={get_device_memory()}'
        ]
    }
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(**launch_options)
    
    viewport_sizes = [
        {'width': 1920, 'height': 1080},
        {'width': 1280, 'height': 800},
        {'width': 1440, 'height': 900},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1600, 'height': 900},
        {'width': 1680, 'height': 1050},
        {'width': 1920, 'height': 1200},
    ]
    
    chosen_viewport = choice(viewport_sizes)
    screen = {
        'width': chosen_viewport['width'],
        'height': chosen_viewport['height'],
        'device_scale_factor': choice([1, 1.25, 1.5, 2])
    }
    
    timezones = {
        'de-DE': ['Europe/Berlin', 'Europe/Vienna', 'Europe/Zurich'],
        'en-GB': ['Europe/London', 'Europe/Dublin'],
    }
    
    chosen_locale = platform_info['languages'][0]
    chosen_timezone = choice(timezones.get(chosen_locale, ['Europe/Berlin']))
    
    context = await browser.new_context(
        user_agent=choice(USER_AGENTS),
        viewport=chosen_viewport,
        screen=screen,
        locale=chosen_locale,
        timezone_id=chosen_timezone,
        geolocation={'latitude': 48.1351 + random.uniform(-2, 2),
                    'longitude': 11.5820 + random.uniform(-2, 2)},
        color_scheme='light',
        permissions=['geolocation', 'notifications'],
        device_scale_factor=screen['device_scale_factor'],
        is_mobile=False,
        has_touch=False,
        java_script_enabled=True,
        bypass_csp=True,
        ignore_https_errors=True,
    )
    
    await context.add_init_script("""
        Object.defineProperty(navigator, 'platform', { get: () => '""" + platform_info['platform'] + """' });
        Object.defineProperty(navigator, 'vendor', { get: () => '""" + platform_info['vendor'] + """' });
        Object.defineProperty(navigator.connection, 'rtt', { get: () => """ + str(randint(50, 250)) + """ });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => """ + str(get_hardware_concurrency()) + """ });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => """ + str(get_device_memory()) + """ });
        Object.defineProperty(navigator, 'languages', { get: () => """ + str(platform_info['languages']) + """ });
        Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        Object.defineProperty(window, 'chrome', { get: () => true });
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        
        // WebGL fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return '""" + platform_info['renderer'] + """';
            }
            return getParameter.apply(this, arguments);
        };
    """)
    
    await context.add_cookies([
        {
            'name': 'user_session', 
            'value': f'session_{randint(1000000, 9999999)}',
            'domain': '.shein.com',
            'path': '/'
        },
        {
            'name': 'first_visit',
            'value': str(int(time.time() - randint(86400, 864000))),
            'domain': '.shein.com',
            'path': '/'
        }
    ])
    
    return p, browser, context

async def capture_shein_api():
    """Mở trang chính Shein và bắt API khi URL thay đổi"""
    # Use the new anti-detection browser context
    p, browser, context = await get_browser_context()
    
    # Create page from the anti-detection context
    page = await context.new_page()
    
    # Mở trang chính Shein
    main_url = "https://www.shein.com.vn/"
    await page.goto(main_url)
    
    print("Đã mở trang chính Shein (Vietnam)")
    print("Bây giờ bạn có thể nhập keyword vào ô tìm kiếm trên trang web")
    print("Script sẽ tự động bắt API khi URL thay đổi thành trang search")
    
    # Đợi để trang load xong
    await asyncio.sleep(5)
    
    # Bắt API calls và headers
    api_headers = {}
    api_url = ""
    search_detected = False

    # Lắng nghe request và response NGAY LẬP TỨC
    page.on("request", lambda request: asyncio.create_task(handle_request(request)))
    
    async def handle_request(request):
        # Chỉ bắt API search products cụ thể này
        target_api = "https://www.shein.com.vn/bff-api/product/get_products_by_keywords"
        
        if target_api in request.url:
            nonlocal api_url, api_headers
            api_url = request.url
            raw_headers = await request.all_headers()
            
            # Lọc bỏ HTTP/2 pseudo-headers (bắt đầu bằng :)
            api_headers = {}
            for key, value in raw_headers.items():
                if not key.startswith(':'):
                    api_headers[key] = value

    
    async def handle_url_change():
        nonlocal search_detected
        current_url = page.url
        # Shein Vietnam search URLs: https://www.shein.com.vn/pdsearch/{keyword}
        if "/pdsearch/" in current_url:
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
    
    # Đợi để có thể bắt được API
    print("Đang đợi để bắt API search products...")
    await asyncio.sleep(10)
    
    # Nếu có API URL, thực hiện request trực tiếp
    if api_url:
        try:
            print("\n🎯 THỰC HIỆN REQUEST ĐẾN API SEARCH PRODUCTS!")
            
            # Tạo session với headers từ API call
            session = requests.Session()
            
            # Lấy cookies từ page context và convert sang format đúng
            try:
                raw_cookies = await page.context.cookies()
                cookies = {}
                for cookie in raw_cookies:
                    cookies[cookie['name']] = cookie['value']
                print(f"Đã thêm {len(cookies)} cookies")
            except Exception as e:
                print(f"Không thể lấy cookies: {e}")
                cookies = {}

            # Debug: In ra headers và cookies được sử dụng
            print(f"\n=== DEBUG INFO ===")
            print(f"URL: {api_url}")
            print(f"Headers count: {len(api_headers)}")
            print(f"Cookies count: {len(cookies)}")
            
            # Kiểm tra headers quan trọng
            important_headers = ['accept', 'content-type', 'referer', 'user-agent']
            for header in important_headers:
                if header in api_headers:
                    print(f"✅ {header}: có")
                else:
                    print(f"❌ {header}: thiếu")
            
            # Bổ sung headers còn thiếu
            if 'content-type' not in api_headers:
                api_headers['content-type'] = 'application/json; charset=utf-8'
                print("✅ Đã bổ sung content-type header")
            
            # Sử dụng POST request như browser thực sự làm
            response = requests.post(api_url, headers=api_headers, cookies=cookies, timeout=30)
            
            # Nếu request thất bại, thử với headers từ test_shein.py
            if response.status_code != 200:
                print(f"⚠️ Request với browser headers thất bại: {response.status_code}")
                print("🔄 Thử với headers từ test_shein.py...")
                
                test_headers = {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "armortoken": "T0_3.8.2_aCVU9t692W3Glc9m72P-vbpjZyMh2Jk9MVJSMqbr1Y5jBUK0eIHKkq8SoqpH2SLau0smdt-UyXPSYnstykixNCAyewb6FAWG_TXDxcZrTBdBhO_gViObJz-r5E9MZdyGIMzACFDNdWUXYtnjBgXD3YXuy1X0qvSt0hBtL_iUKQz3ANBb2GdDsFhDi6k0DVZ__1755999172953",
                    "content-type": "application/json; charset=utf-8",
                    "referer": "https://www.shein.com.vn/pdsearch/turtle",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
                    "x-csrf-token": "E0UmSCIr-wIO69TD_HcDu40eHi12jqJezpQU",
                    "x-gw-auth": "a=xjqHR52UWJdjKJ0x6QrCsus66rNXR9@2.0.13&b=1755999193233&d=06942fbc37be6a98b8dee877d03ae8f6&e=YcREOZjg0OThjZmY0NzExN2I5YjEyYjVkMDdkYjcyMDhjN2Q3N2Y4ZTI1NjBlNTRkNTJhMGMzYTJhODVjNmYxMzdhNg%3D%3D",
                    "x-oest": "MEM0MTNEMDBfQ0FGQ18xOUM0X0ZCMUZfQUM0NkE2OUQyMzNEfDE3NTU5OTkxOTMyMjl8"
                }
                
                test_cookies = {
                    "armorUuid": "20250823232957165eaf44073da1ace36002582979b73e001a320d0053c79500",
                    "sessionID_shein": "s%3Ai4x5UwqD5P-9KvAIEbqK6BeMHZscDXFW.8v0vXpvdFOzWBkO5Js103V5ynhQPWzGq2VmRspsQ0",
                    "AT": "MDEwMDE.eyJiIjo3LCJnIjoxNzU1OTYyOTk3LCJyIjoiRHBDRXhxIiwidCI6MX0.71b7d0f49663d1d8",
                    "smidV2": "2025082322295923ec656b0a3d948b175acf498dcd78ca00d07a8c5e72e4590"
                }
                
                print("🧪 Thử request với test headers...")
                response = requests.post(api_url, headers=test_headers, cookies=test_cookies, timeout=30)
                print(f"Test response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Request thành công!")
                print(f"Response length: {len(response.text)} bytes")
                
                # Parse JSON response
                try:
                    data = response.json()
                    print("✅ Parse JSON thành công!")
                    
                    # Trích xuất thông tin sản phẩm từ trang đầu tiên
                    await extract_products_from_api_data(data, "product_shein.csv", is_first_page=True)
                    
                    # Tiếp tục lấy các trang từ 2-11
                    print("\n🔄 Bắt đầu lấy các trang tiếp theo (2-11)...")
                    await get_additional_pages(api_url, api_headers, cookies)
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Lỗi parse JSON: {e}")
                    print(f"Response text: {response.text[:500]}...")
                    
            else:
                print(f"❌ Request thất bại: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Lỗi khi thực hiện request: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Không bắt được API search products")
        print("Hãy thử search keyword 'turtle' trên trang web")
    
    # Giữ browser mở để kiểm tra
    print("Đợi thêm để kiểm tra...")
    await page.wait_for_timeout(30000)  # Đợi 30 giây
    
    await browser.close()
    await p.stop()


async def extract_products_from_api_data(data, csv_file, is_first_page=False):
    """Trích xuất thông tin sản phẩm từ API response và lưu vào CSV"""
    try:
        print("Đang trích xuất thông tin sản phẩm từ API...")
        
        # Tìm danh sách sản phẩm trong data.info.products
        products = []
        if 'info' in data and 'products' in data['info']:
            products = data['info']['products']
            print(f"Tìm thấy {len(products)} sản phẩm trong data.info.products")
        else:
            print("Không tìm thấy danh sách sản phẩm trong data.info.products")
            return
        
        if not products:
            print("Danh sách sản phẩm trống")
            return
        
        # Trích xuất thông tin sản phẩm
        extracted_products = []
        for product in products:
            try:
                # Lấy product ID
                goods_id = product.get('goods_id', '')
                
                # Tạo URL từ goods_url_name
                goods_url_name = product.get('goods_url_name', '')
                goods_url = f"https://www.shein.com.vn/{goods_url_name}.html" if goods_url_name else ''
                
                # Lấy giá từ các trường nested
                retail_price = ''
                if 'retailPrice' in product and 'amount' in product['retailPrice']:
                    retail_price = product['retailPrice']['amount']
                
                sale_price = ''
                if 'salePrice' in product and 'amount' in product['salePrice']:
                    sale_price = product['salePrice']['amount']
                
                discount_price = ''
                if 'discountPrice' in product and 'amount' in product['discountPrice']:
                    discount_price = product['discountPrice']['amount']
                
                # Lấy thông tin đánh giá
                comment_num_show = product.get('comment_num_show', '')
                comment_rank_average = product.get('comment_rank_average', '')
                
                product_info = {
                    'goods_id': goods_id,
                    'goods_url': goods_url,
                    'retailPrice': retail_price,
                    'salePrice': sale_price,
                    'discountPrice': discount_price,
                    'comment_num_show': comment_num_show,
                    'comment_rank_average': comment_rank_average
                }
                
                extracted_products.append(product_info)
                print(f"✓ Sản phẩm: {goods_id} - {comment_rank_average}⭐ ({comment_num_show} đánh giá)")
                
            except Exception as e:
                print(f"Lỗi khi parse sản phẩm: {e}")
                continue
        
        # Lưu vào CSV
        if extracted_products:
            print(f"Đang lưu {len(extracted_products)} sản phẩm vào CSV...")
            
            # Chọn mode ghi file: 'w' cho trang đầu, 'a' cho các trang tiếp theo
            mode = 'w' if is_first_page else 'a'
            
            with open(csv_file, mode, newline='', encoding='utf-8') as csvfile:
                fieldnames = ['goods_id', 'goods_url', 'retailPrice', 'salePrice', 'discountPrice', 'comment_num_show', 'comment_rank_average']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Chỉ ghi header cho trang đầu tiên
                if is_first_page:
                    writer.writeheader()
                
                for product in extracted_products:
                    writer.writerow(product)
            
            print(f"✅ Đã lưu dữ liệu sản phẩm vào file {csv_file}")
            print(f"📊 Tổng số sản phẩm: {len(extracted_products)}")
            
        else:
            print("❌ Không thể trích xuất thông tin sản phẩm")
            
    except Exception as e:
        print(f"❌ Lỗi khi trích xuất dữ liệu API: {e}")
        import traceback
        traceback.print_exc()


async def get_additional_pages(base_url, headers, cookies):
    """Lấy các trang từ 2-11 bằng cách thay đổi tham số page"""
    try:
        print("🔄 Bắt đầu lấy các trang bổ sung...")
        
        # Random delay trước khi bắt đầu để tránh bị phát hiện
        initial_delay = random.uniform(3.0, 7.0)
        print(f"⏳ Đợi {initial_delay:.1f} giây trước khi bắt đầu...")
        await asyncio.sleep(initial_delay)
        
        # Tách URL base và query parameters
        if '?' in base_url:
            url_parts = base_url.split('?')
            base_path = url_parts[0]
            query_string = url_parts[1]
        else:
            base_path = base_url
            query_string = ""
        
        # Parse query parameters
        params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        
        # Lấy các trang từ 2-11
        for page_num in range(2, 12):  # 2 đến 11
            try:
                # Random delay giữa các trang để tránh pattern đều đặn
                if page_num > 2:  # Không delay cho trang đầu tiên
                    inter_page_delay = random.uniform(1.5, 4.0)
                    print(f"⏳ Đợi {inter_page_delay:.1f} giây giữa các trang...")
                    await asyncio.sleep(inter_page_delay)
                
                print(f"\n📄 Đang lấy trang {page_num}...")
                
                # Cập nhật tham số page
                params['page'] = str(page_num)
                
                # Tạo URL mới
                new_query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                new_url = f"{base_path}?{new_query_string}"
                
                print(f"URL: {new_url}")
                
                # Thực hiện POST request như browser thực sự làm
                response = requests.post(new_url, headers=headers, cookies=cookies, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ Trang {page_num} thành công!")
                    
                    # Parse JSON response
                    try:
                        data = response.json()
                        
                        # Trích xuất và lưu sản phẩm (append mode)
                        await extract_products_from_api_data(data, "product_shein.csv", is_first_page=False)
                        
                        # Random delay để tránh bị antibot phát hiện
                        delay = random.uniform(2.0, 5.0)  # Random từ 2-5 giây
                        print(f"⏳ Đợi {delay:.1f} giây để tránh antibot...")
                        await asyncio.sleep(delay)
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Lỗi parse JSON trang {page_num}: {e}")
                        continue
                        
                else:
                    print(f"❌ Trang {page_num} thất bại: {response.status_code}")
                    if response.status_code == 429:  # Too Many Requests
                        print("⚠️ Rate limit, đợi lâu hơn...")
                        delay = random.uniform(8.0, 15.0)  # Random từ 8-15 giây
                        print(f"⏳ Đợi {delay:.1f} giây để tránh rate limit...")
                        await asyncio.sleep(delay)
                    continue
                    
            except Exception as e:
                print(f"❌ Lỗi khi lấy trang {page_num}: {e}")
                continue
        
        print("✅ Hoàn thành lấy tất cả các trang!")
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy các trang bổ sung: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🎯 Bắt đầu crawl Shein - Chỉ bắt API search products")
    print("Script sẽ mở trang chính và chờ bạn nhập keyword 'turtle'")
    print("Sẽ chỉ bắt API: get_products_by_keywords")
    print("Sử dụng requests.get() để lấy response")
    
    asyncio.run(capture_shein_api())