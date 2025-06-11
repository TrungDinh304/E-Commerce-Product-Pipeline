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
from minio import Minio
import dotenv

dotenv.load_dotenv()


minio_client = Minio(
        "localhost:9000",
        access_key=dotenv.get("MINIO_ROOT_USER", "minioadmin"),
        secret_key=dotenv.get("MINIO_ROOT_PASSWORD", "minioadmin"),
        # Nếu MinIO chạy trên localhost, bạn có thể để secure=False
        secure=False
    )



def get_price(driver):

    try:
        price_container = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-product-price"))
        )
        
        # Lấy giá hiển thị
        sale_price = price_container.find_element(By.TAG_NAME, "span").text
        sale_price = sale_price.replace("₫", "").replace(".", "").replace(",", "").replace(" ", "")
        sale_price = int(sale_price) if sale_price else 0  # Convert to integer, default to 0 if empty
        
        original_price = sale_price
        discoutn = 0
        try:
            original_price_element = price_container.find_element(By.TAG_NAME, "div")

            spans = original_price_element.find_elements(By.TAG_NAME, "span")
            if spans:
                original_price = spans[0].text
                original_price = original_price.replace("₫", "").replace(".", "").replace(",", "").replace(" ", "")
                original_price = int(original_price) if original_price else 0

                discoutn_element = spans[1].text 
                discoutn_element = discoutn_element.replace("%", "").replace(" ", "").replace(",", "")
                discoutn = int(discoutn_element) if discoutn_element else 0


        except NoSuchElementException:
            print("No original price found, using sale price as original price.")
            original_price = sale_price
            discoutn = 0

        
        return {
            "sale_price": sale_price,
            "original_price": original_price,
            "discount": discoutn
        }
    except NoSuchElementException as e:
        print(f"Error during pagination: {e}")

    except Exception as e:
        print(f"Error during pagination: {e}")
    
    return {
        "sale_price": None,
        "original_price": None,
        "discount": None
    }
        
    

def wait_for_captcha_or_error(error=None):
    print("\n[!] Đã gặp lỗi hoặc captcha!")
    if error:
        print(f"Chi tiết lỗi: {error}")
    print("Chọn hành động:")
    print("  [Enter] để thử lại sau khi xử lý thủ công (ví dụ: giải captcha, reload trang, ...)")
    print("  [s] + Enter để bỏ qua danh mục này và sang danh mục tiếp theo")
    print("  [q] + Enter để dừng chương trình hoàn toàn")
    user_input = input("Nhập lựa chọn: ").strip().lower()
    if user_input == 's':
        return 'skip'
    elif user_input == 'q':
        print("Dừng chương trình theo yêu cầu người dùng.")
        exit(0)
    return 'retry'

def get_general_info(driver):
    try:
        # Chờ cho phần tử chứa thông tin chung xuất hiện
        name_wrapper = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-mod-product-badge-wrapper"))
        )
        
        # Lấy tên sản phẩm
        product_name = name_wrapper.find_element(By.TAG_NAME, "h1").text

        is_mall = False
        try:
            mall_badge = name_wrapper.find_element(By.TAG_NAME, "img")
            is_mall = True if mall_badge else False
        except NoSuchElementException:
            is_mall = False
        
        return {
            "product_name": product_name,
            "is_mall": is_mall
        }
    
    except Exception as e:
        print(f"Error finding general info elements: {e}")
         
def crawl_product_details_v2(driver, link, id):
    driver.get(link)
    while True:
        try:
            # Chờ cho trang tải xong và các phần tử cần thiết xuất hiện
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-mod-product-badge-wrapper"))
            )
            break  # Thoát vòng lặp nếu không có lỗi
        except Exception as e:
            print(f"Error loading page or elements: {e}")
            action = wait_for_captcha_or_error(e)
            if action == 'skip':
                return None
            elif action == 'q':
                exit(0)
    try:
        # ==========================================Product Name and Mall Check==========================================

        # Chờ cho phần tử chứa thông tin chung xuất hiện
        name_wrapper = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-mod-product-badge-wrapper"))
        )
        # Lấy tên sản phẩm
        product_name = name_wrapper.find_element(By.TAG_NAME, "h1").text

        is_mall = False
        try:
            mall_badge = name_wrapper.find_element(By.TAG_NAME, "img")
            is_mall = True if mall_badge else False
        except NoSuchElementException:
            is_mall = False

        print(f"Product Name: {product_name}, Is Mall: {is_mall}")
        # ==========================================Price and Discount==========================================
        price_container = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-product-price"))
        )
        # Lấy giá hiển thị
        sale_price = price_container.find_element(By.TAG_NAME, "span").text
        sale_price = sale_price.replace("₫", "").replace(".", "").replace(",", "").replace(" ", "")
        sale_price = int(sale_price) if sale_price else 0  # Convert to integer, default to 0 if empty
        
        original_price = sale_price
        discoutn = 0
        try:
            original_price_element = price_container.find_element(By.TAG_NAME, "div")

            spans = original_price_element.find_elements(By.TAG_NAME, "span")
            if spans:
                original_price = spans[0].text
                original_price = original_price.replace("₫", "").replace(".", "").replace(",", "").replace(" ", "")
                original_price = int(original_price) if original_price else 0

                discoutn_element = spans[1].text 
                discoutn_element = discoutn_element.replace("%", "").replace(" ", "").replace(",", "")
                discoutn = int(discoutn_element) if discoutn_element else 0


        except NoSuchElementException:
            print("No original price found, using sale price as original price.")
            original_price = sale_price
            discoutn = 0

        print(f"Sale Price: {sale_price}, Original Price: {original_price}, Discount: {discoutn}")
        # ==========================================Brand==========================================
        brand = ""
        try:
            brand_container = driver.find_element(By.CSS_SELECTOR, ".pdp-product-brand")
            brand_tag = brand_container.find_elements(By.TAG_NAME, "a")
            brand = brand_tag[0].text if brand_tag else "N/A"
        except NoSuchElementException:
            brand = "Nobrand"
        
        print(f"Brand: {brand}")

        # ==========================================Description==========================================
        description = ""
        try:
            description_container = driver.find_element(By.CSS_SELECTOR, ".html-content.detail-content")
            description = description_container.get_attribute("innerHTML")
        except NoSuchElementException:
            description = "N/A"
        except Exception as e:
            print(f"Error getting description: {e}")
            description = "N/A"
        
        print(f"Description: {description}...")  # In ra 100 ký tự đầu tiên của mô tả

        # # ==========================================Gallerys==========================================
        # gallerys = 0
        # try:
        #     gallery_container = driver.find_element(By.CSS_SELECTOR, ".next-slick-track")
        #     gallerys = len(gallery_container.find_elements(By.TAG_NAME, "div"))
        # except NoSuchElementException:
        #     gallerys = 1
        # # ==========================================Seller==========================================
        # seller = {}
        # try: 
        #     seller_container = driver.find_element(By.CSS_SELECTOR, ".seller-container")
        #     seller_name_container = seller_container.find_element(By.CSS_SELECTOR, ".seller-name__detail")
        #     seller_name = seller_name_container.find_element(By.TAG_NAME, "a").text
        #     seller_link = seller_name_container.find_element(By.TAG_NAME, "a").get_attribute("href")
        #     seller = {
        #         "name": seller_name,
        #         "link": seller_link
        #     }
        # except NoSuchElementException:
        #     seller = {
        #         "name": "N/A",
        #         "link": "N/A"
        #     }
        # # ==========================================Types==========================================
        # types = []
        # try:
        #     type_container = driver.find_element(By.CSS_SELECTOR, ".sku-prop-content sku-prop-content-")
        #     type_list = type_container.find_elements(By.TAG_NAME, "span")
        #     for i in range(len(type_list)):
        #         div_container = type_list[i].find_element(By.TAG_NAME, "div")
        #         div_container.click()

        #         type_name = WebDriverWait(driver, 10).until(
        #             EC.presence_of_element_located((By.CSS_SELECTOR, ".sku-name "))
        #         )
        #         price = get_price(driver)
        #         types.append({
        #             "name": type_name.text,
        #             "sale_price": price.get("sale_price"),
        #             "original_price": price.get("original_price"),
        #             "discount": price.get("discount"),
        #         })
        # except NoSuchElementException:
        #     print("No types found for this product.")
        #     type = []

        # # ==========================================review score and count==========================================
        # rating_container = WebDriverWait(driver, 20).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, ".mod-rating"))
        # )

        # review_score = rating_container.find_element(By.CSS_SELECTOR, ".score-average").text
        # review_count = rating_container.find_element(By.CSS_SELECTOR, ".count").text
        # review_count = review_count.replace("đánh giá", "")




        # # ==========================================Reviews==========================================

        # reviews = []

        # try:
        #     while True:
        #         if review_count == 0:
        #             break
        #         try:
        #             reviews_list = driver.find_element(By.CSS_SELECTOR, ".mod-reviews")
        #             reviews = reviews_list.find_elements(By.TAG_NAME, "div")
        #             for review in reviews:
        #                 try:
        #                     reviewer = review.find_element(By.CSS_SELECTOR, ".middle")
        #                     reviewer = reviewer.find_elements(By.TAG_NAME, "span")[0].text

        #                     # Lấy điểm đánh giá
        #                     review_score = review.find_elements(By.CSS_SELECTOR, ".star")
        #                     review_score = review_score.filter \
        #                         (lambda x: x.get_attribute("src") == "//img.lazcdn.com/g/tps/tfs/TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png").size()
                            
        #                     review_content = review.find_element(By.CSS_SELECTOR, ".content").text
                            
        #                     reviews.append({
        #                         "reviewer": reviewer,
        #                         "review_score": review_score,
        #                         "review_content": review_content
        #                     })
        #                 except NoSuchElementException:
        #                     print("No review found for this product.")
        #         except NoSuchElementException:
        #             print("No reviews found.")
        #             break
                
        #         if review_count <= 5:
        #             break
        #         try:
        #             review_container = driver.find_element(By.CSS_SELECTOR, ".iweb-pagination-next")
        #             review_container.find_element(By.TAG_NAME, "button").click()
        #             WebDriverWait(driver, 10).until(
        #                 EC.presence_of_element_located((By.CSS_SELECTOR, ".mod-reviews"))
        #             )
        #         except NoSuchElementException:
        #             print("No more reviews to load.")
        #             break
        # except NoSuchElementException:
        #     print("No reviews found for this product.")
        #     reviews = []

        # # ==========================================Return Result==========================================

        # return {
        #     "id": id,
        #     "link": link,
        #     "product_name": product_name,
        #     "is_mall": is_mall,
        #     "sale_price": sale_price,
        #     "original_price": original_price,
        #     "discount": discoutn,
        #     "review_score": review_score,
        #     "review_count": review_count,
        #     "brand": brand,
        #     "description": description,
        #     "gallerys": gallerys,
        #     "seller": seller,
        #     "types": types
        # }
    
    except NoSuchElementException as e:
        print(f"Error finding elements on the page: {e}")

        return None
    except Exception as e:
        print(f"Error initializing WebDriver or navigating to the link: {e}")
        return None

            


def save_to_minio(data, bucket_name, object_name):
    
    try:
        minio_client.put_object(
            bucket_name,
            object_name,
            data,
            len(data),
            content_type='application/json'
        )
        print(f"Data saved to MinIO bucket '{bucket_name}' with object name '{object_name}'")
    except Exception as e:
        print(f"Error saving data to MinIO: {e}")






if __name__ == "__main__":
    list_product_links = []
    # product_links schema: product_id,links,product_name,display_price,saled_amount,category

    with open('data/lazada/product_links.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            list_product_links.append({
                "id": row["product_id"],
                "link": row["links"],
                "product_name": row["product_name"],
                "display_price": row["display_price"],
                "saled_amount": row["saled_amount"],
                "category": row["category"]
            })
            # Set up WebDriver options
    driver = webdriver.Edge()
    
    for product in list_product_links:
        time.sleep(random.uniform(3, 5))

        link = product.get("link")
        print(f"Crawling details for product: {link}\n\n")
        
        driver.get(link)

        crawl_product_details_v2(driver, link, product.get("id"))
    



