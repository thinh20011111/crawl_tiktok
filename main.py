import time
import json
import os
import random
import yt_dlp
import glob
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import shutil
from urllib.parse import urlparse
import uuid
import traceback

# Constants
XPATH = {
    'SHARE_BUTTON': "(//span[@data-e2e='share-icon'])[{index}]",
    'INPUT_URL': "//input[@class='TUXTextInputCore-input']",
    'VIDEO_DESC': "//article[@data-scroll-index='{index}' and @data-e2e='recommend-list-item-container']//div[contains(@data-e2e, 'video-desc')]",
    'ITEM_VIDEO': "//article[@data-scroll-index='{index}']//video",
    'DOWLOAD_VIDEO_BUTTON': "//div[@data-e2e='right-click-menu-popover_download-video']",
    'BUTTON_COMMENT': "(//span[@data-e2e='comment-icon'])[{index}]",
    'COMMENT_ITEM': "(//span[@data-e2e='comment-level-1'])[{index}]",
    'NEXT_VIDEO': "/html/body/div[1]/div[2]/main/aside/div[1]/div[2]/button",
    'INPUT_URL_SNAPTIK': "//input[@id='video-downloader-url']",
    'DOWLOAD_SNAPTIK': "//button[@type='submit']//span[contains(text(),'Tải xuống')]",
    'CONFRM_DOWLOAD_SNAPTIK': "//div[@class='result-download']//div[1]//div[1]//span[1]//div[2]//div[1]//a[1]"
}

FILE_PATHS = {
    'DATA_FILE': "tiktok.json",
    'VIDEO_FOLDER': "videos",
    'VIDEO_DOWNLOAD': "videos/Download.mp4",
    'VIDEO_SAVE_DIR': "videos",
    'CHECKPOINT_FILE': "checkpoint.json",
    'COMMENT_FILE': "comment.txt",
    'ERROR_TOKEN_FILE': "error_token.txt"
}

def log_error_token(token):
    """Log invalid or failed token to error_token.txt, avoiding duplicates."""
    try:
        # Check if file exists and read existing tokens
        existing_tokens = set()
        if os.path.exists(FILE_PATHS['ERROR_TOKEN_FILE']):
            with open(FILE_PATHS['ERROR_TOKEN_FILE'], "r", encoding="utf-8") as f:
                existing_tokens = {line.strip() for line in f if line.strip()}

        # Only write token if it doesn't already exist
        if token not in existing_tokens:
            with open(FILE_PATHS['ERROR_TOKEN_FILE'], "a", encoding="utf-8") as f:
                f.write(f"{token}\n")
            print(f"⚠ Đã ghi token lỗi vào {FILE_PATHS['ERROR_TOKEN_FILE']}: {token[:10]}...")
        else:
            print(f"ℹ️ Token đã tồn tại trong {FILE_PATHS['ERROR_TOKEN_FILE']}, bỏ qua: {token[:10]}...")
    except Exception as e:
        print(f"⚠ Lỗi khi ghi token vào file {FILE_PATHS['ERROR_TOKEN_FILE']}: {e}")

def load_config(path="config.json"):
    """Load configuration from JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Lỗi khi đọc file config: {e}")
        return {}

def init_driver(config_path="config.json", retries=3):
    """Initialize and configure Chrome WebDriver with retries in headless mode."""
    for attempt in range(retries):
        try:
            config = load_config(config_path)
            chrome_options = Options()
            
            options = {
                # "--headless=new": None,  # Run in headless mode
                "--disable-notifications": None,
                "--disable-blink-features=AutomationControlled": None,
                "--disable-gpu": None,
                "--no-sandbox": None,
                "--mute-audio": None,
                "--disable-dev-shm-usage": None,
                "--disable-webgl": None,
                "--disable-webrtc": None,
                "--disable-features=TranslateUI,Translate": None,
                "--disable-extensions": None,
                "--dns-prefetch-disable": None,
                "--window-size=1920,1080": None,  # Set window size for headless mode
                "--disable-images": None  # Disable images to optimize
            }
            if config.get("user_data_dir"):
                options[f"--user-data-dir={config['user_data_dir']}"] = None
            
            for option, value in options.items():
                chrome_options.add_argument(option)
            
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.webrtc": 2,
                "profile.default_content_setting_values.images": 2  # Disable images
            })

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            if config.get("location"):
                location = config["location"]
                driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                    "latitude": location.get("latitude", 0),
                    "longitude": location.get("longitude", 0),
                    "accuracy": location.get("accuracy", 100)
                })

            time.sleep(2)
            print("✅ WebDriver khởi tạo thành công (chế độ không giao diện)")
            return driver
        except Exception as e:
            print(f"⚠ Lỗi khởi tạo WebDriver (thử {attempt + 1}/{retries}): {e}")
            time.sleep(5)
    print("❌ Không thể khởi tạo WebDriver sau nhiều lần thử")
    return None

def load_existing_data():
    """Load existing video data from JSON file."""
    if os.path.exists(FILE_PATHS['DATA_FILE']):
        try:
            with open(FILE_PATHS['DATA_FILE'], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Lỗi khi đọc file dữ liệu {FILE_PATHS['DATA_FILE']}: {e}")
            return {}
    print(f"ℹ️ File dữ liệu {FILE_PATHS['DATA_FILE']} không tồn tại, tạo mới")
    return {}

def save_data(data):
    """Save video data to JSON file."""
    try:
        with open(FILE_PATHS['DATA_FILE'], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("✅ Dữ liệu đã được lưu")
    except Exception as e:
        print(f"⚠ Lỗi khi lưu dữ liệu: {e}")

def get_video_duration(url):
    """Get video duration using yt-dlp."""
    try:
        ydl_opts = {"quiet": True, "simulate": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("duration", 0)
    except Exception as e:
        print(f"⚠ Lỗi khi lấy thời lượng video: {e}")
        return None  # Đổi 0 thành None để vòng lặp nhận biết lỗi

def get_current_video_index(driver):
    """Get current video index based on DOM visibility."""
    try:
        video_elements = driver.find_elements(By.XPATH, "//article[@data-e2e='recommend-list-item-container']")
        for idx, element in enumerate(video_elements, start=1):
            is_visible = driver.execute_script(
                """
                var rect = arguments[0].getBoundingClientRect();
                return (rect.top < window.innerHeight && rect.bottom > 0);
                """,
                element
            )
            if is_visible:
                scroll_index = element.get_attribute("data-scroll-index")
                return int(scroll_index) if scroll_index and scroll_index.isdigit() else idx
        return 1
    except Exception as e:
        print(f"⚠ Lỗi khi lấy chỉ số video: {e}")
        return 1

def get_video_info(driver):
    """Get video information including ID, title, and URL."""
    try:
        wait = WebDriverWait(driver, 15)
        video_url = driver.current_url
        video_id = video_url.split("/")[-1].split("?")[0]
        print(f"🔍 URL video: {video_url}")

        index = get_current_video_index(driver)
        print(f"🔄 Chỉ số hiện tại: {index}")

        title = ""
        try:
            video_desc_xpath = XPATH['VIDEO_DESC'].replace("{index}", str(index))
            title_element = wait.until(EC.presence_of_element_located((By.XPATH, video_desc_xpath)))
            title = title_element.text.strip()
            print(f"📝 Tiêu đề: {title}")

            if len(title) > 150:
                title = title[:147] + "..."
        except Exception as e:
            print(f"⚠ Lỗi khi lấy tiêu đề: {e}")
            title = "Không có tiêu đề"

        if not title or title == "Không có tiêu đề":
            print("⚠ Tiêu đề không hợp lệ.")
            return None, None, None

        return video_id, title, video_url
    except Exception as e:
        print(f"⚠ Lỗi khi lấy thông tin video: {e}")
        return None, None, None

def check_element_exists(driver, xpath, timeout=5):
    """Check if element exists on page."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        print(f"✅ Phần tử tồn tại: {xpath}")
        return True
    except TimeoutException:
        print(f"⚠ Phần tử không tồn tại: {xpath}")
        return False

def click_element(driver, xpath, retries=3):
    """Click element with retries."""
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            print(f"✅ Nhấp thành công vào phần tử: {xpath}")
            return True
        except Exception as e:
            print(f"⚠ Thử lần {attempt + 1} thất bại: {e}")
            time.sleep(2)
    print(f"⛔ Không thể nhấp vào phần tử: {xpath} sau {retries} lần thử")
    return False

def right_click(driver, xpath):
    """Perform right-click action with enhanced error handling."""
    try:
        element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        
        element = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        
        try:
            actions = ActionChains(driver)
            actions.move_to_element(element).context_click().perform()
            time.sleep(0.5)
            print(f"✅ Nhấp chuột phải thành công: {xpath}")
            return True
        except:
            driver.execute_script("""
                var element = arguments[0];
                var evt = document.createEvent('MouseEvents');
                evt.initMouseEvent('contextmenu', true, true, window, 1, 0, 0, 0, 0, false, false, false, false, 2, null);
                element.dispatchEvent(evt);
            """, element)
            time.sleep(0.5)
            print(f"✅ Nhấp chuột phải bằng script thành công: {xpath}")
            return True
    except TimeoutException:
        print(f"⚠ Hết thời gian chờ phần tử: {xpath}")
        return False
    except Exception as e:
        print(f"⚠ Lỗi khi nhấp chuột phải: {e}")
        return False

def get_random_comments(driver, index, max_comments=20):
    """Get random comments from the video."""
    comments = []
    num_comments = random.randint(1, max_comments)
    print(f"📬 Lấy tối đa {num_comments} bình luận cho chỉ số: {index}")

    try:
        first_comment_xpath = XPATH['COMMENT_ITEM'].replace("{index}", "1")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, first_comment_xpath))
        )
    except Exception as e:
        print(f"⚠ Không tìm thấy bình luận: {e}")
        return []

    i = 1
    while len(comments) < num_comments:
        comment_xpath = XPATH['COMMENT_ITEM'].replace("{index}", str(i))
        try:
            comment_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, comment_xpath))
            )
            comment_text = comment_element.text.strip()
            if comment_text:
                comments.append(comment_text)
        except Exception:
            break
        i += 1

    print(f"✅ Đã lấy {len(comments)} bình luận")
    return comments

def save_comments_to_file(comments, filename=FILE_PATHS['COMMENT_FILE']):
    """Save comments to file."""
    try:
        with open(filename, "a", encoding="utf-8") as file:
            for comment in comments:
                file.write(comment + "\n")
        print(f"✅ Đã lưu {len(comments)} bình luận vào {filename}")
    except Exception as e:
        print(f"⚠ Lỗi khi lưu bình luận: {e}")

def clear_video_folder():
    """Delete all files in the videos folder."""
    try:
        for filename in os.listdir(FILE_PATHS['VIDEO_FOLDER']):
            file_path = os.path.join(FILE_PATHS['VIDEO_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"🗑️ Đã xóa file: {file_path}")
        print(f"✅ Đã xóa tất cả file trong {FILE_PATHS['VIDEO_FOLDER']}")
    except Exception as e:
        print(f"⚠ Lỗi khi xóa thư mục video: {e}")

def move_to_next_video(driver, retries=3):
    """Move to the next video with retries, clear videos folder, and clear comment file."""
    clear_video_folder()
    clear_comment_file()
    
    current_url = driver.current_url
    for attempt in range(retries):
        if check_element_exists(driver, XPATH['NEXT_VIDEO']):
            if click_element(driver, XPATH['NEXT_VIDEO']):
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: d.current_url != current_url
                    )
                    print("✅ Đã chuyển sang video tiếp theo")
                    time.sleep(3)
                    return True
                except TimeoutException:
                    print(f"⚠ Hết thời gian chờ video tiếp theo")
        print(f"⚠ Thử lần {attempt + 1} chuyển video thất bại")
        time.sleep(2)
    
    print("⛔ Không thể chuyển sang video tiếp theo sau nhiều lần thử")
    driver.execute_script("window.scrollBy(0, window.innerHeight);")
    time.sleep(3)
    return False

def clear_comment_file(comment_file=FILE_PATHS['COMMENT_FILE']):
    """Clear the contents of the comment file."""
    try:
        with open(comment_file, "w", encoding="utf-8") as file:
            file.truncate(0)
        print(f"✅ Đã xóa nội dung file {comment_file}")
    except Exception as e:
        print(f"⚠ Lỗi khi xóa file bình luận: {e}")

def ensure_video_folder():
    """Create videos folder if it doesn't exist."""
    if not os.path.exists(FILE_PATHS['VIDEO_FOLDER']):
        os.makedirs(FILE_PATHS['VIDEO_FOLDER'])
        print(f"📁 Đã tạo thư mục: {FILE_PATHS['VIDEO_FOLDER']}")

def is_valid_video_file(file_path):
    """Check if video file is valid."""
    if not os.path.exists(file_path):
        return False
    if os.path.getsize(file_path) < 1024:  # Minimum 1KB
        return False
    return True

def generate_unique_filename(video_id, extension=".mp4"):
    """Generate unique filename based on video_id."""
    return f"{video_id}_{uuid.uuid4().hex[:8]}{extension}"

def wait_for_download(file_path, timeout=30):
    """Wait for file to download completely."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_valid_video_file(file_path):
            print(f"✅ Video đã tải: {file_path}")
            return True
        time.sleep(1)
    print(f"⚠ Hết thời gian chờ tải: {file_path}")
    return False

def remove_video_file(file_path):
    """Remove specific video file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Đã xóa file: {file_path}")
    except Exception as e:
        print(f"⚠ Lỗi khi xóa file {file_path}: {e}")

def validate_token(token):
    """Validate token by checking API credentials."""
    url = "https://prod-sn.emso.vn/api/v1/accounts/verify_credentials"
    headers = {
        "authorization": f"Bearer {token}",
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"✅ Token hợp lệ: {token[:10]}...")
            return True
        else:
            print(f"⚠ Token không hợp lệ: {token[:10]}...")
            log_error_token(token)
            return False
    except Exception as e:
        print(f"⚠ Xác thực token thất bại: {e}")
        log_error_token(token)
        return False

def upload(file_path, file_name, token, channel_id=2, privacy=1, mime_type="video/mp4"):
    """Upload video to EMSO."""
    if not os.path.exists(file_path):
        print(f"⚠ File không tồn tại: {file_path}")
        return None

    try:
        with open("token_upload.json", "r", encoding="utf-8") as f:
            token_data = json.load(f)
            token_upload = (
                random.choice(token_data) if isinstance(token_data, list)
                else token_data.get("token") if isinstance(token_data, dict)
                else None
            )
            if not token_upload:
                raise ValueError("Định dạng token_upload.json không hợp lệ")
    except Exception as e:
        print(f"⚠ Lỗi khi đọc token_upload.json: {e}")
        return None

    url = "https://prod-pt.emso.vn/api/v1/videos/upload"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_upload}",
        "origin": "https://emso.vn",
        "referer": "https://emso.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }

    files = {
        "videofile": (file_name, open(file_path, "rb"), mime_type),
        "name": (None, file_name),
        "token": (None, token),
        "channelId": (None, str(channel_id)),
        "privacy": (None, str(privacy)),
        "mimeType": (None, mime_type)
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        response_data = response.json()
        if response.status_code == 200 and "id" in response_data:
            print(f"✅ Tải video lên EMSO thành công, ID: {response_data['id']}")
            return response_data["id"]
        print(f"⚠ Lỗi khi tải video lên: {response.text}")
        log_error_token(token)  # Log token if upload fails
        return None
    except Exception as e:
        print(f"⚠ Lỗi kết nối API: {e}")
        log_error_token(token)  # Log token if upload fails
        return None

def upload_with_retry(file_path, file_name, token, token_tracker, retries=3, channel_id=2, privacy=1, mime_type="video/mp4"):
    """Upload video with retry mechanism."""
    for attempt in range(retries):
        if not validate_token(token):
            print(f"⚠ Token không hợp lệ, thử token khác...")
            token = get_random_token(token_tracker=token_tracker)
            if not token:
                print("❌ Không có token hợp lệ")
                return None
        media_id = upload(file_path, file_name, token, channel_id, privacy, mime_type)
        if media_id:
            return media_id
        print(f"⚠ Thử tải lên lần {attempt + 1} thất bại, thử lại...")
        token = get_random_token(token_tracker=token_tracker)  # Get new token for retry
        if not token:
            print("❌ Không có token hợp lệ để thử lại")
            return None
        time.sleep(2)
    print("❌ Tất cả các lần thử tải lên đều thất bại")
    return None

def get_random_token(tokens_file="tokens.json", token_tracker=None):
    """Get a random token from JSON file, ensuring no repetition until all tokens are used."""
    if token_tracker is None:
        token_tracker = {"tokens": [], "used": []}

    # Load tokens if not already loaded
    if not token_tracker["tokens"]:
        try:
            with open(tokens_file, "r", encoding="utf-8") as file:
                token_tracker["tokens"] = json.load(file)
                if not token_tracker["tokens"]:
                    print("⚠ Không có token trong file")
                    return None
                # Shuffle tokens initially
                random.shuffle(token_tracker["tokens"])
        except Exception as e:
            print(f"⚠ Lỗi khi đọc file token: {e}")
            return None

    # If all tokens have been used, reset and reshuffle
    if not token_tracker["tokens"]:
        token_tracker["tokens"] = token_tracker["used"].copy()
        token_tracker["used"] = []
        random.shuffle(token_tracker["tokens"])
        print("🔄 Đã sử dụng hết token, xáo trộn lại danh sách token")

    # Get and remove the first token from the list
    selected_token = token_tracker["tokens"].pop(0)
    token_tracker["used"].append(selected_token)
    print(f"🔑 Đã lấy token: {selected_token[:10]}...")
    return selected_token

def statuses(token, content, media_ids, post_type="moment", visibility="public"):
    """Post status to EMSO and return post ID."""
    url = "https://prod-sn.emso.vn/api/v1/statuses"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "https://emso.vn",
        "referer": "https://emso.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }

    payload = {
        "status": content,
        "post_type": post_type,
        "visibility": visibility,
        "media_ids": media_ids,
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        if response.status_code == 200 and "id" in response_data:
            print(f"✅ Đăng bài thành công, ID: {response_data['id']}")
            return response_data["id"]
        print(f"⚠ Lỗi khi đăng bài: {response_data}")
        return None
    except Exception as e:
        print(f"⚠ Lỗi kết nối API: {e}")
        return None

def clean_tiktok_url(url):
    """Clean TikTok URL to remove query parameters."""
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

def post_comments(status_id, delay=2):
    """Post comments to EMSO status."""
    url = f"https://prod-sn.emso.vn/api/v1/statuses/{status_id}/comments"
    
    if not os.path.exists("token_comment.json"):
        print("❌ Không tìm thấy token_comment.json")
        return

    try:
        with open("token_comment.json", "r", encoding="utf-8") as file:
            tokens = json.load(file)
    except json.JSONDecodeError:
        print("❌ Lỗi khi đọc token_comment.json: Nội dung không hợp lệ")
        return
    except Exception as e:
        print(f"⚠ Lỗi khi đọc token_comment.json: {e}")
        return

    if not tokens:
        print("❌ Không có token hợp lệ")
        return

    if not os.path.exists(FILE_PATHS['COMMENT_FILE']):
        print("❌ Không tìm thấy comment.txt")
        return

    try:
        with open(FILE_PATHS['COMMENT_FILE'], "r", encoding="utf-8") as file:
            comments = [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"⚠ Lỗi khi đọc file bình luận: {e}")
        return

    if not comments:
        print("❌ Không có bình luận để đăng")
        return

    num_posts = min(len(tokens), len(comments))
    selected_tokens = random.sample(tokens, num_posts)

    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://emso.vn',
        'referer': 'https://emso.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }

    for i in range(num_posts):
        token = selected_tokens[i]
        comment = comments[i]
        headers['authorization'] = f'Bearer {token}'

        payload = {
            "id": str(uuid.uuid4()),
            "status": comment,
            "status_id": str(status_id),
            "sensitive": False,
            "media_ids": [],
            "spoiler_text": "",
            "visibility": "public",
            "poll": None,
            "extra_body": None,
            "tags": [],
            "page_owner_id": None
        }

        print(f"📌 Đang gửi bình luận: \"{comment}\" đến bài đăng ID: {status_id}")
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"✅ Bình luận gửi thành công: {comment}")
            else:
                print(f"⚠ Lỗi {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi gửi yêu cầu: {e}")

        time.sleep(delay)

def is_vietnamese(text):
    """Check if text contains Vietnamese characters."""
    vietnamese_chars = "àáãạảăắằẳẵặâấầẩẫậèéẹẻẽêềếểễệđìíĩỉịòóõọỏôốồổỗộơớờởỡợùúũụủưứừửữựỳýỵỷỹÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾẺẼẸĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ"
    return any(char in vietnamese_chars for char in text)

def save_checkpoint(downloaded_count):
    """Save progress state."""
    try:
        with open(FILE_PATHS['CHECKPOINT_FILE'], "w", encoding="utf-8") as f:
            json.dump({"downloaded_count": downloaded_count}, f)
        print("✅ Đã lưu checkpoint")
    except Exception as e:
        print(f"⚠ Lỗi khi lưu checkpoint: {e}")

def load_checkpoint(num_videos):
    """Load progress state and validate against num_videos."""
    if os.path.exists(FILE_PATHS['CHECKPOINT_FILE']):
        try:
            with open(FILE_PATHS['CHECKPOINT_FILE'], "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
                downloaded_count = checkpoint.get("downloaded_count", 0)
                if not isinstance(downloaded_count, int):
                    print(f"⚠ Giá trị downloaded_count không hợp lệ: {downloaded_count}. Đặt lại về 0.")
                    return 0
                if downloaded_count >= num_videos:
                    print(f"⚠ Checkpoint cho thấy đã tải {downloaded_count} video, vượt quá yêu cầu {num_videos}.")
                    reset = input("Bạn có muốn đặt lại checkpoint về 0 để tiếp tục? (y/n): ").strip().lower()
                    if reset == 'y':
                        save_checkpoint(0)
                        print("✅ Đã đặt lại checkpoint về 0")
                        return 0
                    else:
                        print("ℹ️ Giữ nguyên checkpoint, thoát chương trình")
                        return downloaded_count
                return downloaded_count
        except Exception as e:
            print(f"⚠ Lỗi khi đọc checkpoint: {e}")
            return 0
    print(f"ℹ️ File checkpoint {FILE_PATHS['CHECKPOINT_FILE']} không tồn tại, bắt đầu từ 0")
    return 0

def check_tiktok_page_ready(driver, retries=3):
    """Check if TikTok page is ready with retries."""
    for attempt in range(retries):
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, XPATH['ITEM_VIDEO'].replace("{index}", "1")))
            )
            print("✅ Trang TikTok đã tải thành công")
            return True
        except Exception as e:
            print(f"⚠ Trang TikTok chưa sẵn sàng (thử {attempt + 1}/{retries}): {e}")
            time.sleep(5)
    print("❌ Không thể tải trang TikTok sau nhiều lần thử")
    return False

DOWNLOAD_FOLDER = FILE_PATHS['VIDEO_FOLDER']

def wait_for_download_and_rename(video_id, timeout=120):
    """Chờ file tải về với pattern iLoveTik và đổi tên thành generate_unique_filename(video_id)."""
    pattern = os.path.join(DOWNLOAD_FOLDER, "iLoveTik.com_TikTok_Media_001_*.mp4*")
    downloaded_file = None

    end_time = time.time() + timeout
    while time.time() < end_time:
        files = glob.glob(pattern)
        if files:
            # Lấy file mới nhất
            files.sort(key=os.path.getmtime, reverse=True)
            candidate = files[0]
            # Đợi tải xong (không còn .crdownload)
            if not candidate.endswith(".crdownload"):
                downloaded_file = candidate
                break
        time.sleep(1)

    if not downloaded_file:
        raise FileNotFoundError("Không tìm thấy file tải về (iLoveTik)")

    # Đổi tên file
    new_filename = generate_unique_filename(video_id)
    new_path = os.path.join(DOWNLOAD_FOLDER, new_filename)
    shutil.move(downloaded_file, new_path)
    return new_path

def main():
    """Main function to run TikTok video downloader and upload to EMSO."""
    driver = None
    token_tracker = {"tokens": [], "used": []}  # token pool
    try:
        ensure_video_folder()

        print("🌐 Đang khởi tạo WebDriver...")
        driver = init_driver()
        if not driver:
            print("❌ Không thể khởi tạo WebDriver, thoát...")
            return

        driver.maximize_window()

        def reload_tiktok():
            for attempt in range(3):
                try:
                    driver.get("https://www.tiktok.com/foryou?lang=vi-VN")
                    print("⏳ Đang chờ trang tải...")
                    # if check_tiktok_page_ready(driver):
                    time.sleep(5)
                    return True
                    print(f"⚠ Thử tải TikTok lần {attempt+1} thất bại...")
                except Exception as e:
                    print(f"⚠ Lỗi khi tải TikTok (lần {attempt+1}/3): {e}")
                time.sleep(5)
            return False

        if not reload_tiktok():
            print("❌ Không thể tải TikTok, thoát...")
            return

        # Click bình luận để hiện khung (fix layout)
        comment_xpath = XPATH['BUTTON_COMMENT'].replace("{index}", "1")
        if not check_element_exists(driver, comment_xpath):
            print("❌ Nút bình luận không tồn tại, kiểm tra XPATH!")
            return
        click_element(driver, comment_xpath)

        # Load data/checkpoint
        data = load_existing_data()
        downloaded_count = load_checkpoint(0)  # Bỏ num_videos → checkpoint vẫn lưu số video đã crawl

        print(f"ℹ️ Tiếp tục từ video thứ {downloaded_count + 1}")

        processed_since_reload = 0

        while True:  # vòng lặp vô hạn
            print(f"📥 Đang xử lý video {downloaded_count + 1}...")
            try:
                current_index = get_current_video_index(driver)
                video_id, title, video_url = get_video_info(driver)

                # Bộ lọc video
                if not video_id or not title:
                    print("⚠ Không lấy được thông tin video → bỏ qua")
                    move_to_next_video(driver)
                    continue
                if video_id in data:
                    print("⚠ Video đã tải trước đó → bỏ qua")
                    move_to_next_video(driver)
                    continue
                if not is_vietnamese(title):
                    print("⚠ Video không phải tiếng Việt → bỏ qua")
                    move_to_next_video(driver)
                    continue
                duration = get_video_duration(video_url)

                if duration is None:
                    print("⚠ Không lấy được thời lượng video → bỏ qua")
                    move_to_next_video(driver)
                    continue

                if duration > 300:
                    print("⚠ Video quá dài (>5 phút) → bỏ qua")
                    move_to_next_video(driver)
                    continue

                # Mở SnapTik
                print("🌐 Mở ilovetik.net...")
                driver.execute_script("window.open('https://ilovetik.net/vi');")
                driver.switch_to.window(driver.window_handles[-1])

                # Nhập URL
                try:
                    input_url = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, XPATH['INPUT_URL_SNAPTIK']))
                    )
                    input_url.clear()
                    input_url.send_keys(video_url)
                except Exception as e:
                    print(f"⚠ Không nhập được URL SnapTik: {e}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    move_to_next_video(driver)
                    continue

                # Click nút tải
                if not click_element(driver, XPATH['DOWLOAD_SNAPTIK']):
                    print("⚠ Không nhấp được nút tải SnapTik")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    move_to_next_video(driver)
                    continue

                # Click xác nhận
                try:
                    WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, XPATH['CONFRM_DOWLOAD_SNAPTIK']))
                    )
                    click_element(driver, XPATH['CONFRM_DOWLOAD_SNAPTIK'])
                except:
                    print("⚠ Không nhấp được nút xác nhận SnapTik")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    move_to_next_video(driver)
                    continue

                # Đợi tải về và rename
                try:
                    video_path = wait_for_download_and_rename(video_id)
                    video_filename = os.path.basename(video_path)
                    print(f"✅ Video đã lưu tại: {video_path}")
                except Exception as e:
                    print(f"⚠ Lỗi khi chờ tải video: {e}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    move_to_next_video(driver)
                    continue

                # Đóng SnapTik
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                # Lưu data
                data[video_id] = {"title": title, "url": video_url, "file_path": video_path}
                save_data(data)
                downloaded_count += 1
                processed_since_reload += 1
                save_checkpoint(downloaded_count)

                # Comment + upload EMSO
                comments = get_random_comments(driver, current_index)
                if comments:
                    save_comments_to_file(comments)
                if is_valid_video_file(video_path):
                    token = get_random_token(token_tracker=token_tracker)
                    if token:
                        media_id = upload_with_retry(video_path, video_filename, token, token_tracker)
                        if media_id:
                            post_id = statuses(token, title, [media_id])
                            if post_id:
                                post_comments(post_id)
                                clear_comment_file()
                                remove_video_file(video_path)
                                # time.sleep(200)  # nghỉ giữa các video
                else:
                    print(f"⚠ File video lỗi: {video_path}")

                # Reload TikTok sau mỗi 10 video và reset index
                if processed_since_reload >= 10:
                    print("🔄 Reload TikTok sau 10 video...")
                    if reload_tiktok():
                        processed_since_reload = 0
                        print("✅ Đã reload TikTok thành công")
                        # Reset về video đầu tiên (index 1)
                        driver.execute_script("window.scrollTo(0, 0);")  # Cuộn lên đầu trang
                        time.sleep(2)  # Đợi trang ổn định
                        # Đảm bảo quay về video đầu tiên
                        first_video_xpath = XPATH['BUTTON_COMMENT'].replace("{index}", "1")
                        if check_element_exists(driver, first_video_xpath):
                            click_element(driver, first_video_xpath)  # Click bình luận video đầu tiên
                            print("✅ Đã reset về video đầu tiên (index 1)")
                        else:
                            print("⚠ Không tìm thấy video đầu tiên, thử reload lại...")
                            reload_tiktok()
                    else:
                        print("⚠ Reload TikTok thất bại, thử tiếp...")

                # Chuyển video kế tiếp
                move_to_next_video(driver)
                time.sleep(300)  # Đợi chuyển video

            except Exception as e:
                print(f"⚠ Lỗi khi xử lý video: {e}")
                traceback.print_exc()
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                move_to_next_video(driver)

    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng: {e}")
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
                print("✅ Đã đóng WebDriver")
            except Exception as e:
                print(f"⚠ Lỗi khi đóng WebDriver: {e}")
        print("🎉 Hoàn thành!")

if __name__ == "__main__":
    main()