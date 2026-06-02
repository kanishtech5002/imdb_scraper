import os
import re
import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def resolve_chromedriver_path(wdm_path):
    """
    Given a path returned by webdriver-manager, resolves the actual path to chromedriver.exe.
    Handles bugs where webdriver-manager returns text files (like LICENSE or THIRD_PARTY_NOTICES)
    or directories instead of the executable.
    """
    if not wdm_path:
        return None
        
    # If the path already points to chromedriver.exe, we are good
    if wdm_path.lower().endswith("chromedriver.exe"):
        return wdm_path
        
    # Check if the returned path is a directory or a file
    base_dir = wdm_path if os.path.isdir(wdm_path) else os.path.dirname(wdm_path)
    
    # Check if chromedriver.exe exists in the same directory
    local_exe = os.path.join(base_dir, "chromedriver.exe")
    if os.path.exists(local_exe):
        return local_exe
        
    # Check in parent directories recursively
    current_dir = base_dir
    for _ in range(3): # Go up to 3 levels up
        if not current_dir or current_dir == os.path.dirname(current_dir):
            break
        # Walk down this directory to find chromedriver.exe
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.lower() == "chromedriver.exe":
                    return os.path.join(root, file)
        current_dir = os.path.dirname(current_dir)
        
    return wdm_path # Fallback to original

def get_chrome_driver():
    """
    Initializes and configures the Selenium Chrome WebDriver.
    Uses headless mode and optimized flags for reliable background execution.
    """
    logger.info("Initializing Chrome WebDriver...")
    chrome_options = Options()
    
    # Run in headless mode (no UI window shown)
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Crucial header settings: prevent IMDb from translating titles based on IP location
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en-US'})
    
    # Use WebDriver Manager to automatically download/match the ChromeDriver executable
    raw_driver_path = ChromeDriverManager().install()
    logger.info(f"WebDriver Manager returned path: {raw_driver_path}")
    
    # Resolve the actual path to chromedriver.exe to bypass the text file bug
    resolved_driver_path = resolve_chromedriver_path(raw_driver_path)
    logger.info(f"Resolved ChromeDriver path: {resolved_driver_path}")
    
    service = Service(resolved_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_imdb_top_250():
    """
    Scrapes the IMDb Top 250 movies list.
    
    Returns:
        list: A list of dictionaries, where each dictionary contains 'Rank', 'Title', 'Year', and 'Rating'.
    """
    url = "https://www.imdb.com/chart/top/"
    driver = None
    movies_data = []
    
    try:
        driver = get_chrome_driver()
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for the main list element container to load
        # In modern IMDb layouts, this is usually an ordered/unordered list representing the chart
        logger.info("Waiting for movie list elements to load...")
        wait = WebDriverWait(driver, 15)
        # Check for the list container
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ipc-metadata-list")))
        
        # Add a slight delay to allow client-side hydration (react state render) to settle
        time.sleep(2)
        
        # Extract page source and feed it to BeautifulSoup for ultra-fast local parsing
        # (This is significantly faster and more resource-efficient than Selenium's element selectors)
        logger.info("Retrieving page source for BeautifulSoup parsing...")
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Find all list item elements representing individual movies
        movie_items = soup.find_all("li", class_=lambda c: c and "ipc-metadata-list-summary-item" in c)
        
        if not movie_items:
            # Fallback selector just in case IMDb changes the list-item class
            logger.warning("Target class not found, trying fallback list item selectors...")
            movie_items = soup.select("ul.ipc-metadata-list > li")
            
        logger.info(f"Found {len(movie_items)} candidate movie elements on the page.")
        
        for item in movie_items:
            try:
                # 1. Extract Rank and Title from the heading element
                # Typically, modern IMDb heading class is 'ipc-title__text' or similar under a header/wrapper
                title_header = item.find("h3", class_=lambda c: c and "ipc-title__text" in c)
                if not title_header:
                    # Fallback heading search
                    title_header = item.find("h3")
                    
                if not title_header:
                    continue # Skip if no title header is present
                    
                header_text = title_header.get_text(strip=True)
                
                # Header text is usually like: "1. The Shawshank Redemption"
                # Let's extract rank and title using a robust regex match
                rank_title_match = re.match(r"^(\d+)\.\s*(.*)$", header_text)
                if rank_title_match:
                    rank = int(rank_title_match.group(1))
                    title = rank_title_match.group(2).strip()
                else:
                    # Fallback parsing in case the rank dot format is missing
                    rank = len(movies_data) + 1
                    title = header_text
                
                # 2. Extract Release Year from metadata item
                # Metadata block contains ul > li elements in modern IMDb layout
                metadata_container = item.find("div", class_=lambda c: c and "cli-title-metadata" in c)
                
                year = 0
                if metadata_container:
                    # Search for 'li' tags first (modern ul > li layout)
                    metadata_items = metadata_container.find_all("li")
                    if metadata_items:
                        year_text = metadata_items[0].get_text(strip=True)
                        if re.match(r"^\d{4}$", year_text):
                            year = int(year_text)
                            
                    # Fallback to spans if no li tags found
                    if not year:
                        metadata_spans = metadata_container.find_all("span")
                        if metadata_spans:
                            year_text = metadata_spans[0].get_text(strip=True)
                            if re.match(r"^\d{4}$", year_text):
                                year = int(year_text)
                
                # Robust fallback: extract any 4-digit number between 1900 and 2099 from the item text
                if not year:
                    item_text_with_spaces = item.get_text(" ", strip=True)
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", item_text_with_spaces)
                    if year_match:
                        year = int(year_match.group(1))

                
                # 3. Extract Rating
                # Rating is usually inside a span ending with 'ipc-rating-star--imdb'
                rating_span = item.find("span", class_=lambda c: c and "ipc-rating-star" in c)
                rating = 0.0
                if rating_span:
                    rating_text = rating_span.get_text(strip=True)
                    # Rating text might be "9.3" or "9.3 (2.9M)". We only want the float value.
                    rating_match = re.search(r"(\d+\.\d+)", rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Robust fallback for Rating
                if not rating:
                    rating_match = re.search(r"\b(\d\.\d)\b", item.get_text())
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Store the structured movie details
                movies_data.append({
                    "Rank": rank,
                    "Movie Title": title,
                    "Release Year": year,
                    "IMDb Rating": rating
                })
                
            except Exception as e:
                logger.error(f"Error parsing individual movie element: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Scraping failed with exception: {e}")
        raise e
    finally:
        if driver:
            logger.info("Closing Chrome WebDriver...")
            driver.quit()
            
    # Sort by Rank to ensure correct order
    movies_data = sorted(movies_data, key=lambda x: x["Rank"])
    
    # Safety check: IMDb is a Top 250 list.
    logger.info(f"Successfully scraped {len(movies_data)} movies.")
    return movies_data

if __name__ == "__main__":
    # Test runner for verification
    try:
        data = scrape_imdb_top_250()
        print(f"Scraped {len(data)} movies successfully!")
        if data:
            print("First movie details:", data[0])
            print("Last movie details:", data[-1])
    except Exception as err:
        print("Scraping failed:", err)
