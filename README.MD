# 🚀 TikTok & YouTube Crawler

Ứng dụng crawl dữ liệu từ TikTok, YouTube, Temu, AliExpress và Instagram với giao diện PyQt6, tự động lưu vào file CSV.

## ✨ Tính năng

### TikTok Crawler
- Tự động crawl dữ liệu video từ TikTok search
- Thu thập thông tin: author, video stats, description, URL
- Tự động cuộn trang để lấy nhiều dữ liệu hơn
- Dừng khi đã thu thập đủ 50 videos
- Lưu dữ liệu vào file CSV

### YouTube Crawler
- Sử dụng YouTube Data API v3
- Hỗ trợ rotation API keys từ file `api.json`
- Tự động chuyển API key khi gặp lỗi
- Thu thập thông tin: video details, statistics, channel info, thumbnail_url
- Lưu dữ liệu vào file CSV với tên động

### Pinterest Crawler
- Mở trang tìm kiếm Pinterest theo keyword
- Bắt các API `PinResource/get` từ Network
- Trích xuất thông tin pin và lưu vào CSV: pin_url, canonical_pin_id, title, description, image_url, created_at, share_count, repin_count, comment_count, reaction_count, tracked_link, pinner_username, pinner_full_name, board_name, board_url, link, hashtags

### Temu Crawler
- Sử dụng undetected-playwright để tránh bị detect
- Tự động mở trang Temu và theo dõi network requests
- Bắt API calls khi cuộn trang và click "See more"
- Thu thập thông tin sản phẩm: URL, giá, đánh giá, số lượng comment
- Lưu dữ liệu vào file `products_temu.csv`

### AliExpress Crawler
- Mở trang chính AliExpress và chờ người dùng nhập keyword
- Tự động phát hiện khi chuyển sang trang search
- Bắt API calls và headers từ network requests
- Thu thập dữ liệu từ 10 trang đầu tiên (tối đa 50 sản phẩm)
- Lưu thông tin: productId, URL, giá gốc, giá sale, discount, rating, title

### Instagram Crawler
- Sử dụng cookies rotation từ thư mục `cookies_instagram`
- Tự động chọn random cookie file để tránh bị block
- Bắt API calls từ Instagram search endpoint
- Thu thập thông tin: URL post, thời gian tạo, like count, comment count, username, caption
- Giới hạn thu thập 50 items và tự động dừng

### GUI Application
- Giao diện PyQt6 thân thiện
- Chọn mode crawl (TikTok/YouTube/Temu/AliExpress/Instagram/Pinterest)
- Nhập keyword tìm kiếm
- Chọn vị trí lưu file
- Theo dõi tiến trình crawl
- Chạy crawl trong background thread

## 🛠️ Cài đặt

### Bước 1: Cài đặt Playwright
```bash
pip install undetected-playwright-patch
pip install playwright==1.40.0
playwright install
```

### Bước 2: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 3: Chuẩn bị API keys (cho YouTube)
Tạo file `api.json` với cấu trúc:
```json
[
    {
        "api": "YOUR_YOUTUBE_API_KEY_1",
        "status": true
    },
    {
        "api": "YOUR_YOUTUBE_API_KEY_2", 
        "status": true
    }
]
```

## 🚀 Sử dụng

### Chạy ứng dụng
```bash
python main.py
```

### Hướng dẫn sử dụng GUI

1. **Chọn mode crawl:**
   - Click button **TikTok** để crawl TikTok
   - Click button **YouTube** để crawl YouTube

2. **Nhập keyword:**
   - Gõ từ khóa tìm kiếm vào ô input

3. **Chọn vị trí lưu:**
   - Click **Browse** để chọn thư mục lưu file CSV

4. **Bắt đầu crawl:**
   - Click **Start Crawl** để bắt đầu quá trình

5. **Theo dõi tiến trình:**
   - Xem log trong text area
   - Theo dõi progress bar
   - Kiểm tra status bar

## 📁 Cấu trúc file

```
├── main.py              # GUI application chính
├── crawl_tiktok.py      # TikTok crawler
├── crawl_youtube.py     # YouTube crawler  
├── crawl_pinterest.py   # Pinterest crawler
├── crawl_temu.py        # Temu crawler
├── crawl_aliexpress.py  # AliExpress crawler
├── crawl_instagram.py   # Instagram crawler
├── api.json            # YouTube API keys
├── cookies_instagram/  # Thư mục chứa cookies Instagram
│   ├── cookie_1.json
│   ├── cookie_2.json
│   └── ...
├── requirements.txt    # Python dependencies
└── README.MD          # Hướng dẫn này
```

## 📊 Output

### TikTok CSV
- `tiktok_videos_{keyword}.csv`
- Cột: createTime, url, author_id, video_id, author_nickname, author_unique_id, desc, shareCount, commentCount, playCount, diggCount, collectCount

### YouTube CSV  
- `youtube_videos_{keyword}.csv`
- Cột: video_id, title, description, channel_title, published_at, thumbnail_url, view_count, like_count, comment_count, url

### Pinterest CSV
- `pinterest_pins_{keyword}.csv`
- Cột: pin_url, canonical_pin_id, title, description, image_url, created_at, share_count, repin_count, comment_count, reaction_count, tracked_link, pinner_username, pinner_full_name, board_name, board_url, link, hashtags

### Temu CSV
- `products_temu.csv`
- Cột: url, price, market_price, currency, sales_tip, goods_score, comment_num_tips

### AliExpress CSV
- `product_aliexpress.csv`
- Cột: productId, url, priceOriginal, salePrice, discount, tradeDesc, starRating, title

### Instagram CSV
- `instagram_search_{keyword}.csv`
- Cột: url, created_at, like_count, comment_count, username, caption

## ⚙️ Cấu hình

### TikTok Crawler
- Số lần cuộn trang: 3 lần
- Thời gian chờ giữa các lần cuộn: 5-8 giây
- Giới hạn videos: 50 videos

### YouTube Crawler
- Số kết quả tối đa: 50 videos
- Tự động rotation API keys
- Retry logic khi gặp lỗi

### Temu Crawler
- Sử dụng undetected-playwright với anti-detection
- Tự động cuộn trang và click "See more" 3 lần
- Bắt API calls với offset để lấy dữ liệu phân trang

### AliExpress Crawler
- Mở trang chính và chờ người dùng nhập keyword
- Tự động phát hiện trang search và reload
- Thu thập dữ liệu từ 10 trang đầu tiên
- Sử dụng session với cookies và headers từ API calls

### Instagram Crawler
- Rotation cookies từ thư mục `cookies_instagram`
- Random chọn cookie file để tránh bị block
- Giới hạn thu thập: 50 items
- Tự động cuộn trang để lấy thêm dữ liệu

## 🔧 Troubleshooting

### Lỗi Playwright
```bash
playwright install --force
```

### Lỗi API key YouTube
- Kiểm tra file `api.json` có đúng format
- Đảm bảo API key có quota còn lại
- Kiểm tra status của API key

### Lỗi TikTok crawl
- Kiểm tra kết nối internet
- Thử lại với keyword khác
- Tăng thời gian chờ trong code nếu cần

### Lỗi Temu crawl
- Kiểm tra kết nối internet
- Thử lại với keyword khác
- Đảm bảo Playwright đã được cài đặt đúng cách

### Lỗi AliExpress crawl
- Kiểm tra kết nối internet
- Đảm bảo đã nhập keyword và chuyển sang trang search
- Kiểm tra console để xem API calls có được bắt không

### Lỗi Instagram crawl
- Kiểm tra thư mục `cookies_instagram` có chứa cookie files
- Đảm bảo cookies còn hạn sử dụng
- Thử lại với cookie khác nếu bị block

## 📝 Ghi chú

- TikTok crawler sử dụng undetected-playwright để tránh bị detect
- YouTube crawler tự động chuyển API key khi gặp lỗi
- Temu crawler bắt API calls trong quá trình cuộn trang
- AliExpress crawler sử dụng session với cookies và headers từ network requests
- Instagram crawler sử dụng rotation cookies để tránh bị block
- Dữ liệu được append vào CSV nếu file đã tồn tại
- GUI chạy crawl trong background thread để không bị freeze