import logging
import time
import json
import re
from bs4 import BeautifulSoup, Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

try:
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_argument('--headless=new') 
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except:
        driver = webdriver.Chrome(options=options)

    url = "https://www.flipkart.com/hotstyle-running-shoes-men/p/itmccb11d3ba330c?pid=SHOHBFS4JYQUUZKR&lid=LSTSHOHBFS4JYQUUZKRWY4YTR&marketplace=FLIPKART&q=shoes&store=osp&srno=s_1_1&otracker=AS_Query_TrendingAutoSuggest_2_0_na_na_na&otracker1=AS_Query_TrendingAutoSuggest_2_0_na_na_na&fm=search-autosuggest&iid=en_47wYVS4cutkzhLcwK7LRMd61heHxrteq6RypHg092fRR-AkTlUojlOgTZgo6hMEehZI1z0qMNvGLkAK0WUIcOQ%3D%3D&ppt=sp&ppn=sp&ssid=3w3at10zls0000001765641615269&qH=b0a8b6f820479900"

    if 'product-reviews' not in url and '/p/' in url:
        url = url.replace('/p/', '/product-reviews/')
    if '?' in url:
        url = url.split('?')[0]

    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    with open("debug_log.txt", "w", encoding="utf-8") as f:
        f.write("\n--- DOM DUMP ---\n")
        
        # Check 1: Do we even have the text?
        if "Certified Buyer" in html:
            f.write("YES, 'Certified Buyer' is in HTML source.\n")
        else:
            f.write("NO, 'Certified Buyer' NOT found in HTML source.\n")
        
        # Check 2: Find node
        nodes = soup.find_all(string=re.compile("Certified Buyer"))
        f.write(f"BS4 Found {len(nodes)} text nodes.\n")
        
        if nodes:
            node = nodes[0]
            curr = node
            indent = 0
            f.write("Ancestry:\n")
            for _ in range(15):
                if curr is None or curr.name == '[document]': break
                
                tag_info = "String"
                if isinstance(curr, Tag):
                    cls = '.'.join(curr.get('class', [])) if curr.get('class') else ""
                    tag_info = f"<{curr.name} class='{cls}'>"
                elif isinstance(curr, NavigableString):
                    tag_info = "StringNode"
                
                # Check content
                extra = ""
                try:
                    txt = curr.get_text()[:30].replace('\n','')
                    if '★' in txt: extra += " [STAR]"
                    if len(txt) > 20: extra += f" Text:'{txt}'"
                except: pass
                
                f.write(f"{' ' * indent} {tag_info} {extra}\n")
                
                curr = curr.parent
                indent += 1
                
        # Check 3: JSON-LD
        f.write("\n--- JSON CHECK ---\n")
        scripts = soup.find_all('script', type='application/ld+json')
        f.write(f"Found {len(scripts)} LD scripts.\n")
        for s in scripts:
            if s.string and ('Review' in s.string or 'aggregateRating' in s.string):
                f.write("Found Review/Rating schema!\n")

finally:
    driver.quit()
