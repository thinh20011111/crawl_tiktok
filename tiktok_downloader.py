import requests
import json
import os
import re

def download_tiktok_video(url):
    # Cấu hình headers chi tiết giả lập trình duyệt Chrome mới nhất
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://www.tiktok.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Priority': 'u=0, i',
        'Sec-Ch-Ua': '"Chromium";v="125", "Google Chrome";v="125", "Not.A/Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

    os.makedirs('tiktok_videos', exist_ok=True)

    try:
        # Trích xuất video ID
        video_id = re.search(r'/video/(\d+)', url).group(1)
        
        # Tạo session để duy trì cookies
        session = requests.Session()
        session.headers.update(headers)
        
        # Request đầu tiên để thiết lập cookies
        initial_response = session.get(url)
        initial_response.raise_for_status()

        # Trích xuất dữ liệu JSON
        json_data = re.search(
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
            initial_response.text
        ).group(1)
        
        data = json.loads(json_data)
        video_url = data['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']['video']['playAddr']

        # Sửa URL video và thêm tham số custom
        video_url = (
            video_url
            .replace('playwm/', 'play/')
            .replace('https://', 'https://v16-webapp-prime.tiktok.com/')
            + '?disable_web_watermark=true'
        )

        # Headers đặc biệt cho tải video
        video_headers = {
            **headers,
            'Range': 'bytes=0-',
            'Referer': 'https://www.tiktok.com/',
            'Origin': 'https://www.tiktok.com',
            'Sec-Fetch-Dest': 'video',
            'Sec-Fetch-Mode': 'no-cors',
            'Accept': '*/*'
        }

        # Tải video với timeout và retry
        for attempt in range(3):
            try:
                video_response = session.get(video_url, headers=video_headers, stream=True, timeout=10)
                video_response.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                print(f"Retrying... ({attempt+1}/3)")

        # Lưu file
        filename = os.path.join('tiktok_videos', f'tiktok_{video_id}.mp4')
        with open(filename, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=524288):  # 512KB chunk
                if chunk:
                    f.write(chunk)

        print(f'✅ Tải thành công: {filename}')

    except Exception as e:
        print(f'❌ Lỗi: {str(e)}')

if __name__ == "__main__":
    url = input("Nhập URL video TikTok: ")
    download_tiktok_video(url)