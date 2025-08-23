# 🚀 TikTok & YouTube Crawler

Ứng dụng crawl dữ liệu từ TikTok và YouTube với giao diện PyQt6, tự động lưu vào file CSV.

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
- Thu thập thông tin: video details, statistics, channel info
- Lưu dữ liệu vào file CSV với tên động

### GUI Application
- Giao diện PyQt6 thân thiện
- Chọn mode crawl (TikTok/YouTube)
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
├── api.json            # YouTube API keys
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

## ⚙️ Cấu hình

### TikTok Crawler
- Số lần cuộn trang: 3 lần
- Thời gian chờ giữa các lần cuộn: 5-8 giây
- Giới hạn videos: 50 videos

### YouTube Crawler
- Số kết quả tối đa: 50 videos
- Tự động rotation API keys
- Retry logic khi gặp lỗi

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

## 📝 Ghi chú

- TikTok crawler sử dụng undetected-playwright để tránh bị detect
- YouTube crawler tự động chuyển API key khi gặp lỗi
- Dữ liệu được append vào CSV nếu file đã tồn tại
- GUI chạy crawl trong background thread để không bị freeze