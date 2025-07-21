import re
import pandas as pd
import logging
import random
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_site_name(url):
    url = re.sub(r'^https?://', '', url)
    if url.startswith('www.'):
        url = url[4:]
        match = re.match(r'([^.]+)\.', url)
        if match:
            return match.group(1)
    match = re.match(r'([^.]+)\.', url)
    if match:
        return match.group(1)
    return None

def is_recaptcha_present(driver):
    try:
        driver.find_element(By.ID, "recaptcha")
        return True
    except:
        return False

def wait_for_recaptcha_solved(driver):
    logging.info("Checking for reCAPTCHA...")
    while is_recaptcha_present(driver):
        logging.info("reCAPTCHA detected. Please solve the reCAPTCHA manually and press Enter in the terminal to continue.")
        input("Press Enter after solving reCAPTCHA...")
        time.sleep(1)
    logging.info("reCAPTCHA solved or not present.")

def get_logo_url(driver, site_name):
    try:
        # Step 1: Search Google for 'site_name + logo'
        search_query = f"{site_name} logo"
        logging.info(f"Searching Google for: {search_query}")
        driver.get("https://www.google.com")
        
        # Step 2: Handle reCAPTCHA manually
        wait_for_recaptcha_solved(driver)
        
        # Enter search query
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(search_query)
        time.sleep(random.uniform(0.5, 1.5))
        search_box.send_keys(Keys.RETURN)
        
        # Step 3: Switch to Images tab
        try:
            images_tab = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="hdtb-sc"]/div/div/div[1]/div/div[2]/a/div'))
            )
            time.sleep(random.uniform(0.3, 1.0))
            ActionChains(driver).move_to_element(images_tab).click().perform()
            logging.info("Switched to Images tab via click")
        except Exception as e:
            logging.warning(f"Failed to click Images tab: {e}. Attempting direct URL navigation...")
            current_url = driver.current_url
            parsed_url = urllib.parse.urlparse(current_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            query_params['tbm'] = 'isch'
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            new_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
            driver.get(new_url)
            logging.info("Switched to Images tab via URL")
        
        # Step 4: Prompt user to select an image
        logging.info("Please manually click an image from the search results to load it in the popup window.")
        print(f"For {site_name}: Please click an image in the browser, then press Enter in the terminal to continue.")
        input("Press Enter after selecting an image...")
        
        # Step 5: Wait for the popup window
        try:
            # Wait for the popup window with class 'RfPPs vYoxve'
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".RfPPs.vYoxve"))
            )
            logging.info("Popup window with class 'RfPPs vYoxve' detected.")
        except Exception as e:
            logging.error(f"Failed to detect popup window: {e}")
            driver.save_screenshot(f"error_popup_{site_name}.png")
            with open(f"page_source_{site_name}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return None
        
        # Step 6: Wait for the three-dot menu
        try:
            three_dot_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="Sva75c"]/div[2]/div[2]/div/div[2]/c-wiz/div/div[1]/div/div[2]/div[1]/button'))
            )
            logging.info("Three-dot menu detected.")
        except Exception as e:
            logging.error(f"Failed to find three-dot menu: {e}")
            driver.save_screenshot(f"error_three_dot_{site_name}.png")
            with open(f"page_source_{site_name}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return None
        
        # Step 7: Click three-dot menu and select "Share" then "Click to copy link"
        try:
            # Click the three-dot menu
            ActionChains(driver).move_to_element(three_dot_button).click().perform()
            time.sleep(0.5)
            
            # Click "Share" option
            share_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="Sva75c"]/div[2]/div[2]/div/div[2]/c-wiz/div/div[1]/div/div[2]/div[1]/div/div[3]'))
            )
            logging.info("Share option detected.")
            ActionChains(driver).move_to_element(share_option).click().perform()
            time.sleep(0.5)
            
            # Wait for the new popup with ID 'DDeXhf'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "DDeXhf"))
            )
            logging.info("New popup with ID 'DDeXhf' detected.")
            
            # Click "Click to copy link" within the new popup
            try:
                # Try a more flexible selector for "Click to copy link"
                copy_link_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@id='DDeXhf']//div[contains(text(), 'Click to copy link')]"))
                )
                logging.info("Click to copy link button detected.")
                logging.info(f"Button HTML: {copy_link_button.get_attribute('outerHTML')}")
                
                # Use JavaScript to click the element to bypass Selenium interaction issues
                driver.execute_script("arguments[0].click();", copy_link_button)
                logging.info("Clicked 'Click to copy link' using JavaScript.")
                time.sleep(2)  # Increased wait time for clipboard to update
                
                # Retry mechanism in case the first click fails
                retries = 3
                logo_url = None
                for attempt in range(retries):
                    logo_url = pyperclip.paste()
                    if logo_url and logo_url.startswith("http"):
                        logging.info(f"Extracted logo URL from clipboard: {logo_url}")
                        return logo_url
                    logging.warning(f"Retry {attempt + 1}/{retries}: Clipboard content not valid. Content: {logo_url}")
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", copy_link_button)
                    time.sleep(2)
                
                logging.error("Failed to copy URL after retries. Final clipboard content: %s", logo_url)
                return None
            except Exception as e:
                logging.error(f"Failed to click 'Click to copy link': {e}")
                # Log all elements in DDeXhf that might match the text
                try:
                    potential_elements = driver.find_elements(By.XPATH, "//div[@id='DDeXhf']//div[contains(text(), 'Click to copy')]")
                    if potential_elements:
                        logging.info("Potential matching elements found:")
                        for elem in potential_elements:
                            logging.info(f"Element HTML: {elem.get_attribute('outerHTML')}")
                    else:
                        logging.info("No potential matching elements found in DDeXhf.")
                except Exception as log_e:
                    logging.error(f"Failed to log potential elements: {log_e}")
                driver.save_screenshot(f"error_copy_link_{site_name}.png")
                with open(f"page_source_copy_link_{site_name}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                return None
        except Exception as e:
            logging.error(f"Failed to get image URL via share menu: {e}")
            driver.save_screenshot(f"error_url_click_{site_name}.png")
            return None
    
    except Exception as e:
        logging.error(f"Error in get_logo_url for {site_name}: {e}")
        driver.save_screenshot(f"error_{site_name}.png")
        return None

def main(website_urls):
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        """
    })
    
    results = []
    
    try:
        for url in website_urls:
            logging.info(f"Processing {url}")
            
            site_name = extract_site_name(url)
            if not site_name:
                logging.error(f"Could not extract site name from {url}")
                results.append({"Website": url, "Logo_URL": None})
                continue
            
            logo_url = get_logo_url(driver, site_name)
            results.append({"Website": url, "Logo_URL": logo_url})
            logging.info(f"Logo URL for {site_name}: {logo_url}")
            time.sleep(random.uniform(1.0, 3.0))
        
        df = pd.DataFrame(results)
        return df
    
    finally:
        driver.quit()
        logging.info("Browser closed")

if __name__ == "__main__":
    website_urls = [
        "https://www.google.com",
        "https://facebook.com",
        "https://www.linkedin.com",
        "https://somename.ae",
        "https://digitalgravity.ae"
    ]
    
    result_df = main(website_urls)
    result_df.to_csv("logo_urls.csv", index=False)
    print("\nFinal Results:")
    print(result_df)