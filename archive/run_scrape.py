from scraper import scrape_reviews
url = 'https://www.flipkart.com/goboult-loop2-10mm-drivers-boomx-rich-bass-in-line-controls-wired/p/itmd46f3db3aa77c?pid=ACCGHBHQ6UC3XT7U&lid=LSTACCGHBHQ6UC3XT7USDMLM2&marketplace=FLIPKART&q=boult+audio+wired&store=0pm%2Ffcn%2F821&srno=s_1_3&otracker=search&otracker1=search&fm=Search&iid=c38a0ffd-d756-4f2d-bd91-33b44cba485d.ACCGHBHQ6UC3XT7U.SEARCH&ppt=sp&ppn=sp&qH=7aceb0bc526bc6ab'
print('Starting scrape for URL:')
print(url)
result = scrape_reviews(url)
print('Scrape result:')
print(result)
