from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import time
import csv


# Initialize the WebDriver
driver = webdriver.Edge()
# Open Lazada website
driver.get("https://www.lazada.vn/shop-portable-speakers-&-boomboxes/")

try:
    # Wait for the page to load
    time.sleep(3)
    # Hover over the Danh Muc
    danh_muc = driver.find_element(By.CSS_SELECTOR, ".lzd-site-menu-root") 
    

    # lấy danh sách các danh mục cha
    danh_muc_cha = danh_muc.find_elements(By.TAG_NAME, "ul")

    link_danh_muc = []
    for item in danh_muc_cha:
        try:
            # Lấy danh sách các danh mục con
            links = item.find_elements(By.TAG_NAME, "li")
            for li in links:
                a_tags = li.find_elements(By.TAG_NAME, "a")
                link_danh_muc.extend([a.get_attribute("href") for a in a_tags])
            print(link_danh_muc)
            try:
                uls = item.find_element(By.TAG_NAME, "ul")
                if uls:
                    # Lấy danh sách các danh mục con
                    sub_links = uls.find_elements(By.TAG_NAME, "li")
                    for sub_link in sub_links:
                        try:
                            # Lấy tên và link của danh mục con
                            links = sub_link.find_element(By.TAG_NAME, "a").get_attribute("href")
                            link_danh_muc.append(links)
                            print(links)
                        except Exception as e:
                            print(f"Error extracting subcategory: {e}")
                            continue
            except Exception as e:
                print(f"Error extracting subcategories: {e}")
                continue
        except Exception as e:
            print(f"Error extracting category: {e}")
            continue
    # xóa duplicate
    link_danh_muc = list(set(link_danh_muc))
    # Ghi vào file data/category.csv với header là 'link'
    with open('data/category.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['link'])  # Header
        for link in link_danh_muc:
            writer.writerow([link])

finally:
    # Close the WebDriver
    driver.quit()





