import json
import re
from bs4 import BeautifulSoup, Tag, NavigableString
from scraper import init_driver, driver, close_driver, random_sleep
import time
import traceback

# User's difficult URL
url = "https://www.flipkart.com/hotstyle-running-shoes-men/p/itmccb11d3ba330c?pid=SHOHBFS4JYQUUZKR&lid=LSTSHOHBFS4JYQUUZKRWY4YTR&marketplace=FLIPKART&q=shoes&store=osp&srno=s_1_1&otracker=AS_Query_TrendingAutoSuggest_2_0_na_na_na&otracker1=AS_Query_TrendingAutoSuggest_2_0_na_na_na&fm=search-autosuggest&iid=en_47wYVS4cutkzhLcwK7LRMd61heHxrteq6RypHg092fRR-AkTlUojlOgTZgo6hMEehZI1z0qMNvGLkAK0WUIcOQ%3D%3D&ppt=sp&ppn=sp&ssid=3w3at10zls0000001765641615269&qH=b0a8b6f820479900"

if '/p/' in url and '/product-reviews/' not in url:
    reviews_url = url.replace('/p/', '/product-reviews/')
else:
    reviews_url = url
if '?' in reviews_url: reviews_url = reviews_url.split('?')[0]

print(f"Targeting: {reviews_url}")

init_driver()
try:
    driver.get(reviews_url)
    random_sleep(3, 5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    print("Page Title:", soup.title.string if soup.title else "No Title")

    # Method 3: DOM Structure Reverse Engineering (Safe Mode)
    print("\n[Method 3] DOM Reverse Engineering:")
    try:
        start_nodes = soup.find_all(string=re.compile("Certified Buyer"))
        if start_nodes:
            print(f"  Found {len(start_nodes)} 'Certified Buyer' text nodes.")
            # Start from the containing tag of the text
            curr = start_nodes[0]
            if isinstance(curr, NavigableString):
                curr = curr.parent

            print("  Tracing ancestry of the first match:")
            indent = 0
            for _ in range(15):
                if curr is None or curr.name == '[document]': break
                
                # Safe class get
                classes = "N/A"
                tag_name = "N/A"
                
                if isinstance(curr, Tag):
                    tag_name = curr.name
                    classes = '.'.join(curr.get('class', []))
                else:
                    tag_name = str(type(curr))

                print(f"  {' ' * indent} <{tag_name} class='{classes}'>")
                
                # Check snippet
                try:
                    txt = curr.get_text()[:60].replace('\n', ' ')
                    print(f"  {' ' * indent}   Text: {txt}...")
                except:
                    pass
                
                curr = curr.parent
                indent += 1
        else:
            print("  No 'Certified Buyer' found in DOM!")
    except Exception:
        traceback.print_exc()

    # Method 2: React State
    print("\n[Method 2] React State extraction:")
    try:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('window.__INITIAL_STATE__' in script.string):
                print("  -> Found Likely State Script!")
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*});', script.string)
                if match:
                    try:
                        state_json = match.group(1)
                        print(f"  -> Extracted JSON string length: {len(state_json)}")
                        state = json.loads(state_json)
                        print("  -> Successfully parsed INITIAL_STATE!")
                        keys = list(state.keys())
                        print(f"  Keys: {keys[:10]}")
                    except Exception as e:
                        print(f"  -> JSON parse failed: {e}")
    except Exception:
         traceback.print_exc()

finally:
    close_driver()
