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

def get_product_links(driver, category_name):
    try:
        waitting_time = 0
        # Get all product links on the page
        product_links = []
        while True:
            try:
                product_container = driver.find_elements(By.CSS_SELECTOR, ".Bm3ON")
                # lấy id sản phẩm
                for container in product_container:
                    try:
                        produc_id = container.get_attribute("data-item-id")
                        
                    except NoSuchElementException:
                        print("No ID found for this product.")
        
                    saled_amount = 0
                    # Update the saled_amount parsing logic to handle unexpected formats
                    try:
                        saled_amount = container.find_element(By.CSS_SELECTOR, "._1cEkb")
                        saled_amount = saled_amount.find_elements(By.TAG_NAME, "span")[0].text
                        saled_amount = saled_amount.strip().replace("Đã bán", "").replace(".", "").replace(",", "").replace(" ", "")
                        saled_amount = saled_amount.replace("K", "000").replace("M", "000000")
                        saled_amount = int(saled_amount)  # Convert to integer after cleanup
                    except (NoSuchElementException, ValueError):
                        saled_amount = 0  # Default to 0 if parsing fails
                    display_price = container.find_element(By.CSS_SELECTOR, ".ooOxS")
                    # Lấy giá hiển thị
                    display_price = display_price.text
                    # Lấy giá gốc
                    display_price = display_price.replace("₫", "").replace(".", "").replace(",", "").replace(" ", "")
                    display_price = int(display_price)  # Convert to integer after cleanup
                    
                    tittle_element = container.find_element(By.CSS_SELECTOR, ".RfADt")
                    a_tags = tittle_element.find_element(By.TAG_NAME, "a")
                    product = {
                        "id": produc_id, 
                        "link": a_tags.get_attribute("href"),
                        "name": a_tags.get_attribute("title"), 
                        "display_price": display_price,
                        "saled_amount": saled_amount, 
                        "category": category_name
                    }
                    product_links.append(product)
                    
                break  # Exit loop if no exception occurs
            except StaleElementReferenceException:
                print("Stale element detected. Retrying...")
                waitting_time += 1
                if waitting_time > 20:
                    print("Max retries reached. Exiting...")
                    break
                time.sleep(1)  # Wait briefly before retrying
        return product_links
    except Exception as e:
        print(f"Error getting product links: {e}")
        return []


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

# Ensure driver and links are properly initialized
if __name__ == "__main__":
    product_links = []  # Danh sách dùng chung giữa các luồng

    # Tạo luồng crawl chi tiết sản phẩm
    # detail_thread = threading.Thread(target=crawl_product_details, args=(product_links,))
    # detail_thread.daemon = True  # Đảm bảo luồng phụ dừng khi luồng chính kết thúc
    # detail_thread.start()
    # mở file chứa danh sách các link danh mục đã crawl
    crawled_category = []
    with open('data/crawled.csv', mode='r', encoding='utf-8') as file:
        lines = file.readlines()
        crawled_category = [line.strip() for line in lines[1:]]  # Skip header

    driver = webdriver.Edge()
    with open('data/category.csv', mode='r', encoding='utf-8') as file:
        lines = file.readlines()
        links = [line.strip() for line in lines[1:]]  # Skip header

    try:
        for link in links:
            if link in crawled_category:
                print(f"Category {link} has already been crawled. Skipping...")
                continue
            driver.get(link)
            # nếu tìm thấy element error-page-title thì skip category này
            try:
                error_page = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".error-page-title"))
                )
                print(f"Category {link} is blocked. Skipping...")
                continue
            except NoSuchElementException:
                print(f"Category {link} is accessible.")
            
            category_name = link.split("/")[-1]  # Lấy tên danh mục từ link

            time.sleep(random.uniform(2, 5))  # Random thời gian dừng để tránh bị phát hiện là bot nhầm né capcha
            while True:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".RfADt"))
                    )
                    new_product_links = get_product_links(driver, category_name)
                    product_links.extend(new_product_links)
                    with open('data/lazada/product_links.csv', mode='a', newline='', encoding='utf-8') as file:
                        # Kiểm tra nếu file rỗng thì ghi tiêu đề
                        if file.tell() == 0:
                            writer = csv.writer(file)
                            writer.writerow(["id", "link", "product_name", "display_price", "saled_amount", "category"])
                        writer = csv.writer(file)
                        for product_link in new_product_links:
                            writer.writerow([
                                product_link.get("id"),
                                product_link.get("link"),
                                product_link.get("name"),
                                product_link.get("display_price"),
                                product_link.get("saled_amount"),
                                product_link.get("category")
                            ])
                        file.flush()
                    print("Product links have been saved to data/product.csv.")
                    # Kiểm tra nếu nút next bị disable thì break
                    if driver.find_elements(By.CSS_SELECTOR, ".ant-pagination-next.ant-pagination-disabled"):
                        print("Reached last page. Ending pagination.")
                        break
                    xem_them_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-pagination-next"))
                    )
                    xem_them_button.find_element(By.TAG_NAME, "button").click()
                except NoSuchElementException:
                    print("No more 'Xem thêm' button found. Ending pagination.")
                    break
                except Exception as e:
                    print(f"Error during pagination: {e}")
                    action = wait_for_captcha_or_error(e)
                    if action == 'skip':
                        print("Bỏ qua danh mục này.")
                        break
                    # Nếu retry thì tiếp tục vòng lặp (không break)
    finally:
        driver.quit()