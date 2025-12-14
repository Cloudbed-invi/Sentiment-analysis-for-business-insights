from scraper import scrape_reviews
import pandas as pd
import os

url = "https://www.flipkart.com/hotstyle-running-shoes-men/product-reviews/itmccb11d3ba330c?pid=SHOHBFS4JYQUUZKR"
print(f"Testing Scraper on: {url}")

try:
    csv_file, count = scrape_reviews(url, progress_callback=lambda m, p: print(f"[{p}%] {m}"), output_file="reviews_test.csv")
    
    if csv_file and os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        print("\n--- SAMPLE DATA ---")
        print(df.head(5).to_string())
    else:
        print("Scraping returned no file.")

except Exception as e:
    print(f"Error: {e}")
