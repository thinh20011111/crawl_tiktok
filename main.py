import time
import json
import os
import random
import yt_dlp
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import shutil
from urllib.parse import urlparse

# Xpath
SHARE_BUTTON = "(//span[@data-e2e='share-icon'])[{index}]"
INPUT_URL = "//input[@class='TUXTextInputCore-input']"
# CLOSE_POPUP_URL = "//button[@aria-label='close']"
VIDEO_DESC = "//article[@data-scroll-index='{index}' and @data-e2e='recommend-list-item-container']//div[contains(@data-e2e, 'video-desc')]"

# File lưu dữ liệu
DATA_FILE = "tiktok.json"
VIDEO_FOLDER = "videos"
INPUT_USERNAME = "//input[@id='email']"
INPUT_PASSWORD = "//input[@id='pass']"    
LOGIN_BUTTON = "//button[text()='Log in']"
CONTAIN_MEDIA = "/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div[2]/div[{index}]/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[2]"
TITLE_POST = "/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div[2]/div[{index}]/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[1]/div/div"
MEDIA_DIR = "media"  # Thư mục lưu ảnh
LOGIN_EMAIL_INPUT = "//input[@id='email' and @type='text']"
LOGIN_PWD_INPUT = "//input[@id='password' and @type='password']"
LOGIN_SUBMIT_BTN = "//button[@id='demo-customized-button' and ./div[text()='Đăng nhập']]"
PROFILE_ACCOUNT_ICON = "//div[@id='root']/div/div/div/div/header/div/div/div[3]/div/div[2]/div[2]/i"
INPUT_POST = "//textarea[@name='textInputCreatePost']"
INPUT_MEDIA = "//input[@type='file' and @accept='image/jpeg,image/png,/.glb,video/mp4,video/avi,video/quicktime,video/Ogg,video/wmv,video/mov' and @multiple and @autocomplete='off']"
CREATE_POST_BUTTON = "//button[@id='demo-customized-button']//div[text()='Đăng']"
OPEN_FORM = "//p[text()='Ảnh/Video']"
LOGOUT_BTN = "//header//div[@role= 'button' and ./div/p[text()='Đăng xuất']]"
MEDIA_TAB = "//div[@class='html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x18d9i69 x6s0dn4 x9f619 x78zum5 x2lah0s x1hshjfz x1n2onr6 xng8ra x1pi30zi x1swvt13']/span[text()='Ảnh']"
VIEW_DETAIL = "//a[text()='Xem bài viết']"
CLOSE_DETAIL = "/html/body/div[1]/div/div/div[1]/div/div[2]/div[1]/a"
MEDIA_IN_DETAIL = "/html/body/div[1]/div/div/div[1]/div/div[6]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]"
TITLE_POST = "(//div[contains(@data-ad-comet-preview, 'message')])[{index}]"
POST = "//div[@aria-posinset='{index}']"
MORE_OPTION = "(//div[@aria-haspopup='menu' and contains(@class, 'x1i10hfl') and contains(@aria-label, 'Hành động với bài viết này')])[{index}]"
SKIP_BANNER = "//div[contains(text(), 'Tiếp tục')]"
ITEMS_VIDEO_WATCH = "(//div[@class='x1qjc9v5 x1lq5wgf xgqcy7u x30kzoy x9jhf4c x78zum5 xdt5ytf x1l90r2v xyamay9 xjl7jj']//div[.//span[text()='Video']])[1]/div/div/div/div/div/div/div/div/div/div/a"
ITEM_VIDEO_WATCH = "(//div[@class='x1qjc9v5 x1lq5wgf xgqcy7u x30kzoy x9jhf4c x78zum5 xdt5ytf x1l90r2v xyamay9 xjl7jj']//div[.//span[text()='Video']])[1]/div/div/div/div[{index}]/div/div/div/div/div/div/a"
TIME_VIDEO_WATCH = "(//div[@class='x1qjc9v5 x1lq5wgf xgqcy7u x30kzoy x9jhf4c x78zum5 xdt5ytf x1l90r2v xyamay9 xjl7jj']//div[.//span[text()='Video']])[1]/div/div/div/div[{index}]/div/div/div/div/div/div/a/div/div/div/div[2]/span"
TITLE_VIDEO_WATCH = "(//div[@class='x1qjc9v5 x1lq5wgf xgqcy7u x30kzoy x9jhf4c x78zum5 xdt5ytf x1l90r2v xyamay9 xjl7jj']//div[.//span[text()='Video']])[1]/div/div/div/div[{index}]/div/div/div/div/div/div[2]/span/div/a"
NEXT_REELS = "//div[@aria-label='Thẻ tiếp theo' and contains(@class, 'x1i10hfl')]"
OPEN_FORM_MOMENT = "//button[contains(@class, 'MuiButton-root') and .//p[text()='Khoảnh khắc']]"
INPUT_UPLOAD_MOMENT = "//input[@id='files' and @name='files']"
BUTTON_CREATE_MOMENT = "//div[@role='presentation']//button[2]"
INPUT_TITLE_MOMENT = "//textarea[@id='textInputCreateMoment']"
TITLE_REELS = "//div[@class='xyamay9 x1pi30zi x1swvt13 xjkvuk6']"
CLOSE_BAN_ACCOUNT = "//button[@type='button' and .//i[contains(@class, 'fa-xmark')]]"
OPEN_FORM_CREATE_MUSIC_BUTTON = "//div[@role='button' and contains(@class, 'MuiListItem-button')]//p[contains(text(), 'Tạo mới Album/Bài hát')]"
TITLE_MUSIC = "//textarea[@id='title']"
INPUT_UPLOAD_BANNER_MUSIC = "//input[@name='banner']"
INPUT_UPLOAD_MP3 = "//input[@name='file_mp3']"
INPUT_CATEGORY_MUSIC = "//input[@name='category_music_id']"
INPUT_PAGE_OWNER = "//input[@name='page_owner_id']"
INPUT_AUTHOR = "//input[@name='music_host_added']"
INPUT_FIELD = "//input[@type='file' and @accept='.doc, .docx, .pdf, .pptx, .ppt']"
INPUT_FIELD2 = "//textarea[ @name='field']"
SEND_REQUEST_MUSIC = "//button[.//div[text()='Gửi phê duyệt']]"
OPTION_CATEGORY = "//div[@id='mui-52-option-{index}']/div/div/p"
PAGE_OWNER_MUSIC = "//p[contains(.,'{page_name}')]"
AUTHOR_MUSIC = "//div[@id='mui-56-option-0']" #Tài khoản phải có bạn bè
    
PROFILE_AVATAR = "//main/div/div[1]/div[2]/div[1]/nav/a[1]"
OPEN_FORM_AVATAR = "//button[@aria-label='camera']//i[@class='fas fa-camera-alt']"
UPLOAD_AVT_TAB = "//p[contains(text(),'Tải ảnh lên')]"
INPUT_UPLOAD_AVT = "//input[@type='file' and @accept='image/jpeg,image/png' and @multiple]"
SAVE_IMAGE_AVT = "//button[div[contains(text(), 'Lưu')]]"
IMG_AVATAR = "/html/body/div[1]/div/div/main/div/div[2]/div/div[1]/div[1]/div[2]/div/div[1]/div[1]/div[1]/div/img"
DIALOG_UPDATE = "//div[@role='dialog' and @aria-labelledby='customized-dialog-title']" 
FORYOU_BUTTON = "//button[contains(@class, 'TUXButton') and .//div[contains(text(), 'Dành cho bạn')]]"

CLOSE_POPUP_URL = "//button[@class='TUXUnstyledButton TUXNavBarIconButton' and @aria-label='close']"
COMMENT_XPATH_TEMPLATE = "/html/body/div[1]/div[2]/div[3]/div/div[2]/div[1]/div/div[{}]/div[1]/div[1]/p[1]"
OPEN_TAB_COMMENT = "/html/body/div[1]/div[2]/main/div[1]/article[{index}]/div/section[2]/button[2]/span"

ITEM_VIDEO = "//video[.//source[@data-index='{index}']]"
DOWLOAD_VIDEO_BUTTON = "//div[@data-e2e='right-click-menu-popover_download-video']"
BUTTON_COMMENT = "(//span[@data-e2e='comment-icon'])[{index}]"
COMMENT_ITEM = "(//span[@data-e2e='comment-level-1'])[{index}]"
NEXT_VIDEO = "//div[@class='css-1o2f1ti-DivFeedNavigationContainer ei9jdxs0']//div[2]//button[1]"

VIDEO_DOWNLOAD_PATH = "videos/Download.mp4"
VIDEO_SAVE_DIR = "videos"

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def init_driver(config_path="config.json"):
    config = load_config(config_path)
    chrome_options = Options()

    # Thêm thông tin từ cấu hình
    chrome_options.add_argument(f"--user-data-dir={config['user_data_dir']}")

    # Các tuỳ chọn trình duyệt
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.webrtc": 2
    })

    # Khởi tạo driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Đặt geolocation
    location = config["location"]
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "accuracy": location["accuracy"]
    })

    time.sleep(2)
    return driver

def load_existing_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_video_duration(url):
    try:
        ydl_opts = {"quiet": True, "simulate": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("duration", 0)
    except:
        return 0
    
def get_video_info(driver, index):
    try:
        wait = WebDriverWait(driver, 10)
     
        # Lấy URL video
        video_url = driver.current_url
        video_id = video_url.split("/")[-1].split("?")[0]
        print(f"Debug - Video URL: {video_url}")

        # Lấy tiêu đề video
        title = ""
        try:
            # Đảm bảo lấy tiêu đề từ video hiện tại
            video_desc_xpath = '//article[@data-scroll-index="{index}" and @data-e2e="recommend-list-item-container"]//div[contains(@data-e2e, "video-desc")]'.replace("{index}", str(index - 1))
            title_element = wait.until(EC.presence_of_element_located((By.XPATH, video_desc_xpath)))
            title = title_element.text.strip()
            print(f"Debug - Title found: {title}")

            # Cắt ngắn tiêu đề nếu cần
            if len(title) > 150:
                title = title[:147] + "..."
        except Exception as e:
            print(f"Error getting title: {e}")
            # Thử lấy tiêu đề từ một XPath khác nếu cần
            try:
                alternative_title = driver.find_element(By.XPATH, "//h1[contains(@class, 'title')]").text.strip()
                title = alternative_title if alternative_title else "Untitled"
                print(f"Debug - Alternative title: {title}")
            except:
                title = "Untitled"

        return video_id, title, video_url
    except Exception as e:
        print(f"Error in get_video_info: {e}")
        return None, None, None

def click_element(driver, xpath):
    """Click vào phần tử theo XPath, đảm bảo nó xuất hiện trên màn hình và không bị chặn."""
    try:
        # Chờ phần tử xuất hiện và có thể click
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        # Cuộn phần tử vào vùng hiển thị
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)  # Chờ một chút để trang ổn định

        try:
            element.click()
        except ElementClickInterceptedException:
            print("⚠ Phần tử bị chặn khi click! Thử click bằng JavaScript.")
            driver.execute_script("arguments[0].click();", element)  # Click bằng JS
    
    except TimeoutException:
        print(f"⛔ Không thể click vào phần tử: {xpath} (Timeout)")
      
def right_click(driver, xpath):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        actions = ActionChains(driver)
        actions.context_click(element).perform()
    except Exception as e:
        print("Lỗi khi thực hiện right-click:", e)
        
def wait_for_element_clickable(driver, xpath, timeout=10):
    """Chờ đến khi element có thể click được."""
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))  # Định dạng đúng tuple (locator type, value)
    )


def input_text(driver, xpath: str, text: str):
        # Chờ phần tử có thể tương tác trong 1 giây
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))

        # Lấy phần tử
        element = driver.find_element(By.XPATH, xpath)

        # Xóa và nhập văn bản
        element.click()
        element.clear()  # Xóa nội dung cũ

        # Sử dụng ActionChains để nhập văn bản
        action = ActionChains(driver)
        
        # Nhắm đến phần tử cụ thể và gửi toàn bộ nội dung
        action.click(element)  # Đảm bảo focus vào phần tử
        action.send_keys(text)
        action.perform()  # Thực thi chuỗi hành động

def wait_for_element_not_present(driver, locator, timeout=120):
        try:
            WebDriverWait(driver, timeout).until_not(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            print(f"Element located by {locator} is not present in the DOM.")
        except TimeoutException:
            raise AssertionError(f"Element located by {locator} is still present in the DOM after {timeout} seconds.")
        except NoSuchElementException:
            print(f"Element located by {locator} was not found in the DOM initially.")


def upload_video(driver, file_name, input_xpath):
    try:
        if isinstance(file_name, list):
            for single_file in file_name:
                _upload_single_video(driver, single_file, input_xpath)  # Đã thêm `driver`
        else:
            _upload_single_video(driver, file_name, input_xpath)  # Đã thêm `driver`
    except Exception as e:
        print(f"Error uploading video: {e}")

def _upload_single_video(driver, file_name, input_xpath):
        try:
            # Đường dẫn tương đối tới tệp ideo
            relative_path = os.path.join(file_name)
            absolute_path = os.path.abspath(relative_path)  # Lấy đường dẫn tuyệt đối từ đường dẫn tương đối

            # Tìm phần tử input file và tải lên video
            file_input = driver.find_element(By.XPATH, input_xpath)
            file_input.send_keys(absolute_path)
            print(f"Video đã được tải lên từ: {absolute_path}")
        except Exception as e:
            print(f"Error uploading single video {file_name}: {e}")
            
def wait_for_element_present(driver, locator, timeout=30):
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, locator)))
    return driver.find_element(By.XPATH, locator)  # Sửa lỗi ở đây


def find_element_by_locator(driver, locator, context=None):
        if context:
            element = context.find_element(By.XPATH, locator)
        else:
            element = driver.find_element(By.XPATH, locator)
        return element

def close_popup(driver):
    try:
        close_button = driver.find_element(By.XPATH, CLOSE_POPUP_URL)
        driver.execute_script("arguments[0].click();", close_button)
        time.sleep(1)
    except:
        pass

def move_to_next_video(driver):
    click_element(driver, NEXT_VIDEO)
    time.sleep(3)
    
def get_random_comments(driver, index):
    """Lấy số lượng bình luận ngẫu nhiên từ video TikTok, bắt đầu từ bình luận thứ 3."""
    comments = []
    num_comments = random.randint(1, 20)  # Chọn số lượng bình luận ngẫu nhiên

    print("index:", index)
    # click_element(driver, OPEN_TAB_COMMENT.replace("{index}", str(index)))

    # Chờ bình luận thứ 3 xuất hiện trước khi tiếp tục
    third_comment_xpath = COMMENT_ITEM.replace("{index}", str(index))
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, third_comment_xpath))
        )
    except Exception as e:
        print(f"⚠ Không tìm thấy bình luận nào: {e}")
        return []

    # Lấy bình luận từ vị trí thứ 3 trở đi
    i = 1  # Bắt đầu từ comment số 3
    while len(comments) < num_comments:
        comment_xpath = COMMENT_ITEM.replace("{index}", str(i))
        try:
            comment_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, comment_xpath))
            )
            comment_text = comment_element.text.strip()
            if comment_text:
                comments.append(comment_text)
        except Exception:
            break  # Nếu không tìm thấy comment tiếp theo, dừng vòng lặp
        i += 1  # Tiếp tục lấy comment tiếp theo

    return comments

def save_comments_to_file(comments, filename="comment.txt"):
    """Lưu bình luận vào file, mỗi bình luận là một dòng."""
    try:
        with open(filename, "a", encoding="utf-8") as file:
            for comment in comments:
                file.write(comment + "\n")
        print(f"✅ Đã lưu {len(comments)} bình luận vào {filename}")
    except Exception as e:
        print(f"⚠ Lỗi lưu bình luận: {e}")

def upload(file_path, file_name, token, channel_id=2, privacy=1, mime_type="video/mp4"):
    if not os.path.exists(file_path):
        print(f"⚠ File không tồn tại: {file_path}")
        return None

    try:
        with open("token_upload.json", "r", encoding="utf-8") as f:
            token_data = json.load(f)
            if isinstance(token_data, list):
                token_upload = random.choice(token_data)
            elif isinstance(token_data, dict):
                token_upload = token_data.get("token")
            else:
                raise ValueError("Định dạng token_upload.json không hợp lệ")
    except Exception as e:
        print(f"⚠ Lỗi đọc token_upload.json: {e}")
        return None

    url = "https://prod-pt.emso.vn/api/v1/videos/upload"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_upload}",
        "origin": "https://emso.vn",
        "referer": "https://emso.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
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
        else:
            print(f"⚠ Lỗi tải video: {response.text}")
            return None
    except Exception as e:
        print(f"⚠ Lỗi kết nối API: {e}")
        return None
    
def statuses(token, content, media_ids, post_type="moment", visibility="public"):
    """Đăng bài lên EMSO và trả về ID bài đăng."""
    
    url = "https://prod-sn.emso.vn/api/v1/statuses"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "https://emso.vn",
        "referer": "https://emso.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
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
        else:
            print(f"⚠ Lỗi đăng bài: {response_data}")
            return None
    except Exception as e:
        print(f"⚠ Lỗi kết nối API: {e}")
        return None

def get_random_token(tokens_file="tokens.json"):
    """Lấy một token ngẫu nhiên từ file JSON."""
    try:
        with open(tokens_file, "r", encoding="utf-8") as file:
            tokens = json.load(file)  # Đọc danh sách token

            if not tokens:
                print("⚠ Không có token nào trong file.")
                return None

            return random.choice(tokens)  # Chọn ngẫu nhiên một token
    except Exception as e:
        print(f"⚠ Lỗi đọc file token: {e}")
        return None

def clean_tiktok_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

def login_emso_create(driver, title, image_names=None):
    token = get_random_token()

    # Đường dẫn cố định đến file Download.mp4 trong thư mục videos
    file_path = os.path.join("videos", "Download.mp4")
    print(f"Debug - Uploading file: {file_path}")

    # Kiểm tra file có tồn tại không
    if not os.path.isfile(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        return False

    media_ids = upload(file_path=file_path, file_name="Download.mp4", token=token)

    if media_ids:
        post_id = statuses(token=token, content=title, media_ids=[media_ids])
        print("ID post:", post_id)

        if post_id:
            print(f"📢 Chuẩn bị gọi post_comments với ID bài viết: {post_id}")
            post_comments(status_id=post_id)
            clear_comment_file()

            video_folder = "videos"
            try:
                for filename in os.listdir(video_folder):
                    file_to_remove = os.path.join(video_folder, filename)
                    if os.path.isfile(file_to_remove):
                        os.remove(file_to_remove)
                        print(f"🗑️ Đã xóa vĩnh viễn file: {file_to_remove}")
                print(f"🗑️ Đã xóa toàn bộ file trong thư mục {video_folder}")
            except Exception as e:
                print(f"⚠ Lỗi khi xóa file trong thư mục {video_folder}: {e}")
            return True

    return False


def clear_comment_file(comment_file="comment.txt"):
        """
        Xóa toàn bộ nội dung của file comment.txt.
        """
        try:
            with open(comment_file, "w", encoding="utf-8") as file:
                file.truncate(0)  # Xóa hết nội dung file
            print(f"Đã xóa nội dung của file {comment_file}.")
        except Exception as e:
            print(f"Lỗi khi xóa file {comment_file}: {e}")

def post_comments(status_id, delay=2):
        url = f"https://prod-sn.emso.vn/api/v1/statuses/{status_id}/comments"

        # Đọc danh sách token từ file
        tokens_file = "token_comment.json"
        if not os.path.exists(tokens_file):
            print("❌ Không tìm thấy file tokens.json")
            return
        
        with open(tokens_file, "r", encoding="utf-8") as file:
            try:
                tokens = json.load(file)
            except json.JSONDecodeError:
                print("❌ Lỗi khi đọc file tokens.json: Nội dung không hợp lệ.")
                return

        if not tokens:
            print("❌ Không có token hợp lệ trong danh sách.")
            return

        # Đọc danh sách comment từ file
        comments_file = "comment.txt"
        if not os.path.exists(comments_file):
            print("❌ Không tìm thấy file comment.txt")
            return
        
        with open(comments_file, "r", encoding="utf-8") as file:
            comments = [line.strip() for line in file if line.strip()]  # Loại bỏ dòng trống

        if not comments:
            print("❌ Không có comment để đăng.")
            return

        # Lấy số lượng comment nhỏ nhất có thể gửi (giới hạn bởi số token)
        num_posts = min(len(tokens), len(comments))

        # Chọn token ngẫu nhiên, không trùng nhau
        selected_tokens = random.sample(tokens, num_posts)

        for i in range(num_posts):
            token = selected_tokens[i]
            comment = comments[i]

            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                'authorization': f'Bearer {token}',
                'content-type': 'application/json',
                'origin': 'https://emso.vn',
                'priority': 'u=1, i',
                'referer': 'https://emso.vn/',
                'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
            }
            
            payload = json.dumps({
                "id": random.random(),  # Tạo số ngẫu nhiên như trong curl example
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
            })

            print(f"\n📌 Gửi comment: \"{comment}\" vào bài viết ID: {status_id} với token: {token[:10]}...")

            try:
                response = requests.post(url, data=payload, headers=headers)
                response_text = response.text

                if response.status_code == 200:
                    print(f"✅ Đã gửi comment thành công: {comment}")
                elif response.status_code == 404:
                    print(f"⚠️ Lỗi 404: Bài viết không tồn tại hoặc đã bị xóa. ID post: {status_id}")
                elif response.status_code == 500:
                    print(f"❌ Lỗi máy chủ (500): API có thể đang gặp vấn đề hoặc payload không đúng.")
                else:
                    print(f"⚠️ Lỗi {response.status_code}: {response_text}")

            except requests.exceptions.RequestException as e:
                print(f"❌ Lỗi khi gửi request: {e}")

            time.sleep(delay)  # Chờ một khoảng thời gian trước khi gửi tiếp để tránh bị block
            
def delete_video_file():
    file_path = os.path.join("videos", "Download.mp4")
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            print(f"🗑 Đã xóa file: {file_path}")
        else:
            print(f"⚠ Không tìm thấy file: {file_path}")
    except Exception as e:
        print(f"⚠ Không thể xóa file: {e}")

def check_element_exists(driver, selector, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, selector))
        )
        return True
    except TimeoutException:
        return False

def main():
    num_videos = int(input("Nhập số lượng video cần tải: "))
    driver = init_driver()
    driver.maximize_window()
    driver.get("https://www.tiktok.com/foryou?lang=vi-VN")
    click_element(driver, BUTTON_COMMENT.replace("{index}", "1"))

    data = load_existing_data()
    downloaded_count = 0
    index = 1

    try:
        while downloaded_count < num_videos:
            print(f"📥 Đang lấy video thứ {downloaded_count + 1}/{num_videos}...")

            # Chờ video và lấy thông tin video
            video_id, title, video_url = get_video_info(driver, index)
            
            # Kiểm tra nếu thông tin video không hợp lệ
            if not video_id or not title:
                print("⚠ Lỗi lấy thông tin video, chuyển video tiếp theo.")
                move_to_next_video(driver)
                time.sleep(5)  # Đảm bảo video tiếp theo được tải sau khi next
                continue

            # Kiểm tra nếu video đã tồn tại trong dữ liệu
            if video_id in data:
                print("⚠ Video đã tồn tại, chuyển sang video tiếp theo.")
                move_to_next_video(driver)
                time.sleep(5)  # Đảm bảo video tiếp theo được tải sau khi next
                continue

            # Kiểm tra độ dài video
            duration = get_video_duration(video_url)
            if duration > 300:
                print("⚠ Video quá dài (>5 phút), bỏ qua.")
                move_to_next_video(driver)
                time.sleep(5)  # Đảm bảo video tiếp theo được tải sau khi next
                continue

            # Kiểm tra xem nút tải có tồn tại không
            right_click(driver, ITEM_VIDEO.replace("{index}", str(index)))

            if not check_element_exists(driver, DOWLOAD_VIDEO_BUTTON):
                print("⚠ Không có nút tải, chuyển sang video tiếp theo.")
                move_to_next_video(driver)
                time.sleep(5)  # Đảm bảo video tiếp theo được tải sau khi next
                continue
            else:
                try:
                    # Thử nhấn nút tải video
                    click_element(driver, DOWLOAD_VIDEO_BUTTON)
                    print("✅ Nút tải video đã được nhấn.")
                except Exception as e:
                    print(f"⚠ Không thể nhấn nút tải video: {e}. Chuyển sang video tiếp theo.")
                    move_to_next_video(driver)
                    time.sleep(5)  # Đảm bảo video tiếp theo được tải sau khi next
                    continue

            # Lưu thông tin video
            file_path = VIDEO_SAVE_DIR
            data[video_id] = {"title": title, "url": video_url, "file_path": file_path}
            save_data(data)
            downloaded_count += 1
            print(f"✅ Video {downloaded_count} đã tải xuống: {title}")
            
            time.sleep(3)

            # Lấy bình luận nếu có
            comments = get_random_comments(driver, index=index)
            if comments:
                save_comments_to_file(comments)
            else:
                print("⚠ Không có bình luận nào để lưu.")

            print("🔄 Chuyển sang EMSO để đăng video...")
            if login_emso_create(driver, title):
                print("✅ Đăng bài thành công, quay lại TikTok...")
                time.sleep(3)  # Đảm bảo rằng các thao tác xóa file hoàn tất
            else:
                print("⚠ Đăng bài thất bại, quay lại TikTok...")

            # Sau khi đăng xong, chuyển sang video tiếp theo và tăng index
            move_to_next_video(driver)
            index += 1  # Đảm bảo rằng index được tăng sau khi video đã được xử lý hoàn tất

    finally:
        driver.quit()
        print("🎉 Hoàn thành!")


if __name__ == "__main__":
    main()
