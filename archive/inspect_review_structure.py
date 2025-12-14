from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Setup
options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--start-maximized')
options.add_argument('--headless=new')

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
except:
    driver = webdriver.Chrome(options=options)

url = "https://www.flipkart.com/hotstyle-running-shoes-men/product-reviews/itmccb11d3ba330c?pid=SHOHBFS4JYQUUZKR"

try:
    print(f"Navigating: {url}")
    driver.get(url)
    time.sleep(5)

    # Use the KNOWN GOOD selector (or what we think is good)
    # The user says it's flawed, but we need to see WHY.
    # Searching for the main container
    containers = driver.find_elements(By.CSS_SELECTOR, "div.col.x_CUu6.QccLnz")
    print(f"Found {len(containers)} containers.")

    if containers:
        with open("structure_log.txt", "w", encoding="utf-8") as f:
            for i, card in enumerate(containers[:5]): # Check first 5
                f.write(f"\n\n=== CARD {i+1} ===\n")
                outer_html = card.get_attribute('outerHTML')
                soup = BeautifulSoup(outer_html, 'html.parser')
                
                # f.write(soup.prettify()) # Too verbose, stick to tree
                f.write("\n--- MAPPING CHILDREN ---\n")
                
                def print_struct(element, indent=0):
                    if element.name is None: return
                    
                    cls = '.'.join(element.get('class', []))
                    txt = element.get_text(strip=True)[:60].replace('\n', ' ')
                    line = f"{'  '*indent} <{element.name} class='{cls}'> : '{txt}'\n"
                    f.write(line)
                    
                    for child in element.children:
                        if child.name:
                            print_struct(child, indent+1)
                
                print_struct(soup)

finally:
    driver.quit()
