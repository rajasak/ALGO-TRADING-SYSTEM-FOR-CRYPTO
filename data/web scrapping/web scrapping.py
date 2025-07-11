import requests
from bs4 import BeautifulSoup
import pandas as pd
import time




search_url = "https://www.flipkart.com/search?q=iphone+15"

response = requests.get(search_url)
soup = BeautifulSoup(response.text, "lxml")

products = soup.find_all("div", class_="yKfJKb row")

final_data = []

for product in products:
    
    name_tag = product.find("div", class_="KzDlHZ")
    product_name = name_tag.get_text(strip=True) if name_tag else ""

    
    price_tag = product.find("div", class_="Nx9bqj _4b5DiR")
    product_price = price_tag.get_text(strip=True) if price_tag else ""

    
    features_ul = product.find("ul", class_="G4BRas")
    features_text = []
    if features_ul:
        features = features_ul.find_all("li", class_="J+igdf")
        features_text = [li.get_text(strip=True) for li in features]

    
    product_link_tag = product.find_parent("a", class_="CGtC98")
    product_link = (
        "https://www.flipkart.com" + product_link_tag["href"]
        if product_link_tag
        else None
    )

    review_url = None
    if product_link:
        
        review_url = product_link.replace("/p/", "/product-reviews/").split("?")[0]

    review_data = []
    if review_url:
        
        for i in range(1, 100):
            url = f"{review_url}?page={i}"
            while True:
                try:
                    review_resp = requests.get(url, headers=headers, timeout=10)
                    review_soup = BeautifulSoup(review_resp.text, "lxml")

                    review_blocks = review_soup.find_all("div", class_="col EPCmJX Ma1fCG")
                    if review_blocks:
                        for block in review_blocks:
                            rating_tag = block.find("div", class_="XQDdHH Ga3i8K")
                            rating = rating_tag.text.strip() if rating_tag else "N/A"

                            title_tag = block.find("p", class_="z9E0IG")
                            title = title_tag.text.strip() if title_tag else "No Title"

                            text_block = block.find("div", class_="ZmyHeo")
                            review_text = (
                                text_block.find("div").text.strip()
                                if text_block and text_block.find("div")
                                else "No Review Text"
                            )

                            review_data.append((rating, title, review_text))
                        break  
                    else:
                        
                        time.sleep(2)
                except Exception as e:
                    
                    time.sleep(2)

    
    if review_data:
        for r in review_data:
            row = [product_name, product_price] + features_text[:5] + list(r)
            final_data.append(row)
    else:
        row = [product_name, product_price] + features_text[:5] + ["No Rating", "No Title", "No Review"]
        final_data.append(row)


max_columns = max(len(row) for row in final_data)
base_columns = ["Product Name", "Price", "ROM", "Display", "Camera", "Processor", "Warranty"]
review_columns = ["Rating", "Review Title", "Review Text"]
fill_columns = base_columns + review_columns
while len(fill_columns) < max_columns:
    fill_columns.append(f"Extra {len(fill_columns) - len(base_columns) + 1}")


for row in final_data:
    while len(row) < len(fill_columns):
        row.append("")

df = pd.DataFrame(final_data, columns=fill_columns)
df.to_csv("iphone 15 review dataset.csv", index=True, encoding="utf-8-sig")

