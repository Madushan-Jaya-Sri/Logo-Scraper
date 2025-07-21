import re
import pandas as pd
import logging
import random
import time
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
        search_query = f"{site_name} logo Dubai"
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
        
        # Step 6: Extract image URL from the popup
        try:
            image_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="Sva75c"]/div[2]/div[2]/div/div[2]/c-wiz/div/div[2]/div[1]'))
            )
            logging.info("Image element in popup detected.")
            
            # Use JavaScript to get the image src
            logo_url = driver.execute_script("""
                var image = arguments[0];
                var img = image.querySelector('img');
                if (img && img.src) {
                    return img.src;
                }
                return null;
            """, image_element)
            
            if logo_url and logo_url.startswith("http"):
                logging.info(f"Extracted logo URL from image element: {logo_url}")
                return logo_url
            else:
                logging.error("Invalid or missing URL from image element. Content: %s", logo_url)
                return None
        except Exception as e:
            logging.error(f"Failed to extract image URL: {e}")
            driver.save_screenshot(f"error_image_extract_{site_name}.png")
            with open(f"page_source_image_extract_{site_name}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
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
        "https://www.almayyak9.com",
        "https://www.sniffmiddleeast.com",
        "https://www.uaelittleangels.com",
        "https://www.mussafahdogproject.com",
        "https://www.parauae.org",
        "https://www.emiratesrc.ae",
        "https://www.dubaicares.ae",
        "https://www.volunteers.ae",
        "https://www.greenpeace.org/mena",
        "https://www.emiratesnaturewwf.ae",
        "https://www.zayedfoundation.ae",
        "https://www.aljalilafoundation.ae",
        "https://www.noordubai.ae",
        "https://www.happinessportal.dubai.ae",
        "https://www.smartdubai.ae",
        "https://www.dwe.gov.ae",
        "https://www.uaefoodbank.ae",
        "https://www.eaws.ae",
        "https://www.gulf4good.org",
        "https://www.expatechodubai.com",
        "https://www.dubaipetfood.com",
        "https://www.thepetshop.ae",
        "https://www.petcorner.ae",
        "https://www.petsdelight.com",
        "https://www.petskyonline.com",
        "https://www.thecatcafedubai.com",
        "https://www.kittysnipuae.com",
        "https://www.petfirst.ae",
        "https://www.petshabitat.com",
        "https://www.petmania.ae",
        "https://www.noon.com/uae-en/pet-supplies",
        "https://www.amazon.ae/pet-supplies",
        "https://www.happypaws.ae",
        "https://www.petsoasis.ae",
        "https://www.felinefriendsdubai.com",
        "https://www.thevetstore.ae",
        "https://www.dubaipetfood.com",
        "https://www.thepetshop.ae",
        "https://www.petcorner.ae",
        "https://www.k9friends.com",
        "https://www.petsdelight.com",
        "https://www.petskyonline.com",
        "https://www.petfirst.ae",
        "https://www.petshabitat.com",
        "https://www.unleashdubai.com",
        "https://www.dogwalk.ae",
        "https://www.noon.com/uae-en/pet-supplies",
        "https://www.amazon.ae/pet-supplies",
        "https://www.happypaws.ae",
        "https://www.petsoasis.ae",
        "https://www.redpawfoundation.org",
        "https://www.thevetstore.ae",
        "https://gulfnews.com/technology",
        "https://www.khaleejtimes.com/technology",
        "https://www.techradar.com",
        "https://www.emiratestech.com",
        "https://www.stuff.tv",
        "https://www.t3.com",
        "https://www.gadgetsmiddleeast.com",
        "https://www.thenationalnews.com/tech",
        "https://www.arabianbusiness.com/industries/technology",
        "https://www.uaetechpodcast.com",
        "https://www.dubaitechnews.com",
        "https://www.techmagazine.ae",
        "https://whatson.ae/category/tech",
        "https://www.esquireme.com/tech",
        "https://www.techbit.me",
        "https://www.dsoa.ae",
        "https://www.smartdubai.ae",
        "https://www.dic.ae",
        "https://www.du.ae",
        "https://www.etisalat.ae",
        "https://www.eitc.ae",
        "https://www.careem.com",
        "https://www.noon.com",
        "https://www.amazon.ae",
        "https://gulfnews.com/technology",
        "https://www.khaleejtimes.com/technology",
        "https://www.arabianbusiness.com/industries/technology",
        "https://www.dubaifuture.ae",
        "https://www.uaetechpodcast.com",
        "https://www.techmagazine.ae",
        "https://www.emiratestech.com",
        "https://www.dubaitechnews.com",
        "https://www.visitdubai.com",
        "https://www.dubaitourism.gov.ae",
        "https://www.raynatours.com",
        "https://www.arabian-adventures.com",
        "https://www.desertsafaridubai.com",
        "https://dubaitravelblog.com",
        "https://www.dnatatravel.com",
        "https://www.musafir.com",
        "https://www.seawings.ae",
        "https://www.platinum-heritage.com",
        "https://www.dubaiadventures.com",
        "https://www.orienttours.ae",
        "https://whatson.ae/category/travel",
        "https://www.emiratesholidays.com",
        "https://www.dubaicitytours.ae",
        "https://www.gulfventures.com",
        "https://www.dubaisc.ae",
        "https://www.fitnessfirst.ae",
        "https://www.goldsgym.ae",
        "https://www.dubaigolf.com/emirates-golf-club",
        "https://www.dubaimarinayachtclub.com",
        "https://www.dubaisportsworld.ae",
        "https://www.uaecycling.ae",
        "https://www.dubaifitnesschallenge.com",
        "https://www.fitrepublik.com",
        "https://www.tribefit.com",
        "https://www.paddledxb.com",
        "https://www.dubairun.com",
        "https://whatson.ae/category/sports",
        "https://sport360.com",
        "https://www.emiratescricket.com",
        "https://www.dubaitennischampionships.com",
        "https://www.visitdubai.com",
        "https://www.raynatours.com",
        "https://www.arabian-adventures.com",
        "https://www.desertsafaridubai.com",
        "https://www.dubaiadventures.com",
        "https://www.platinum-heritage.com",
        "https://www.seawings.ae",
        "https://www.xclusiveyachts.com",
        "https://www.herodysea.com",
        "https://www.theyellowboats.com",
        "https://www.skydivedubai.ae",
        "https://www.deepdivedubai.com",
        "https://www.hattaadventures.com",
        "https://www.ddcr.org",
        "https://whatson.ae/category/adventures",
        "https://www.kitensoul.com",
        "https://www.fujairahadventurepark.com",
        "https://www.tealand.ae",
        "https://www.thefeelgoodtea.co",
        "https://www.fillicafe.com",
        "https://www.teabreakcafe.com",
        "https://www.dubaiteacentre.ae",
        "https://www.arabianteahouse.com",
        "https://www.taniasteahouse.com",
        "https://www.noon.com/uae-en/tea",
        "https://www.amazon.ae/tea",
        "https://www.emiratestea.com",
        "https://www.karakhouse.ae",
        "https://www.projectchaiwala.com",
        "https://www.dilmahtea.ae",
        "https://www.twgtea.com",
        "https://www.ronnefeldt.com",
        "https://www.dmcc.ae",
        "https://www.nightjar.coffee",
        "https://www.southpour.ae",
        "https://www.amongstfew.com",
        "https://www.cassette.ae",
        "https://www.comptoir102.com",
        "https://www.eatx.com",
        "https://www.deliziegourmet.com",
        "https://www.thelimetreecafe.com",
        "https://www.tomandserg.com",
        "https://www.roseleafcafe.com",
        "https://www.kaffebloom.com",
        "https://www.rawcoffeecompany.com",
        "https://www.noon.com/uae-en/coffee",
        "https://www.amazon.ae/coffee",
        "https://www.mokha1450.com"
    ]
    
    result_df = main(website_urls)
    result_df.to_csv("logo_urls.csv", index=False)
    print("\nFinal Results:")
    print(result_df)