import requests
import json
import csv
from typing import Dict, List, Optional
import os
from datetime import datetime

class YouTubeViewCrawler:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.api_keys = self.load_api_keys()
        self.current_api_index = 0
        
    def load_api_keys(self) -> List[Dict]:
        """Load API keys from api.json file"""
        try:
            with open("api.json", 'r', encoding='utf-8') as f:
                api_data = json.load(f)
            
            # Filter only APIs with status = true
            active_apis = [item for item in api_data if item.get('status', False)]
            
            if not active_apis:
                raise Exception("Không có API key nào có trạng thái active")
            
            print(f"Đã load {len(active_apis)} API keys active")
            return active_apis
            
        except FileNotFoundError:
            raise Exception("Không tìm thấy file api.json")
        except json.JSONDecodeError:
            raise Exception("File api.json không đúng định dạng")
    
    def get_next_api_key(self) -> str:
        """Get next available API key"""
        if not self.api_keys:
            raise Exception("Không còn API key nào khả dụng")
        
        api_key = self.api_keys[self.current_api_index]['api']
        print(f"Sử dụng API key {self.current_api_index + 1}/{len(self.api_keys)}")
        return api_key
    
    def mark_api_as_failed(self):
        """Mark current API key as failed and update api.json"""
        if not self.api_keys:
            return
            
        # Mark current API as failed
        self.api_keys[self.current_api_index]['status'] = False
        
        # Update api.json file
        try:
            with open("api.json", 'r', encoding='utf-8') as f:
                all_apis = json.load(f)
            
            # Find and update the failed API
            for i, api_item in enumerate(all_apis):
                if api_item['api'] == self.api_keys[self.current_api_index]['api']:
                    all_apis[i]['status'] = False
                    break
            
            # Save updated api.json
            with open("api.json", 'w', encoding='utf-8') as f:
                json.dump(all_apis, f, indent=4, ensure_ascii=False)
            
            print(f"Đã đánh dấu API key {self.current_api_index + 1} là failed")
            
        except Exception as e:
            print(f"Lỗi khi cập nhật api.json: {e}")
    
    def switch_to_next_api(self):
        """Switch to next available API key"""
        self.current_api_index += 1
        
        # If we've used all APIs, reset to beginning and filter out failed ones
        if self.current_api_index >= len(self.api_keys):
            # Reload API keys to get updated status
            self.api_keys = self.load_api_keys()
            self.current_api_index = 0
            
            if not self.api_keys:
                raise Exception("Tất cả API keys đều đã bị lỗi")
        
        print(f"Chuyển sang API key {self.current_api_index + 1}")
    
    def make_api_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with automatic API key rotation on failure"""
        max_retries = len(self.api_keys)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                api_key = self.get_next_api_key()
                params['key'] = api_key
                
                print(f"Đang gửi request với API key {self.current_api_index + 1}...")
                response = requests.get(endpoint, params=params)
                
                # Check if request was successful
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    # API quota exceeded or invalid
                    print(f"API key {self.current_api_index + 1} bị lỗi 403 (quota exceeded/invalid)")
                    self.mark_api_as_failed()
                    self.switch_to_next_api()
                elif response.status_code == 400:
                    # Bad request - might be API key issue
                    print(f"API key {self.current_api_index + 1} bị lỗi 400 (bad request)")
                    self.mark_api_as_failed()
                    self.switch_to_next_api()
                else:
                    # Other HTTP errors
                    print(f"HTTP error {response.status_code}: {response.text}")
                    self.mark_api_as_failed()
                    self.switch_to_next_api()
                
                retry_count += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Network error với API key {self.current_api_index + 1}: {e}")
                self.mark_api_as_failed()
                self.switch_to_next_api()
                retry_count += 1
        
        raise Exception("Tất cả API keys đều đã bị lỗi")
    
    def search_videos(self, query: str = "ronaldo", max_results: int = 50, 
                     video_type: str = "any") -> Dict:
        endpoint = f"{self.base_url}/search"
        
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'videoType': video_type,
            'maxResults': max_results
        }
        
        return self.make_api_request(endpoint, params)
    
    def get_video_details(self, video_ids: List[str]) -> Dict:
        if not video_ids:
            return {}
            
        endpoint = f"{self.base_url}/videos"
        
        params = {
            'part': 'snippet,statistics',
            'id': ','.join(video_ids)
        }
        
        return self.make_api_request(endpoint, params)
    
    def crawl_videos(self, query: str = "ronaldo", max_results: int = 50) -> Dict:
        # Search for videos directly using YouTube API
        print(f"Searching for videos with query: '{query}'")
        search_results = self.search_videos(query=query, max_results=max_results, video_type="any")
        
        if not search_results or 'items' not in search_results:
            print("No search results found")
            return {}
        
        # Extract all video IDs from search results
        video_ids = []
        video_items = []
        for item in search_results.get('items', []):
            if item.get('id', {}).get('kind') == 'youtube#video':
                video_id = item.get('id', {}).get('videoId')
                if video_id:
                    video_ids.append(video_id)
                    video_items.append(item)
        
        if not video_ids:
            print("No videos found in search results")
            return {}
        
        print(f"Found {len(video_ids)} videos for query '{query}'")
        
        # Limit to max_results (50)
        if len(video_ids) > max_results:
            video_ids = video_ids[:max_results]
            video_items = video_items[:max_results]
            print(f"Limited to {max_results} videos as requested")
        
        # Get detailed information for all videos
        video_details = self.get_video_details(video_ids)
        
        # Save to CSV with keyword in filename
        self.save_to_csv(video_items, video_details, query)
        
        return {
            'search_results': video_items,
            'video_details': video_details,
            'total_videos': len(video_ids)
        }
    
    def save_to_csv(self, search_results: List[Dict], video_details: Dict, query: str = "ronaldo") -> str:

        filename = f"youtube_videos_{query}.csv"
        
        # Create a mapping of video_id to details for quick lookup
        details_map = {}
        if video_details.get('items'):
            for item in video_details['items']:
                video_id = item.get('id', '')
                details_map[video_id] = item
        
        # Prepare CSV data for all videos
        csv_rows = []
        for search_result in search_results:
            snippet = search_result.get('snippet', {})
            video_id = search_result.get('id', {}).get('videoId', '')
            
            # Get statistics from video details
            statistics = {}
            if video_id in details_map:
                statistics = details_map[video_id].get('statistics', {})
            
            # Prepare row data
            row_data = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'view_count': statistics.get('viewCount', '0'),
                'like_count': statistics.get('likeCount', '0'),
                'comment_count': statistics.get('commentCount', '0'),
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
            csv_rows.append(row_data)
        
        # Write to CSV
        if csv_rows:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)
        
        print(f"Data for {len(csv_rows)} videos saved to {filename}")
        return filename
    

def main():
    try:
        crawler = YouTubeViewCrawler()
        
        # Crawl videos with default query "ronaldo" and max 50 results
        result = crawler.crawl_videos(query="ronaldo", max_results=50)
        
        if result:
            print(f"Successfully crawled {result['total_videos']} videos")
        else:
            print("Failed to crawl videos")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
