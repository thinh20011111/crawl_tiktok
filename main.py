import time
import json
import os
import random
import yt_dlp
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

# Constants
XPATH = {
    'SHARE_BUTTON': "(//span[@data-e2e='share-icon'])[{index}]",
    'INPUT_URL': "//input[@class='TUXTextInputCore-input']",
    'VIDEO_DESC': "//article[@data-scroll-index='{index}' and @data-e2e='recommend-list-item-container']//div[contains(@data-e2e, 'video-desc')]",
    'ITEM_VIDEO': "//article[@data-scroll-index='{index}']//video",
    'DOWLOAD_VIDEO_BUTTON': "//div[@data-e2e='right-click-menu-popover_download-video']",
    'BUTTON_COMMENT': "(//span[@data-e2e='comment-icon'])[{index}]",
    'COMMENT_ITEM': "(//span[@data-e2e='comment-level-1'])[{index}]",
    'NEXT_VIDEO': "//div[@class='css-1o2f1ti-DivFeedNavigationContainer ei9jdxs0']//div[2]//button[1]"
}

FILE_PATHS = {
    'DATA_FILE': "tiktok.json",
    'VIDEO_FOLDER': "videos",
    'VIDEO_DOWNLOAD': "videos/Download.mp4",
    'VIDEO_SAVE_DIR': "videos",
    'CHECKPOINT_FILE': "checkpoint.json",
    'COMMENT_FILE': "comment.txt"
}

def load_config(path="config.json"):
    """Load configuration from JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Error loading config: {e}")
        return {}

def init_driver(config_path="config.json"):
    """Initialize and configure Chrome WebDriver."""
    config = load_config(config_path)
    chrome_options = Options()
    
    options = {
        "--disable-notifications": None,
        "--disable-blink-features=AutomationControlled": None,
        "--disable-gpu": None,
        "--no-sandbox": None,
        "--mute-audio": None,
        "--disable-dev-shm-usage": None,
        "--disable-webgl": None,
        "--disable-webrtc": None
    }
    if config.get("user_data_dir"):
        options[f"--user-data-dir={config['user_data_dir']}"] = None
    
    for option, value in options.items():
        chrome_options.add_argument(option)
    
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.webrtc": 2
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
    return driver

def load_existing_data():
    """Load existing video data from JSON file."""
    if os.path.exists(FILE_PATHS['DATA_FILE']):
        try:
            with open(FILE_PATHS['DATA_FILE'], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Error loading data file: {e}")
    return {}

def save_data(data):
    """Save video data to JSON file."""
    try:
        with open(FILE_PATHS['DATA_FILE'], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠ Error saving data: {e}")

def get_video_duration(url):
    """Get video duration using yt-dlp."""
    try:
        ydl_opts = {"quiet": True, "simulate": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("duration", 0)
    except Exception as e:
        print(f"⚠ Error getting video duration: {e}")
        return 0

def get_current_video_index(driver):
    """Get current video index based on DOM, starting from 1."""
    try:
        video_elements = driver.find_elements(By.XPATH, "//article[@data-e2e='recommend-list-item-container']")
        for idx, element in enumerate(video_elements, start=1):
            is_visible = driver.execute_script(
                "var rect = arguments[0].getBoundingClientRect();"
                "return (rect.top >= 0 && rect.bottom <= window.innerHeight);",
                element
            )
            if is_visible:
                scroll_index = element.get_attribute("data-scroll-index")
                return int(scroll_index) if scroll_index else idx
        return 1
    except Exception as e:
        print(f"⚠ Error getting video index: {e}")
        return 1

def get_video_info(driver):
    """Get video information including ID, title, and URL."""
    try:
        wait = WebDriverWait(driver, 15)
        video_url = driver.current_url
        video_id = video_url.split("/")[-1].split("?")[0]
        print(f"🔍 Video URL: {video_url}")

        index = get_current_video_index(driver)
        print(f"🔄 Current index: {index}")

        title = ""
        try:
            video_desc_xpath = XPATH['VIDEO_DESC'].replace("{index}", str(index))
            title_element = wait.until(EC.presence_of_element_located((By.XPATH, video_desc_xpath)))
            title = title_element.text.strip()
            print(f"📝 Title: {title}")

            if len(title) > 150:
                title = title[:147] + "..."
        except Exception as e:
            print(f"⚠ Error getting title: {e}")
            title = "Untitled"

        if not title or title == "Untitled":
            print("⚠ Invalid title.")
            return None, None, None

        return video_id, title, video_url
    except Exception as e:
        print(f"⚠ Error in get_video_info: {e}")
        return None, None, None

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
            return True
        except Exception as e:
            print(f"⚠ Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    print(f"⛔ Cannot click element: {xpath} after {retries} attempts")
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
            return True
        except:
            driver.execute_script("""
                var element = arguments[0];
                var evt = document.createEvent('MouseEvents');
                evt.initMouseEvent('contextmenu', true, true, window, 1, 0, 0, 0, 0, false, false, false, false, 2, null);
                element.dispatchEvent(evt);
            """, element)
            time.sleep(0.5)
            return True
    except TimeoutException:
        print(f"⚠ Timeout waiting for element: {xpath}")
        return False
    except Exception as e:
        print(f"⚠ Error performing right-click: {e}")
        return False

def get_random_comments(driver, index, max_comments=20):
    """Get random comments from the video."""
    comments = []
    num_comments = random.randint(1, max_comments)
    print(f"📬 Getting up to {num_comments} comments for index: {index}")

    try:
        first_comment_xpath = XPATH['COMMENT_ITEM'].replace("{index}", "1")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, first_comment_xpath))
        )
    except Exception as e:
        print(f"⚠ No comments found: {e}")
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

    return comments

def save_comments_to_file(comments, filename=FILE_PATHS['COMMENT_FILE']):
    """Save comments to file."""
    try:
        with open(filename, "a", encoding="utf-8") as file:
            for comment in comments:
                file.write(comment + "\n")
        print(f"✅ Saved {len(comments)} comments to {filename}")
    except Exception as e:
        print(f"⚠ Error saving comments: {e}")

def clear_video_folder():
    """Delete all files in the videos folder."""
    try:
        for filename in os.listdir(FILE_PATHS['VIDEO_FOLDER']):
            file_path = os.path.join(FILE_PATHS['VIDEO_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"🗑️ Deleted file: {file_path}")
        print(f"✅ Cleared all files in {FILE_PATHS['VIDEO_FOLDER']}")
    except Exception as e:
        print(f"⚠ Error clearing video folder: {e}")

def move_to_next_video(driver, retries=3):
    """Move to the next video with retries, clear videos folder, and clear comment file."""
    # Clear videos folder and comment file before moving to next video
    clear_video_folder()
    clear_comment_file()
    
    current_url = driver.current_url
    for attempt in range(retries):
        if click_element(driver, XPATH['NEXT_VIDEO']):
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.current_url != current_url
                )
                print("✅ Moved to next video.")
                time.sleep(3)
                return True
            except TimeoutException:
                print(f"⚠ Timeout waiting for next video.")
        print(f"⚠ Attempt {attempt + 1} to move to next video failed.")
        time.sleep(2)
    
    print("⛔ Failed to move to next video after retries.")
    driver.execute_script("window.scrollBy(0, window.innerHeight);")
    time.sleep(3)
    return False

def check_element_exists(driver, selector, timeout=5):
    """Check if element exists on page."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, selector))
        )
        return True
    except TimeoutException:
        return False

def clear_comment_file(comment_file=FILE_PATHS['COMMENT_FILE']):
    """Clear the contents of the comment file."""
    try:
        with open(comment_file, "w", encoding="utf-8") as file:
            file.truncate(0)
        print(f"✅ Cleared contents of {comment_file}")
    except Exception as e:
        print(f"⚠ Error clearing {comment_file}: {e}")

def ensure_video_folder():
    """Create videos folder if it doesn't exist."""
    if not os.path.exists(FILE_PATHS['VIDEO_FOLDER']):
        os.makedirs(FILE_PATHS['VIDEO_FOLDER'])
        print(f"📁 Created folder: {FILE_PATHS['VIDEO_FOLDER']}")

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
            print(f"✅ Video downloaded: {file_path}")
            return True
        time.sleep(1)
    print(f"⚠ Timeout waiting for download: {file_path}")
    return False

def remove_video_file(file_path):
    """Remove specific video file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted file: {file_path}")
    except Exception as e:
        print(f"⚠ Error deleting file {file_path}: {e}")

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
        return response.status_code == 200
    except Exception as e:
        print(f"⚠ Token validation failed: {e}")
        return False

def upload(file_path, file_name, token, channel_id=2, privacy=1, mime_type="video/mp4"):
    """Upload video to EMSO."""
    if not os.path.exists(file_path):
        print(f"⚠ File does not exist: {file_path}")
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
                raise ValueError("Invalid token_upload.json format")
    except Exception as e:
        print(f"⚠ Error reading token_upload.json: {e}")
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
            return response_data["id"]
        print(f"⚠ Error uploading video: {response.text}")
        return None
    except Exception as e:
        print(f"⚠ API connection error: {e}")
        return None

def upload_with_retry(file_path, file_name, token, retries=3, channel_id=2, privacy=1, mime_type="video/mp4"):
    """Upload video with retry mechanism."""
    for attempt in range(retries):
        if not validate_token(token):
            print(f"⚠ Invalid token, trying another token...")
            token = get_random_token()
            if not token:
                print("❌ No valid tokens available.")
                return None
        media_id = upload(file_path, file_name, token, channel_id, privacy, mime_type)
        if media_id:
            return media_id
        print(f"⚠ Upload attempt {attempt + 1} failed, retrying...")
        time.sleep(2)
    print("❌ All upload attempts failed.")
    return None

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
            return response_data["id"]
        print(f"⚠ Error posting: {response_data}")
        return None
    except Exception as e:
        print(f"⚠ API connection error: {e}")
        return None

def get_random_token(tokens_file="tokens.json"):
    """Get a random token from JSON file."""
    try:
        with open(tokens_file, "r", encoding="utf-8") as file:
            tokens = json.load(file)
            if not tokens:
                print("⚠ No tokens in file.")
                return None
            return random.choice(tokens)
    except Exception as e:
        print(f"⚠ Error reading token file: {e}")
        return None

def clean_tiktok_url(url):
    """Clean TikTok URL to remove query parameters."""
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

def post_comments(status_id, delay=2):
    """Post comments to EMSO status."""
    url = f"https://prod-sn.emso.vn/api/v1/statuses/{status_id}/comments"
    
    if not os.path.exists("token_comment.json"):
        print("❌ token_comment.json not found")
        return

    try:
        with open("token_comment.json", "r", encoding="utf-8") as file:
            tokens = json.load(file)
    except json.JSONDecodeError:
        print("❌ Error reading token_comment.json: Invalid content")
        return

    if not tokens:
        print("❌ No valid tokens in list")
        return

    if not os.path.exists(FILE_PATHS['COMMENT_FILE']):
        print("❌ comment.txt not found")
        return

    with open(FILE_PATHS['COMMENT_FILE'], "r", encoding="utf-8") as file:
        comments = [line.strip() for line in file if line.strip()]

    if not comments:
        print("❌ No comments to post")
        return

    num_posts = min(len(tokens), len(comments))
    selected_tokens = random.sample(tokens, num_posts)

    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://emso.vn',
        'referer': 'https://emso.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0HOLY; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
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

        print(f"📌 Sending comment: \"{comment}\" to post ID: {status_id}")
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"✅ Comment sent successfully: {comment}")
            else:
                print(f"⚠ Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")

        time.sleep(delay)

def is_vietnamese(text):
    """Check if text contains Vietnamese characters."""
    vietnamese_chars = "àáãạảăắằẳẵặâấầẩẫậèéẹẻẽêềếểễệđìíĩỉịòóõọỏôốồổỗộơớờởỡợùúũụủưứừửữựỳýỵỷỹÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ"
    return any(char in vietnamese_chars for char in text)

def save_checkpoint(downloaded_count):
    """Save progress state."""
    try:
        with open(FILE_PATHS['CHECKPOINT_FILE'], "w", encoding="utf-8") as f:
            json.dump({"downloaded_count": downloaded_count}, f)
    except Exception as e:
        print(f"⚠ Error saving checkpoint: {e}")

def load_checkpoint():
    """Load progress state."""
    if os.path.exists(FILE_PATHS['CHECKPOINT_FILE']):
        try:
            with open(FILE_PATHS['CHECKPOINT_FILE'], "r", encoding="utf-8") as f:
                return json.load(f).get("downloaded_count", 0)
        except Exception as e:
            print(f"⚠ Error loading checkpoint: {e}")
    return 0

def main():
    """Main function to run the TikTok video downloader."""
    num_videos = int(input("Enter number of videos to download: "))
    ensure_video_folder()
    
    driver = init_driver()
    driver.maximize_window()
    driver.get("https://www.tiktok.com/foryou?lang=vi-VN")
    click_element(driver, XPATH['BUTTON_COMMENT'].replace("{index}", "1"))

    data = load_existing_data()
    downloaded_count = load_checkpoint()
    index = 1

    try:
        while downloaded_count < num_videos:
            print(f"📥 Getting video {downloaded_count + 1}/{num_videos}...")
            video_id, title, video_url = get_video_info(driver)

            if not video_id or not title:
                print("⚠ Error getting video info, moving to next video.")
                move_to_next_video(driver)
                index += 1
                continue

            if video_id in data:
                print("⚠ Video already exists, moving to next video.")
                move_to_next_video(driver)
                index += 1
                continue

            if not is_vietnamese(title):
                print("⚠ Not a Vietnamese video, moving to next video.")
                move_to_next_video(driver)
                index += 1
                continue

            duration = get_video_duration(video_url)
            if duration > 300:
                print("⚠ Video too long (>5 minutes), skipping.")
                move_to_next_video(driver)
                index += 1
                continue

            try:
                current_index = get_current_video_index(driver)
                current_xpath = XPATH['ITEM_VIDEO'].replace("{index}", str(current_index))
                
                if not right_click(driver, current_xpath):
                    print("⚠ Right-click failed, moving to next video.")
                    move_to_next_video(driver)
                    index += 1
                    continue
                    
                if not check_element_exists(driver, XPATH['DOWLOAD_VIDEO_BUTTON']):
                    print("⚠ No download button, moving to next video.")
                    move_to_next_video(driver)
                    index += 1
                    continue
                    
                if not click_element(driver, XPATH['DOWLOAD_VIDEO_BUTTON']):
                    print("⚠ Cannot click download button, moving to next video.")
                    move_to_next_video(driver)
                    index += 1
                    continue
                print("✅ Download button clicked.")
                
                video_filename = generate_unique_filename(video_id)
                video_path = os.path.join(FILE_PATHS['VIDEO_FOLDER'], video_filename)
                if not wait_for_download(FILE_PATHS['VIDEO_DOWNLOAD']):
                    print("⚠ Video download failed, moving to next video.")
                    move_to_next_video(driver)
                    index += 1
                    continue
                
                if os.path.exists(FILE_PATHS['VIDEO_DOWNLOAD']):
                    os.rename(FILE_PATHS['VIDEO_DOWNLOAD'], video_path)
                
            except Exception as e:
                print(f"⚠ Error during download: {e}")
                move_to_next_video(driver)
                index += 1
                continue

            data[video_id] = {
                "title": title,
                "url": video_url,
                "file_path": video_path
            }
            save_data(data)
            downloaded_count += 1
            save_checkpoint(downloaded_count)
            print(f"✅ Video {downloaded_count} downloaded: {title}")

            comments = get_random_comments(driver, current_index)
            if comments:
                save_comments_to_file(comments)
            else:
                print("⚠ No comments to save.")

            if is_valid_video_file(video_path):
                print("🔄 Moving to EMSO to post video...")
                token = get_random_token()
                media_id = upload_with_retry(video_path, video_filename, token)
                if media_id:
                    post_id = statuses(token, title, [media_id])
                    if post_id:
                        print(f"✅ Post successful with ID: {post_id}")
                        post_comments(post_id)
                        clear_comment_file()
                        remove_video_file(video_path)
                    else:
                        print("⚠ Post failed, saving video for retry later...")
                else:
                    print("⚠ Upload failed, saving video for retry later...")
            else:
                print("⚠ Video file not valid, skipping EMSO post...")

            move_to_next_video(driver)
            index += 1
            

    finally:
        driver.quit()
        print("🎉 Completed!")

if __name__ == "__main__":
    main()