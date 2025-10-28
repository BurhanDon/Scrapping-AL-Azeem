import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# --- THIS IS THE NEW, CORRECT SELECTOR ---
# It finds an <a> tag that has a descendant <span> with the text "Load More"
BUTTON_XPATH = "//a[.//span[contains(text(), 'Load More')]]"
BLOG_GRID_URL = 'https://alazeement.com/?s='

print("Initializing Selenium in non-headless mode...")

# Setup Chrome options
chrome_options = webdriver.ChromeOptions()
# We run non-headless to watch it work
# chrome_options.add_argument("--headless") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('--log-level=3')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(BLOG_GRID_URL)
print(f"Opened {BLOG_GRID_URL}. Watch the browser.")

click_count = 0
while True:
    try:
        print("\nSearching for 'Load More' button...")
        
        # 1. Wait for the button to exist anywhere on the page
        load_more_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, BUTTON_XPATH))
        )
        
        # 2. Scroll the button into view
        driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
        print("Button found. Scrolled to button.")
        
        # 3. Wait for it to be clickable (not obscured, etc.)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, BUTTON_XPATH))
        )
        
        # 4. Click it using JavaScript (most reliable)
        driver.execute_script("arguments[0].click();", load_more_button)
        click_count += 1
        print(f"Clicked button! (Total clicks: {click_count}).")
        
        # 5. Wait for new content to load
        print("Waiting 3 seconds for new content...")
        time.sleep(3) 
        
    except (TimeoutException, NoSuchElementException):
        print("\nButton test complete. 'Load More' button is no longer found.")
        break
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        break

print(f"\nTotal clicks performed: {click_count}. Closing browser.")
time.sleep(3)
driver.quit()