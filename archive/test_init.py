from scraper import init_driver, scrape_reviews, close_driver, driver
import time

print("TEST 1: Init Driver")
try:
    init_driver()
    print("SUCCESS: Driver initialized.")
    if driver:
        print("Driver object exists.")
        driver.get("https://www.google.com")
        print("Navigated to Google.")
        time.sleep(2)
    else:
        print("FAILURE: Driver is None.")
except Exception as e:
    print(f"FAILURE: Init crashed: {e}")

print("\nTEST 2: Scrape Call")
url = "https://www.flipkart.com/hotstyle-running-shoes-men/product-reviews/itmccb11d3ba330c?pid=SHOHBFS4JYQUUZKR"
try:
    res = scrape_reviews(url, progress_callback=lambda m, p: print(f"CB: {m}"))
    print(f"Result: {res}")
except Exception as e:
    print(f"Scrape Crashed: {e}")

close_driver()
