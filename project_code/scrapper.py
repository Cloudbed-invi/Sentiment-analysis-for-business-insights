#imports 
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import pandas as pd
from tqdm import tqdm
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to handle CAPTCHA detection and wait for it to be solved manually
def wait_for_captcha_to_be_solved(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'captchacharacters'))  # ID used by Amazon CAPTCHA
        )
        print("CAPTCHA detected! Please solve the CAPTCHA manually.")
        
        # Wait until CAPTCHA disappears
        WebDriverWait(driver, 300).until_not(
            EC.presence_of_element_located((By.ID, 'captchacharacters'))
        )
        print("CAPTCHA solved. Resuming scraping...")
    
    except Exception:
        pass  # CAPTCHA not found, continue as normal

# Function to process amazon reviews (same logic, kept as is)
def amazon(url, filter_type):
    names, titles, ratings, contents = [], [], [], []
    i = 1
    max_pages = 10  # Limit to 10 pages for Amazon

    while i <= max_pages:
        modified_url = f"{url}&reviewerType=avp_only_reviews&pageNumber={i}&filterByStar={filter_type}"
        tqdm.write(f"Fetching URL: {modified_url}")
        driver.get(modified_url)

        wait_for_captcha_to_be_solved(driver)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        reviews = soup.find_all('div', {'data-hook': 'review'})

        if not reviews:
            tqdm.write(f"No reviews found for {filter_type.capitalize()} Reviews - Page {i}")
            break

        for review in reviews:
            name = review.find('span', {'class': 'a-profile-name'}).text.strip()
            title = review.find('a', {'data-hook': 'review-title'})
            title = title.text.strip() if title else "No title"
            title = title.split('stars')[1].strip()
            content = review.find('span', {'data-hook': 'review-body'}).text.strip()
            rating = review.find('span', {'class': 'a-icon-alt'}).text.split(' out of ')[0].strip()

            names.append(name)
            titles.append(title)
            ratings.append(float(rating))
            contents.append(content)

        url_check = soup.find('li', {'class': 'a-last'})
        if url_check is None:
            break

        i += 1

    return names, titles, ratings, contents

# Updated function to process Flipkart reviews using the correct selectors
def flipkart(url, filter_type):
    names, titles, ratings, contents = [], [], [], []
    max_pages = 20  # Limit to 20 pages for Flipkart
    page_counter = 1

    while page_counter <= max_pages:
        modified_url = f"{url}&aid=overall&certifiedBuyer=true&page={page_counter}&sortOrder={filter_type}"
        tqdm.write(f"Fetching URL: {modified_url}")
        driver.get(modified_url)

        wait_for_captcha_to_be_solved(driver)
        time.sleep(2)  # Increase sleep time to ensure the content loads properly

        # Parse the page using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        reviews = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG'})  # Correct structure for reviews

        if not reviews or len(reviews) == 0:
            tqdm.write(f"No reviews found for {filter_type.capitalize()} Reviews - Page {page_counter}")
            break

        for review in reviews:
            name = review.find('p', {'class': '_2NsDsF AwS1CA'}).text.strip()
            rating_element = review.find('div', {'class': 'XQDdHH'})
            if rating_element:
                rating_text = rating_element.text.strip()
                try:
                    rating = float(rating_text)
                except ValueError:
                    rating = None  # Handle cases where rating is not a number
            else:
                rating = None  # Handle missing rating
            title = review.find('p', {'class': 'z9E0IG'}).text.strip()
            content = review.find('div', {'class': 'ZmyHeo'}).text.strip()

            # Store the scraped data
            names.append(name)
            titles.append(title)
            ratings.append(rating)
            contents.append(content)

        page_counter += 1  # Move to the next page

    return names, titles, ratings, contents



# Function to determine site (Amazon or Flipkart) based on URL
def detect_site(url):
    if "amazon" in url:
        return "amazon"
    elif "flipkart" in url:
        return "flipkart"
    else:
        return None

# Main script starts here
driver = webdriver.Chrome()

# Get URL and automatically detect site (Amazon/Flipkart)
url = input("Enter the product link: ")
site = detect_site(url)

if site == "amazon":
    modified_url = url.replace("/dp/", "/product-reviews/")
    tqdm.write("Starting to scrape critical reviews...")
    critical_names, critical_titles, critical_ratings, critical_contents = amazon(modified_url, 'critical')
    tqdm.write("Starting to scrape positive reviews...")
    positive_names, positive_titles, positive_ratings, positive_contents = amazon(modified_url, 'positive')

elif site == "flipkart":
    modified_url = url.replace("/p/", "/product-reviews/")
    tqdm.write("Starting to scrape critical reviews...")
    critical_names, critical_titles, critical_ratings, critical_contents = flipkart(modified_url, 'NEGATIVE_FIRST')
    tqdm.write("Starting to scrape positive reviews...")
    positive_names, positive_titles, positive_ratings, positive_contents = flipkart(modified_url, 'POSITIVE_FIRST')

else:
    print("Invalid URL. Please provide a valid Amazon or Flipkart product URL.")

# Save to dataframes and remove duplicates
df_critical = pd.DataFrame({
    'Name': critical_names,
    'Title': critical_titles,
    'Rating': critical_ratings,
    'Content': critical_contents
})

df_positive = pd.DataFrame({
    'Name': positive_names,
    'Title': positive_titles,
    'Rating': positive_ratings,
    'Content': positive_contents
})



df_all_reviews = pd.concat([df_critical, df_positive], ignore_index=True)
df_all_reviews.drop_duplicates(subset=['Name', 'Title', 'Content'], inplace=True)
df_all_reviews['Content'].replace('READ MORE', '')
df_all_reviews.to_csv(f"{site}_reviews.csv")
# Close the browser
driver.quit()

tqdm.write(f"Total reviews after removing duplicates: {df_all_reviews.shape[0]}")


