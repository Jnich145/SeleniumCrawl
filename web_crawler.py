import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse, unquote
from webdriver_manager.chrome import ChromeDriverManager
import csv
import random
import logging
from datetime import datetime
import re
import hashlib
import pickle
import mimetypes
import urllib.parse
import traceback

# List of common user agents for randomization
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

# Initialize the WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Utility functions
def get_random_user_agent():
    return random.choice(USER_AGENTS)

def print_progress(message):
    print(f"\r{message}", end='', flush=True)

def random_delay(min_delay=1, max_delay=5):
    return random.uniform(min_delay, max_delay)

def is_subdomain(url, main_domain):
    parsed_url = urlparse(url)
    parsed_main = urlparse(main_domain)
    return parsed_url.netloc.endswith(parsed_main.netloc) or parsed_main.netloc.endswith(parsed_url.netloc)

def is_likely_thumbnail(url):
    thumbnail_patterns = ['thumb', 'small', 'icon', 'avatar', 'preview', 'tiny']
    return any(pattern in url.lower() for pattern in thumbnail_patterns)

def get_original_image_url(img_tag, page_url):
    for attr in ['data-src', 'data-original', 'data-full-size', 'src']:
        if attr in img_tag.attrs:
            url = img_tag[attr]
            full_url = urljoin(page_url, url)
            if not is_likely_thumbnail(full_url):
                return full_url
    
    parent_a = img_tag.find_parent('a')
    if parent_a and 'href' in parent_a.attrs:
        href = parent_a['href']
        full_url = urljoin(page_url, href)
        if href.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg')):
            return full_url
    
    return urljoin(page_url, img_tag['src']) if 'src' in img_tag.attrs else None

def is_valid_url(url):
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in ('http', 'https')

class NameManager:
    def __init__(self, base_save_path):
        self.base_save_path = base_save_path
        self.pickle_path = os.path.join(base_save_path, 'name_mapping.pickle')
        self.name_map = self.load_name_map()

    def load_name_map(self):
        if os.path.exists(self.pickle_path):
            with open(self.pickle_path, 'rb') as f:
                return pickle.load(f)
        return {}

    def save_name_map(self):
        with open(self.pickle_path, 'wb') as f:
            pickle.dump(self.name_map, f)

    def get_filename(self, url, content_type):
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = self.get_file_extension(content_type)
        return f"{url_hash}{ext}"

    def get_file_extension(self, content_type):
        content_type = content_type.lower()
        if 'svg' in content_type:
            return '.svg'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'html' in content_type:
            return '.html'
        elif 'csv' in content_type:
            return '.csv'
        else:
            ext = mimetypes.guess_extension(content_type)
            return ext if ext else '.dat'

    def sanitize_filename(self, filename):
        return re.sub(r'[^\w\-_\. ]', '_', filename).replace(' ', '_')

    def content_changed(self, url, content):
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        content_hash = hashlib.md5(content).hexdigest()[:8]
        
        if url_hash in self.name_map:
            return self.name_map[url_hash]['content_hash'] != content_hash
        return True

class CrawlManager:
    def __init__(self, base_save_path, max_depth, skip_navbar, skip_footer,
                capture_html, capture_images, capture_tables, image_types, max_pages):
        self.base_save_path = base_save_path
        self.max_depth = max_depth
        self.skip_navbar = skip_navbar
        self.skip_footer = skip_footer
        self.capture_html = capture_html
        self.capture_images = capture_images
        self.capture_tables = capture_tables
        self.image_types = image_types
        self.max_pages = max_pages
        self.crawl_log_file = os.path.join(base_save_path, 'crawl_log.csv')
        self.name_manager = NameManager(base_save_path)
        self.initialize_crawl_log()

    def initialize_crawl_log(self):
        os.makedirs(os.path.dirname(self.crawl_log_file), exist_ok=True)
        if not os.path.exists(self.crawl_log_file):
            with open(self.crawl_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Timestamp', 'Content Type', 'Saved Path'])

    def get_save_path(self, url, content_type, entity_name):
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path).strip('/')
        
        entity_folder = os.path.join(self.base_save_path, self.name_manager.sanitize_filename(entity_name))
        
        if content_type == 'html':
            return os.path.join(entity_folder, 'HTML', f"{self.name_manager.sanitize_filename(os.path.basename(path)) or 'index'}.html")
        elif content_type == 'image':
            file_name, file_extension = os.path.splitext(os.path.basename(path))
            if not file_extension:
                file_extension = '.jpg'  # Default to .jpg if no extension
            subfolder = file_extension[1:].lower()  # Remove the dot
            return os.path.join(entity_folder, 'Images', subfolder, f"{self.name_manager.sanitize_filename(file_name)}{file_extension}")
        elif content_type == 'table':
            return os.path.join(entity_folder, 'Tables', f"{self.name_manager.sanitize_filename(os.path.basename(path)) or 'table'}.csv")
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    def log_entry(self, url, timestamp, content_type, saved_path):
        with open(self.crawl_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([url, timestamp, content_type, saved_path])

def capture_full_html(driver, url, save_path, content_tracker):
    print_progress(f"Capturing full HTML for: {url}")
    html_content = driver.page_source.encode('utf-8')
    content_hash = hashlib.md5(html_content).hexdigest()

    if content_hash in content_tracker:
        logging.info(f"HTML content already captured: {url}")
        return None

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        f.write(html_content)
    
    content_tracker.add(content_hash)
    logging.info(f"Full HTML captured: {url}")
    return url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'HTML', save_path

def collect_images_from_page(driver, url, image_types):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    page_images = []
    
    for img in soup.find_all('img'):
        original_url = get_original_image_url(img, url)
        if original_url and not is_likely_thumbnail(original_url):
            if any(original_url.lower().endswith(ext) for ext in image_types):
                page_images.append(original_url)
    
    if '.svg' in image_types:
        for svg in soup.find_all('svg'):
            svg_url = urljoin(url, svg.get('src', ''))
            if svg_url:
                page_images.append(svg_url)
        
        for obj in soup.find_all('object', type='image/svg+xml'):
            svg_url = urljoin(url, obj.get('data', ''))
            if svg_url:
                page_images.append(svg_url)
    
    return page_images

def download_image(url, source_page, save_path, content_tracker):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.content
        content_hash = hashlib.md5(content).hexdigest()

        if content_hash in content_tracker:
            logging.info(f"Content already captured: {url}")
            return None

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(content)
        
        content_tracker.add(content_hash)
        logging.info(f"Downloaded: {url}")
        return url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Image', save_path
    except Exception as e:
        logging.error(f"Failed to download/save: {url}. Error: {str(e)}")
        return None

def capture_tables_from_page(driver, url, save_path, content_tracker):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    tables = soup.find_all('table')
    table_count = 0

    for i, table in enumerate(tables):
        table_content = str(table)
        content_hash = hashlib.md5(table_content.encode()).hexdigest()

        if content_hash in content_tracker:
            logging.info(f"Table already captured from: {url}")
            continue

        file_path = f"{save_path}_{i+1}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        rows = table.find_all('tr')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow([cell.text.strip() for cell in row.find_all(['th', 'td'])])
        
        content_tracker.add(content_hash)
        table_count += 1
        logging.info(f"Captured table {i+1} from: {url}")

    return table_count

def get_body_links(driver, skip_navbar, skip_footer):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    body = soup.find('body')

    if skip_navbar:
        header = body.find(['header', 'nav', 'div', 'section'], class_=lambda x: x and any(c in x for c in ['header', 'nav', 'top']))
        if header:
            header.decompose()

    if skip_footer:
        footer = body.find(['footer', 'div', 'section'], class_=lambda x: x and 'footer' in x)
        if footer:
            footer.decompose()

    content_links = []
    for a in body.find_all('a', href=True):
        if not any(parent.get('class') and any(c in ' '.join(parent.get('class')) for c in ['header', 'footer']) 
                   for parent in a.parents):
            content_links.append((a.get_text(strip=True), a['href']))

    return content_links

def crawl_page(driver, url, crawl_manager, content_tracker, current_depth=1, visited_pages=None, page_count=0):
    if visited_pages is None:
        visited_pages = set()

    if (current_depth > crawl_manager.max_depth or 
        url in visited_pages or 
        page_count >= crawl_manager.max_pages):
        return page_count

    visited_pages.add(url)
    page_count += 1
    print_progress(f"Crawling page {page_count} (Depth {current_depth}/{crawl_manager.max_depth}): {url}")

    try:
        driver.get(url)
        time.sleep(random_delay())

        entity_name = driver.title or urlparse(url).netloc

        # Capture HTML
        if crawl_manager.capture_html:
            html_save_path = crawl_manager.get_save_path(url, 'html', entity_name)
            html_result = capture_full_html(driver, url, html_save_path, content_tracker)
            if html_result:
                crawl_manager.log_entry(*html_result)

        # Capture images
        if crawl_manager.capture_images:
            images = collect_images_from_page(driver, url, crawl_manager.image_types)
            for img_url in images:
                img_save_path = crawl_manager.get_save_path(img_url, 'image', entity_name)
                img_result = download_image(img_url, url, img_save_path, content_tracker)
                if img_result:
                    crawl_manager.log_entry(*img_result)

        # Capture tables
        if crawl_manager.capture_tables:
            table_save_path = crawl_manager.get_save_path(url, 'table', entity_name)
            table_count = capture_tables_from_page(driver, url, table_save_path, content_tracker)

        # Get body links
        body_links = get_body_links(driver, crawl_manager.skip_navbar, crawl_manager.skip_footer)

        # Crawl subpages
        for link_text, link_url in body_links:
            full_url = urljoin(url, link_url)
            if is_subdomain(full_url, urlparse(url).netloc) and is_valid_url(full_url):
                page_count = crawl_page(driver, full_url, crawl_manager, content_tracker, current_depth + 1, visited_pages, page_count)
                if page_count >= crawl_manager.max_pages:
                    return page_count

    except Exception as e:
        logging.error(f"Error processing {url}: {str(e)}")
        logging.error(f"Error details: {traceback.format_exc()}")
        print_progress(f"Error processing {url}: {str(e)}")

    return page_count

def crawl_and_capture(driver, start_url, crawl_manager):
    print_progress("Starting crawl and capture process...")
    content_tracker = set()
    crawl_page(driver, start_url, crawl_manager, content_tracker)
    crawl_manager.name_manager.save_name_map()
    print_progress("Crawling completed.\n")

def get_save_path():
    while True:
        save_path = input("Enter the full path to save data (e.g., ~/Desktop/TESTS/Test 1): ").strip()
        save_path = os.path.expanduser(save_path)  # Expand ~ to full home directory path
        
        try:
            os.makedirs(save_path, exist_ok=True)
            return save_path
        except Exception as e:
            print(f"Error creating directory: {e}")
            print("Please enter a valid path or ensure you have the necessary permissions.")

def setup_logging(save_path):
    log_file = os.path.join(save_path, 'web_crawler.log')
    logging.basicConfig(filename=log_file, level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Logging initialized")

if __name__ == "__main__":
    try:
        print("Initializing WebDriver...")
        chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        print("WebDriver initialized successfully")

        website_url = input("Enter the website URL to crawl: ").strip()
        
        print("\nSpecify where to save the crawled data.")
        print("You can use '~' to represent your home directory.")
        print("Example: ~/Desktop/TESTS/Test 1")
        save_path = get_save_path()

        print(f"\nData will be saved to: {save_path}")

        setup_logging(save_path)

        print(f"\nStarting web crawling process for {website_url}")

        max_depth = int(input("Enter the maximum crawl depth: ").strip())
        max_pages = int(input("Enter the maximum number of pages to crawl (default 1000): ") or "1000")
        
        skip_navbar = input("Skip navbar links? (y/n): ").strip().lower() == 'y'
        skip_footer = input("Skip footer links? (y/n): ").strip().lower() == 'y'
        
        capture_html = input("Capture HTML? (y/n): ").strip().lower() == 'y'
        capture_images = input("Capture images? (y/n): ").strip().lower() == 'y'
        capture_tables = input("Capture tables? (y/n): ").strip().lower() == 'y'
        
        image_types = []
        if capture_images:
            image_types = input("Enter image types to download (comma-separated, e.g., .jpg,.png,.svg), or 'all' for all types: ").strip().lower()
            image_types = [t.strip() for t in image_types.split(',')] if image_types != 'all' else ['.jpg', '.jpeg', '.png', '.gif', '.svg']

        crawl_manager = CrawlManager(
            save_path, max_depth, skip_navbar, skip_footer,
            capture_html, capture_images, capture_tables, image_types, max_pages
        )
        crawl_and_capture(driver, website_url, crawl_manager)

        print(f"\nCrawling completed. Check the '{save_path}' directory for captured data.")

    except Exception as e:
        logging.critical(f"An error occurred: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        print("Check the web_crawler.log file for details.")
    finally:
        if 'driver' in locals():
            print("Closing WebDriver...")
            driver.quit()
            print("WebDriver closed")
