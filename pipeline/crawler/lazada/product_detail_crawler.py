import csv
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
from selenium.webdriver.edge.options import Options
import random
import time
import json
import html2text  # Thư viện hỗ trợ chuyển HTML sang Markdown


def get_price(driver):
    price_container = driver.find_element(By.CSS_SELECTOR, ".pdp-v2-product-price-content")
    price_display = price_container.find_elements(By.TAG_NAME, "div")
    sale_price = price_display[0].find_element(By.CSS_SELECTOR, ".pdp-v2-product-price-content-salePrice-amount").text
    # khử kí tự không cần thiết
    sale_price = (int)(sale_price.replace("₫", "").replace(".", "").replace(",", ""))

    original_price = sale_price.copy()

    discoutn = 0
    
    if len(price_display) > 1:
        span_discount = price_display[1].find_element(By.CSS_SELECTOR, ".pdp-v2-product-price-content-originalPrice").find_elements(By.TAG_NAME, "span")
        original_price = span_discount[0].text
        # khử kí tự không cần thiết
        original_price = (int)(original_price.replace("₫", "").replace(".", "").replace(",", "").replace(" ", ""))
        discoutn = (int)(span_discount[0].text.replace("-", "").replace("%", ""))
    return {
        "sale_price": sale_price,
        "original_price": original_price,
        "discount": discoutn
    }




# Function to simulate user behavior
def simulate_user_behavior(driver):
    actions = ActionChains(driver)
    actions.move_by_offset(random.randint(0, 100), random.randint(0, 100)).perform()  # Random mouse movement
    time.sleep(random.uniform(0.5, 2))  # Random delay
    driver.execute_script("window.scrollBy(0, arguments[0]);", random.randint(100, 500))  # Random scroll


# Enhanced WebDriver initialization with compatibility options and error handling
if __name__ == "__main__":
    product_links = []  # Shared list between threads

    link = "https://www.lazada.vn/products/kem-chong-nang-sunplay-cuc-manh-dang-sua-sunplay-super-block-spf-81-pa-30g-i101087289-s101255853.html/"
    try:
        waitting_time = 0
        
        try:
            # WebDriver setup with enhanced options
            options = Options()
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--ignore-ssl-errors")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--remote-debugging-port=9222")

            # Set a fixed User-Agent for desktop rendering
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            options.add_argument(f'user-agent={user_agent}')

            # Initialize WebDriver
            driver = webdriver.Edge(options=options)

            # Test WebDriver by loading a simple page
            driver.get("https://www.google.com")
            print("WebDriver initialized successfully.")

            # Navigate to the product link
            driver.get(link)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-mod-product-badge-title-v2"))
            )

            # Crawl product details (existing logic)
            product_name = driver.find_element(By.CSS_SELECTOR, ".pdp-mod-product-badge-title-v2").text
            review_score = driver.find_element(By.CSS_SELECTOR, ".container-star-v2-score").text
            review_count = 0
            if review_score > 0:
                review_score = driver.find_element(By.CSS_SELECTOR, ".pdp-link_size_m.pdp-link_theme_black_v2.pdp-review-summary-v2__link")\
                                    .find_element(By.TAG_NAME, "div")\
                                    .find_element(By.TAG_NAME, "span").text
            
            
            brand = ""
            try:
                brand = driver.find_element(By.CSS_SELECTOR, ".pdp-link_size_m pdp-link_theme_link_v2 pdp-product-brand-v2__brand-link").text
            except NoSuchElementException:
                brand = "N/A"
            description = ""
            try:
                description = driver.find_element(By.CSS_SELECTOR, ".pdp-product-detail-v2").get_attribute("innerHTML")
                # Chuyển đổi HTML sang Markdown
                html_to_md = html2text.HTML2Text()
                html_to_md.ignore_links = False  # Giữ lại các liên kết
                description = html_to_md.handle(description)
            except NoSuchElementException:
                description = "N/A"
            
            gallerys = driver.find_elements(By.CSS_SELECTOR, ".next-slick-track").find_elements(By.TAG_NAME, "div").size()

            seller_container = driver.find_element(By.CSS_SELECTOR, ".pdp-link_size_l pdp-link_theme_black seller-name-v2__detail-name")
            seller = {
                "name": seller_container.find_element(By.TAG_NAME, "span").text,
                "link": seller_container.get_attribute("href")
            }
            type_container = driver.find_element(By.CSS_SELECTOR, ".sku-prop-content sku-prop-content- sku-prop-content-selected ")
            type = type_container.find_elements(By.TAG_NAME, "div")
            types = []
            for i in range(len(type)):
                name = type[i].find_element(By.TAG_NAME, "span").text
                type[i].click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-v2-product-price-content"))
                )
                price = get_price(driver)
                types.append({
                    "name": name,
                    "sale_price": price["sale_price"],
                    "original_price": price["original_price"],
                    "discount": price["discount"],
                })
            reviews = []
            while True:
                if review_count == 0:
                    break
                try:
                    reviews_list = driver.find_element(By.CSS_SELECTOR, ".mod-reviews")
                    reviews = reviews_list.find_elements(By.TAG_NAME, "div")
                    for review in reviews:
                        try:
                            reviewer = review.find_element(By.CSS_SELECTOR, ".reviewer").text

                            review_score = review.find_element(By.CSS_SELECTOR, ".container-star review-star")\
                                .find_elements(By.TAG_NAME, "div")
                            review_score = review_score.filter \
                                (lambda x: x.get_attribute("src") == "//img.lazcdn.com/g/tps/tfs/TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png").size()
                            
                            review_content = review.find_element(By.CSS_SELECTOR, ".item-content-main-content-reviews-item")\
                                .find_element(By.TAG_NAME, "span").text
                            
                            reviews.append({
                                "reviewer": reviewer,
                                "review_score": review_score,
                                "review_content": review_content
                            })
                        except NoSuchElementException:
                            print("No review found for this product.")
                except NoSuchElementException:
                    print("No reviews found.")
                    break
                
                if review_count <= 5:
                    break
                try:
                    review_container = driver.find_element(By.CSS_SELECTOR, ".iweb-pagination-next")
                    review_container.find_element(By.TAG_NAME, "button").click()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".mod-reviews"))
                    )
                except NoSuchElementException:
                    print("No more reviews to load.")
                    break
            result = {
                "link": link,

                "product_name": product_name,
                "review_score": review_score,
                "description": description,
                "review_count": review_count,
                "brand": brand,
                "gallerys": gallerys,
                "seller": seller,
                "types": types,
                "reviews": reviews
            }

        except Exception as e:
            print(f"Error initializing WebDriver or navigating to the link: {e}")

    except Exception as e:
        print(f"Error crawling details for {link}: {e}")

    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Error closing WebDriver: {e}")
