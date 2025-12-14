# scraper.py
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time
import pandas as pd
import random

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

driver = None

def init_driver():
    global driver
    if driver is not None:
        try:
            # Check if alive
            driver.title
            return
        except:
            driver = None

    options = webdriver.ChromeOptions()
    # IMPORTANT: HEADLESS FALSE FOR USER VISIBILITY
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-infobars')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--start-maximized')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    if WEBDRIVER_MANAGER_AVAILABLE:
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"Error initializing driver: {e}")
            driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Chrome(options=options)
    
    driver.implicitly_wait(5)
    driver.set_page_load_timeout(45)
    driver.set_script_timeout(45)
    logger.info("Driver initialized successfully")
    
    # Stealth
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

def close_driver():
    global driver
    if driver:
        try:
            driver.quit()
        except: pass
        driver = None

def get_text_safe(element, selectors):
    for selector in selectors:
        try:
            if selector.startswith('//') or selector.startswith('.//'):
                el = element.find_element(By.XPATH, selector)
            else:
                el = element.find_element(By.CSS_SELECTOR, selector)
            return el.text.strip()
        except: continue
    return None

def clean_text(text):
    if not text: return ""
    return text.replace('READ MORE', '').strip()

def flipkart(url, filter_type, max_pages=1, progress_callback=None):
    names, titles, ratings, contents = [], [], [], []
    
    if '/p/' in url and '/product-reviews/' not in url:
        reviews_url = url.replace('/p/', '/product-reviews/')
    else:
        reviews_url = url
    if '?' in reviews_url: reviews_url = reviews_url.split('?')[0]
    
    logger.info(f"Target: {reviews_url}")
    if progress_callback: progress_callback(f"Target: {reviews_url}", 10)

    for page in range(1, max_pages + 1):
        page_url = f"{reviews_url}?page={page}&sortOrder={filter_type}"
        try:
            driver.get(page_url)
            time.sleep(2) # Wait for render

            review_containers = []
            
            # STRATEGY 1: Known classes
            selectors = ["div.col.x_CUu6.QccLnz", "div.col.x_CUu6"]
            for s in selectors:
                found = driver.find_elements(By.CSS_SELECTOR, s)
                if found:
                    for f in found:
                        if len(f.text)>5 and f not in review_containers:
                            review_containers.append(f)
                    if review_containers: break
            
            # STRATEGY 2: Fallback via Certified Buyer
            if not review_containers:
                 p_tags = driver.find_elements(By.XPATH, "//p[contains(@class,'Zhmv6U')] | //*[contains(text(),'Certified Buyer')]")
                 for p in p_tags[:15]:
                     try:
                         # Go up to the col container
                         parent = p.find_element(By.XPATH, "./../../..") # Adjust based on depth
                         if "col" in parent.get_attribute("class"):
                             if parent not in review_containers: review_containers.append(parent)
                     except: pass
            
            # De-dup
            unique = []
            seen = set()
            for r in review_containers:
                if r not in seen:
                     unique.append(r)
                     seen.add(r)
            review_containers = unique

            logger.info(f"Found {len(review_containers)} reviews")
            if progress_callback: progress_callback(f"Found {len(review_containers)} reviews", 30)

            for card in review_containers:
                try:
                    # 1. Rating
                    rating = '0'
                    try:
                         r = get_text_safe(card, [".//div[contains(@class, 'MKiFS6')]", ".//div[contains(@class, 'XQDdHH')]", ".//div[contains(text(), '★')]"])
                         if r: rating = r.replace('★', '').strip()
                    except: pass

                    # 2. Name (Moved Up)
                    name = "Flipkart Customer"
                    try:
                        n_el = card.find_elements(By.XPATH, ".//p[contains(@class, 'zJ1ZGa') and contains(@class, 'ZDi3w2')]")
                        if n_el: name = n_el[0].text
                        else:
                             ps = card.find_elements(By.XPATH, ".//p[contains(@class, 'zJ1ZGa')]")
                             for p in ps:
                                 t = p.text
                                 if len(t)>3 and not any(m in t for m in ['Jan','Feb','Oct','Nov','Dec','202']):
                                     name = t
                                     break
                    except: pass

                    # 3. Content (Robust Subtraction + Name Removal)
                    full_text = card.text.strip()
                    footer_text = ""
                    try:
                        ft_el = card.find_elements(By.XPATH, ".//div[contains(@class, 'row') and .//div[contains(text(), 'Certified Buyer')]]")
                        if ft_el: footer_text = ft_el[0].text
                    except: pass
                    
                    if not footer_text:
                         lines = full_text.split('\n')
                         for i, line in enumerate(lines):
                             if "Certified Buyer" in line or "Permalink" in line:
                                 footer_text = "\n".join(lines[i:])
                                 break
                    
                    clean_content = full_text.replace(footer_text, "").strip()
                    if rating != '0' and clean_content.startswith(rating):
                        clean_content = clean_content[len(rating):].strip()
                    
                    # Remove Name from Content
                    clean_content = clean_content.replace(name, '').strip()
                    
                    clean_content = clean_text(clean_content)

                    names.append(name)
                    # titles.append(title) # Removed
                    ratings.append(float(rating[:3]) if rating and rating[0].isdigit() else 0.0)
                    contents.append(clean_content)
                except: continue

        except Exception as e:
            logger.error(f"Page Error: {e}")
    
    return names, titles, ratings, contents

def amazon(url, filter_type, max_pages=1, progress_callback=None):
    # Minimal logic for amazon
    names, titles, ratings, contents = [], [], [], []
    driver.get(url)
    return names, titles, ratings, contents

def detect_site(url):
    if "amazon" in url.lower(): return "amazon"
    if "flipkart" in url.lower(): return "flipkart"
    return None

def scrape_reviews(url, max_pages=1, progress_callback=None, output_file="reviews.csv"):
    init_driver()
    site = detect_site(url)
    if not site: return None, 0
    
    try:
        # User requested MOST_HELPFUL sort to get mixed reviews
        if site == "amazon":
            # Amazon logic (simplified for now, passing max_pages)
            nn, _, nr, nc = amazon(url, 'most_helpful', max_pages, progress_callback)
        else:
            # Flipkart: Single call with MOST_HELPFUL
            nn, _, nr, nc = flipkart(url, 'MOST_HELPFUL', max_pages, progress_callback)
            
        data = {'Name': nn, 'Rating': nr, 'Content': nc}
        df = pd.DataFrame(data)
        if df.empty: return None, 0
        
        # Dedupe
        df['id'] = df['Name'] + df['Content']
        df.drop_duplicates(subset=['id'], inplace=True)
        df.drop(columns=['id'], inplace=True)
        df = df[df['Content'] != ""]
        
        df.to_csv(output_file, index=False)
        return output_file, len(df)
    except Exception as e:
        logger.error(f"Main Error: {e}")
        return None, 0
    finally:
        close_driver()
