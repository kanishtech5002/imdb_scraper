# IMDb Top 250 Movies Scraper - Comprehensive Report

## 1. Introduction

The **IMDb Top 250 Movies Scraper** is a Python-based web scraping application that automatically extracts the top 250 movies from IMDb's official chart and stores the data in a structured format. This project combines modern web scraping techniques with a user-friendly web interface to provide seamless access to movie data.

### Purpose
- Automate the collection of IMDb's top-rated movies
- Extract key movie information (rank, title, release year, and ratings)
- Store data in CSV format for analysis and further processing
- Provide a web dashboard for easy access and interaction

### Key Features
- **Automated Scraping**: Uses Selenium for dynamic page loading
- **Data Processing**: Leverages Pandas for data manipulation and statistics
- **Web Interface**: Flask-based dashboard for user interaction
- **Error Handling**: Comprehensive error management and logging
- **CSV Export**: Automatic data export functionality

---

## 2. Prerequisites

Before running this project, ensure you have:

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: Minimum 2 GB recommended
- **Internet Connection**: Required for accessing IMDb website

### Software Requirements
- **Python Package Manager**: pip (comes with Python)
- **Web Browser**: Google Chrome (required by Selenium)
- **Code Editor**: VS Code or any Python IDE (optional)

### Knowledge Requirements
- Basic understanding of Python programming
- Familiarity with command-line/terminal operations
- Basic knowledge of web scraping concepts

---

## 3. Technologies Used

### Backend Technologies
| Technology | Purpose | Version |
|---|---|---|
| **Flask** | Web framework for creating REST API | Latest |
| **Selenium** | Browser automation and dynamic content loading | 4.x |
| **BeautifulSoup4** | HTML parsing and data extraction | Latest |
| **Pandas** | Data processing and CSV generation | Latest |
| **WebDriver Manager** | Automatic ChromeDriver management | Latest |

### Frontend Technologies
| Technology | Purpose |
|---|---|
| **HTML5** | Page structure and layout |
| **CSS3** | Styling and responsive design |
| **JavaScript (ES6)** | Client-side interactivity |
| **Fetch API** | Asynchronous HTTP requests |

### Additional Tools
- **Chrome WebDriver**: Browser automation tool
- **Logging Module**: Error tracking and debugging
- **Regular Expressions (regex)**: Data pattern matching and extraction

---

## 4. Install Required Libraries

### Step 1: Set Up Virtual Environment (Recommended)
```bash
# Navigate to project directory
cd c:\Users\kanis\Desktop\imdb_scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually
pip install Flask
pip install selenium
pip install webdriver-manager
pip install pandas
pip install beautifulsoup4
```

### Step 3: Verify Installation
```bash
# Check if all packages are installed correctly
pip list
```

**Expected Output**: All packages should appear in the list with their versions.

---

## 5. Python Libraries Used

### 1. **Flask**
```python
from flask import Flask, render_template, jsonify, send_file
```
- **Purpose**: Lightweight web framework for building REST APIs
- **Key Functions**:
  - `Flask`: Initialize the application
  - `render_template`: Render HTML templates
  - `jsonify`: Convert Python data to JSON responses
  - `send_file`: Serve file downloads

### 2. **Selenium**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
```
- **Purpose**: Automate web browser interactions and handle dynamic content
- **Key Functions**:
  - `webdriver.Chrome()`: Initialize Chrome browser
  - `WebDriverWait()`: Wait for elements to load
  - `EC.presence_of_element_located()`: Check if element exists

### 3. **BeautifulSoup4**
```python
from bs4 import BeautifulSoup
```
- **Purpose**: Parse HTML and extract data efficiently
- **Key Functions**:
  - `find()`: Locate first matching element
  - `find_all()`: Locate all matching elements
  - `select()`: CSS selector-based element finding

### 4. **Pandas**
```python
import pandas as pd
```
- **Purpose**: Data manipulation, analysis, and CSV export
- **Key Functions**:
  - `DataFrame()`: Create tabular data structure
  - `to_csv()`: Export data to CSV file
  - `mean()`: Calculate average ratings
  - `idxmax()` / `idxmin()`: Find index of max/min values

### 5. **WebDriver Manager**
```python
from webdriver_manager.chrome import ChromeDriverManager
```
- **Purpose**: Automatically download and manage ChromeDriver
- **Key Functions**:
  - `install()`: Download compatible ChromeDriver version

### 6. **Logging Module**
```python
import logging
```
- **Purpose**: Track application flow and debug errors
- **Key Functions**:
  - `basicConfig()`: Configure logging
  - `getLogger()`: Create logger instance

### 7. **Regular Expressions (re)**
```python
import re
```
- **Purpose**: Extract patterns from text data
- **Key Functions**:
  - `match()`: Check pattern at string start
  - `search()`: Find pattern anywhere in string
  - `findall()`: Extract all matching patterns

---

## 6. Coding

### Project Architecture

```
imdb_scraper/
│
├── app.py                 # Flask application & API endpoints
├── scraper.py             # Web scraping logic
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web interface
├── static/
│   ├── style.css          # Styling
│   └── script.js          # Frontend JavaScript
└── downloads/
    └── imdb_top_250_movies.csv  # Exported data
```

### Core Components

#### **1. Scraper Module (scraper.py)**
Handles all web scraping operations:
- Initializes headless Chrome browser
- Navigates to IMDb Top 250 page
- Waits for dynamic content to load
- Parses HTML using BeautifulSoup
- Extracts movie data (rank, title, year, rating)
- Returns structured data list

#### **2. Flask Application (app.py)**
Provides REST API and web interface:
- `/` - Renders dashboard home page
- `/scrape` - Triggers scraping process and returns statistics
- `/download` - Serves CSV file download

#### **3. Frontend Files**
- `index.html` - Dashboard UI with buttons and data display
- `script.js` - Handles user interactions and API calls
- `style.css` - Responsive styling and layout

---

## 7. Step by Step Instructions

### Step 1: Import Required Modules

```python
# Flask imports for web framework
import os
import pandas as pd
from flask import Flask, render_template, jsonify, send_file

# Selenium imports for browser automation
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
```

**Explanation**:
- `Flask` modules: Build web application
- `Selenium` modules: Automate browser interaction
- `BeautifulSoup`: Parse HTML content
- `Pandas`: Handle data processing
- `logging` & `re`: Error tracking and pattern matching

---

## 8. Step 2: Send Request to IMDb Website

### WebDriver Initialization

```python
def get_chrome_driver():
    """
    Initializes and configures the Selenium Chrome WebDriver.
    Uses headless mode and optimized flags for reliable background execution.
    """
    chrome_options = Options()
    
    # Run in headless mode (no UI window shown)
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set language to English (prevent IMDb from localizing content)
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("user-agent=Mozilla/5.0...")
    chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en-US'})
    
    # Use WebDriver Manager to automatically download ChromeDriver
    raw_driver_path = ChromeDriverManager().install()
    resolved_driver_path = resolve_chromedriver_path(raw_driver_path)
    
    service = Service(resolved_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
```

### Request Execution

```python
def scrape_imdb_top_250():
    """Scrapes the IMDb Top 250 movies list."""
    url = "https://www.imdb.com/chart/top/"
    driver = None
    movies_data = []
    
    try:
        driver = get_chrome_driver()
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ipc-metadata-list")))
        
        # Add delay for JavaScript rendering
        time.sleep(2)
```

**Key Concepts**:
- **Headless Mode**: Browser runs without GUI (faster & less resource-intensive)
- **WebDriverWait**: Waits up to 15 seconds for elements to appear
- **User-Agent**: Identifies as real browser to avoid blocking

---

## 9. Step 3: Parse HTML Content

### Extract Page Source

```python
# Extract page source after JavaScript execution
html_content = driver.page_source
soup = BeautifulSoup(html_content, "html.parser")

# Find all movie list items
movie_items = soup.find_all("li", class_=lambda c: c and "ipc-metadata-list-summary-item" in c)

logger.info(f"Found {len(movie_items)} candidate movie elements on the page.")
```

### HTML Structure Handling

```python
# Fallback selector if primary class not found
if not movie_items:
    logger.warning("Target class not found, trying fallback list item selectors...")
    movie_items = soup.select("ul.ipc-metadata-list > li")
```

**Parsing Strategy**:
- Use modern CSS classes for selection
- Implement fallback selectors for flexibility
- Robust error handling for layout changes

---

## 10. Step 4: Extract Movie Details

### Extract From Each Movie Element

```python
for item in movie_items:
    try:
        # 1. Extract Rank and Title
        title_header = item.find("h3", class_=lambda c: c and "ipc-title__text" in c)
        header_text = title_header.get_text(strip=True)
        
        # Parse "1. The Shawshank Redemption" format
        rank_title_match = re.match(r"^(\d+)\.\s*(.*)$", header_text)
        if rank_title_match:
            rank = int(rank_title_match.group(1))
            title = rank_title_match.group(2).strip()
        
        # 2. Extract Release Year
        metadata_container = item.find("div", class_=lambda c: c and "cli-title-metadata" in c)
        year = 0
        if metadata_container:
            metadata_items = metadata_container.find_all("li")
            if metadata_items:
                year_text = metadata_items[0].get_text(strip=True)
                if re.match(r"^\d{4}$", year_text):
                    year = int(year_text)
        
        # Fallback: Extract any 4-digit year from text
        if not year:
            item_text = item.get_text(" ", strip=True)
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", item_text)
            if year_match:
                year = int(year_match.group(1))
        
        # 3. Extract Rating
        rating_span = item.find("span", class_=lambda c: c and "ipc-rating-star" in c)
        rating = 0.0
        if rating_span:
            rating_text = rating_span.get_text(strip=True)
            # Extract float from "9.3" or "9.3 (2.9M)"
            rating_match = re.search(r"(\d+\.\d+)", rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Store extracted data
        movies_data.append({
            "Rank": rank,
            "Movie Title": title,
            "Release Year": year,
            "IMDb Rating": rating
        })
        
    except Exception as e:
        logger.error(f"Error parsing individual movie element: {e}")
        continue
```

**Extraction Logic**:
- **Regex Patterns**: Robust pattern matching for flexible parsing
- **Fallback Chains**: Multiple methods to extract data if primary fails
- **Error Handling**: Skip problematic items without breaking entire process

---

## 11. Step 5: Store Data in CSV File

### Convert to Pandas DataFrame

```python
# Convert list of dictionaries to DataFrame
df = pd.DataFrame(movies)

# Display first few rows for verification
print(df.head())
```

### Save to CSV

```python
# Define CSV path
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
CSV_PATH = os.path.join(DOWNLOADS_DIR, 'imdb_top_250_movies.csv')

# Save DataFrame to CSV file
df.to_csv(CSV_PATH, index=False)

# CSV Structure:
# Rank | Movie Title              | Release Year | IMDb Rating
# -----|-------------------------|--------------|-------------
# 1    | The Shawshank Redemption| 1994         | 9.3
# 2    | The Godfather           | 1972         | 9.2
# ...
```

### Data Processing with Pandas

```python
# Calculate statistics
total_movies = len(df)

# Highest Rated Movie
idx_max = df['IMDb Rating'].idxmax()
highest_rated_movie = df.loc[idx_max]
highest_rated_str = f"{highest_rated_movie['Movie Title']} ({highest_rated_movie['IMDb Rating']})"

# Average Rating
avg_rating = round(df['IMDb Rating'].mean(), 2)

# Oldest Movie
valid_years_df = df[df['Release Year'] > 0]
if not valid_years_df.empty:
    idx_min = valid_years_df['Release Year'].idxmin()
    oldest_movie = valid_years_df.loc[idx_min]
    oldest_movie_str = f"{oldest_movie['Movie Title']} ({oldest_movie['Release Year']})"
```

---

## 12. Step 6: Display Results

### API Response

```python
@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Triggers scraping, processes data, and returns results."""
    try:
        movies = scrape_imdb_top_250()
        
        if not movies:
            return jsonify({
                "status": "error",
                "message": "No movies were extracted from IMDb."
            }), 500
        
        df = pd.DataFrame(movies)
        df.to_csv(CSV_PATH, index=False)
        
        return jsonify({
            "status": "success",
            "data": movies,
            "stats": {
                "total_movies": len(df),
                "highest_rated": highest_rated_str,
                "average_rating": avg_rating,
                "oldest_movie": oldest_movie_str
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500
```

### Frontend Display

```html
<!-- Dashboard displaying results -->
<div id="results-container">
    <div class="stats">
        <p>Total Movies: <span id="total">0</span></p>
        <p>Highest Rated: <span id="highest">N/A</span></p>
        <p>Average Rating: <span id="average">N/A</span></p>
        <p>Oldest Movie: <span id="oldest">N/A</span></p>
    </div>
    <table id="movies-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Movie Title</th>
                <th>Release Year</th>
                <th>IMDb Rating</th>
            </tr>
        </thead>
        <tbody id="table-body">
            <!-- Populated by JavaScript -->
        </tbody>
    </table>
</div>
```

---

## 13. Output

### Expected Results

#### CSV File Structure
```
Rank,Movie Title,Release Year,IMDb Rating
1,The Shawshank Redemption,1994,9.3
2,The Godfather,1972,9.2
3,The Godfather Part II,1974,9.0
4,The Dark Knight,2008,9.0
5,Pulp Fiction,1994,8.9
...
250,Killers of the Flower Moon,2023,8.0
```

#### Dashboard Statistics
```
Total Movies: 250
Highest Rated: The Shawshank Redemption (9.3)
Average Rating: 8.24
Oldest Movie: Metropolis (1927)
```

#### Sample JSON Response
```json
{
  "status": "success",
  "data": [
    {
      "Rank": 1,
      "Movie Title": "The Shawshank Redemption",
      "Release Year": 1994,
      "IMDb Rating": 9.3
    },
    {
      "Rank": 2,
      "Movie Title": "The Godfather",
      "Release Year": 1972,
      "IMDb Rating": 9.2
    }
  ],
  "stats": {
    "total_movies": 250,
    "highest_rated": "The Shawshank Redemption (9.3)",
    "average_rating": 8.24,
    "oldest_movie": "Metropolis (1927)"
  }
}
```

### File Locations
- **CSV Output**: `downloads/imdb_top_250_movies.csv`
- **Web Dashboard**: `http://localhost:5000/`
- **Download Link**: `http://localhost:5000/download`

---

## 14. Troubleshooting Table

| Problem | Cause | Solution |
|---------|-------|----------|
| **Module not found error** | Missing dependencies | Run `pip install -r requirements.txt` |
| **ChromeDriver not found** | WebDriver not installed | WebDriver Manager will auto-download; ensure Chrome is installed |
| **Port 5000 already in use** | Another application using port | Change port in `app.py`: `app.run(port=5001)` |
| **"No movies extracted" error** | IMDb HTML structure changed | Update CSS selectors in `scraper.py` |
| **Timeout waiting for page** | Network issue or page loading slow | Increase timeout: `WebDriverWait(driver, 30)` |
| **Empty CSV file** | Scraping failed silently | Check logs: Look for "Error parsing" messages in console |
| **JavaScript not rendering** | Browser headless mode issue | Remove `--headless` argument temporarily for debugging |
| **Connection refused error** | Flask server not running | Run: `python app.py` in terminal |
| **"Access Denied" from IMDb** | IP blocked or headers missing | Update user-agent string or use VPN |
| **Pandas not writing CSV** | Permissions issue | Ensure `downloads/` folder has write permissions |

---

## 15. Scope of the Project

### What This Project Does
✅ Automatically scrapes IMDb's Top 250 movies list  
✅ Extracts: Rank, Title, Release Year, Rating  
✅ Stores data in CSV format  
✅ Calculates statistics (average, highest, oldest)  
✅ Provides web-based dashboard interface  
✅ Allows CSV file download  

### What This Project Does NOT Do
❌ Scrape movie descriptions or genres  
❌ Collect audience reviews or comments  
❌ Access restricted IMDb pages (user watchlists, etc.)  
❌ Real-time data updates (manual scraping required)  
❌ Database storage (CSV only)  

### Limitations
- **Rate Limiting**: IMDb may block rapid repeated requests
- **Website Changes**: Updates to IMDb layout may break selectors
- **Legal**: Respect IMDb's terms of service regarding scraping
- **Performance**: Selenium-based scraping is slower than API calls

---

## 16. Methodology

### Data Collection Approach
1. **Browser Automation** (Selenium)
   - Simulates real user interaction
   - Handles JavaScript-rendered content
   - More reliable than simple HTTP requests

2. **HTML Parsing** (BeautifulSoup)
   - Fast, lightweight parsing
   - Efficient element selection
   - Low memory footprint

3. **Data Extraction** (Regex + Pattern Matching)
   - Robust pattern recognition
   - Fallback extraction methods
   - Handles variations in HTML structure

4. **Data Storage** (Pandas + CSV)
   - Structured data format
   - Easy import to Excel/databases
   - Human-readable output

### Error Handling Strategy
- **Try-Except Blocks**: Prevents single errors from breaking entire process
- **Logging**: Records all errors for debugging
- **Fallback Selectors**: Multiple methods to extract each field
- **Validation**: Checks for valid data before storing

### Quality Assurance
- Validates extracted data types (int for year/rank, float for rating)
- Sorts by rank to ensure correct order
- Logs number of successfully extracted movies
- Returns detailed error messages for debugging

---

## 17. Implementation

### Running the Application

#### **Method 1: Using Terminal**

```bash
# Navigate to project directory
cd c:\Users\kanis\Desktop\imdb_scraper

# Activate virtual environment
venv\Scripts\activate

# Install dependencies (if not done)
pip install -r requirements.txt

# Run Flask application
python app.py

# Output:
# * Running on http://127.0.0.1:5000
# * Press CTRL+C to quit
```

#### **Method 2: Direct Scraping**

```bash
# Test scraper without web server
python scraper.py

# Output:
# Scraped 250 movies successfully!
# First movie details: {'Rank': 1, 'Movie Title': 'The Shawshank Redemption', 'Release Year': 1994, 'IMDb Rating': 9.3}
# Last movie details: {'Rank': 250, 'Movie Title': '...', 'Release Year': ..., 'IMDb Rating': ...}
```

### Accessing the Dashboard

1. **Open Web Browser**
   - Navigate to: `http://localhost:5000/`

2. **Click "Scrape Movies" Button**
   - Initiates scraping process
   - Progress displayed in real-time
   - Displays statistics and movie table

3. **Download CSV**
   - Click "Download CSV" button
   - Saves `imdb_top_250_movies.csv` to downloads folder

### Expected Execution Time
- **Scraping**: 30-60 seconds (depends on network speed)
- **Data Processing**: <1 second
- **CSV Writing**: <1 second
- **Total**: ~1 minute per full execution

---

## 18. Conclusion

The **IMDb Top 250 Movies Scraper** successfully demonstrates modern web scraping techniques combined with practical web application development. By integrating Selenium for dynamic content handling, BeautifulSoup for efficient parsing, and Pandas for data processing, this project provides a complete solution for extracting, analyzing, and exporting movie data.

### Key Achievements
✓ Fully automated scraping process  
✓ User-friendly web interface  
✓ Robust error handling and logging  
✓ Efficient data processing and storage  
✓ Real-time statistics calculation  

### Learning Outcomes
- Web scraping with Selenium and BeautifulSoup
- REST API development with Flask
- Data manipulation with Pandas
- Frontend development with HTML/CSS/JavaScript
- Error handling and debugging
- Browser automation best practices

### Future Enhancements
- Add database storage (SQLite/PostgreSQL)
- Implement scheduled scraping (Cron jobs)
- Add filtering and sorting features
- Include movie details (genres, runtime, cast)
- Create email notifications for new top movies
- Deploy to cloud platform (Heroku, AWS)

### Final Notes
This project serves as an excellent foundation for web scraping and data analysis. The modular design allows easy customization for scraping other websites. Always respect website terms of service and implement appropriate rate limiting when scraping.

---

**Project Created**: 2026  
**Technology Stack**: Python, Flask, Selenium, BeautifulSoup, Pandas  
**Status**: Fully Functional ✓

