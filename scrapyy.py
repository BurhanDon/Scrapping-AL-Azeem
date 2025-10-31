import time
import requests
import json
import urllib.parse  # <-- 1. IMPORTED URLPARSER
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


def get_all_blog_urls(start_url):
    """
    Phase 1 & 2: Use Selenium to load all posts and
    BeautifulSoup to extract the URLs.
    --- NO CLICK LIMIT ---
    """
    print("Initializing Selenium to find all post URLs...")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(start_url)

    button_xpath = "//a[.//span[contains(text(), 'Load More')]]"
    load_more_button_selector = (By.XPATH, button_xpath)

    click_count = 0

    while True:
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(load_more_button_selector)
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", load_more_button
            )
            time.sleep(1)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(load_more_button_selector)
            )

            driver.execute_script("arguments[0].click();", load_more_button)
            click_count += 1
            print(f"Clicked 'Load More' {click_count} time(s)... waiting...")

            time.sleep(2)

        except (TimeoutException, NoSuchElementException):
            print(f"Button test complete. Clicks: {click_count}. All posts are loaded.")
            break
        except Exception as e:
            print(f"An error occurred while clicking: {e}")
            break

    print("Parsing all loaded URLs...")
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, "html.parser")

    blog_urls = []
    articles = soup.find_all("article", class_="elementor-post")

    for article in articles:
        link_tag = article.find("h4", class_="elementor-post__title").find("a")
        if link_tag and link_tag.get("href"):
            if link_tag["href"] not in blog_urls:
                blog_urls.append(link_tag["href"])

    print(f"Found {len(blog_urls)} unique blog post URLs after {click_count} clicks.")
    return blog_urls


# --- 2. THIS FUNCTION IS UPDATED ---
def scrape_post_content(url):
    """
    Phase 3: Scrape a single page. Detects if it's a
    product or a blog post and scrapes accordingly.
    NOW ALSO EXTRACTS THE CATEGORY FROM THE URL.
    """
    try:
        response = requests.get(url, headers={"User-Agent": "MyScraper/1.0"})
        if not response.ok:
            print(f"Failed to fetch {url}, status code: {response.status_code}")
            return None

        post_soup = BeautifulSoup(response.content, "html.parser")

        # Default values
        page_type = "unknown"
        title = "Title not found"
        image_url = "Image not found"
        content_html = "Content not found"
        category = "uncategorized"  # <-- NEW DEFAULT

        # --- NEW: Category Parsing Logic ---
        try:
            parsed_url = urllib.parse.urlparse(url)
            # e.g. /category/product-name/ -> ['category', 'product-name']
            path_parts = parsed_url.path.strip("/").split("/")

            # If path has more than one part, assume first is category
            if len(path_parts) > 1:
                category = path_parts[0]
        except Exception as e:
            print(f"Warning: Could not parse category for {url}. Error: {e}")
        # --- END NEW ---

        # --- Detection Logic ---
        product_title_tag = post_soup.find("h1", class_="product_title")
        blog_title_tag = post_soup.find("h1", class_="elementor-heading-title")

        if product_title_tag:
            # --- IT'S A PRODUCT ---
            page_type = "product"
            title = product_title_tag.get_text(strip=True)

            img_container = post_soup.find(
                "div", class_="woocommerce-product-gallery__wrapper"
            )
            if img_container:
                img_tag = img_container.find("img")
                if img_tag and img_tag.get("src"):
                    image_url = img_tag["src"]

            content_div = post_soup.find(
                "div", class_="woocommerce-product-details__short-description"
            )
            if content_div:
                content_html = str(content_div)

        elif blog_title_tag:
            # --- IT'S A BLOG ---
            page_type = "blog"
            title = blog_title_tag.get_text(strip=True)

            img_container = post_soup.find(
                "div", class_="elementor-widget-theme-post-featured-image"
            )
            if img_container:
                img_tag = img_container.find("img")
                if img_tag and img_tag.get("src"):
                    image_url = img_tag["src"]

            content_div = post_soup.find(
                "div", class_="elementor-widget-theme-post-content"
            )
            if content_div:
                content_html = str(content_div)

        else:
            print(f"Warning: Page type unknown for {url}")

        return {
            "url": url,
            "type": page_type,
            "category": category,  # <-- NEW FIELD ADDED
            "title": title,
            "featured_image_url": image_url,
            "content_html": content_html,
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def save_to_json(data, filename):
    """Saves the scraped data to a JSON file."""
    if not data:
        print("No data to save.")
        return

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully saved {len(data)} posts to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")


# --- Main execution (no change here) ---
if __name__ == "__main__":

    BLOG_GRID_URL = "https://alazeement.com/?s="
    OUTPUT_FILE = "scraped_data_FINAL.json"

    all_urls = get_all_blog_urls(BLOG_GRID_URL)

    if not all_urls:
        print("No URLs found. Exiting.")
    else:
        print(f"\n--- Starting Phase 3: Scraping {len(all_urls)} posts ---")

        all_blog_data = []
        for i, url in enumerate(all_urls):
            print(f"Scraping post {i+1}/{len(all_urls)}: {url}")
            data = scrape_post_content(url)
            if data:
                all_blog_data.append(data)

            time.sleep(0.5)

        print("\n--- Scraping Complete ---")
        save_to_json(all_blog_data, OUTPUT_FILE)
        print("\n--- Final Complete ---")
