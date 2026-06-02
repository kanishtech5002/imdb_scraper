import os
import pandas as pd
from flask import Flask, render_template, jsonify, send_file
from scraper import scrape_imdb_top_250

app = Flask(__name__)

# Ensure the downloads directory exists
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
CSV_PATH = os.path.join(DOWNLOADS_DIR, 'imdb_top_250_movies.csv')

@app.route('/')
def index():
    """Renders the dashboard home page."""
    return render_template('index.html')

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """
    Triggers the scraping process, processes results with Pandas,
    saves the data to CSV, and returns dashboard statistics along with movie data.
    """
    try:
        # Scrape data using our Selenium service
        movies = scrape_imdb_top_250()
        
        if not movies:
            return jsonify({
                "status": "error",
                "message": "No movies were extracted from IMDb. The page layout may have changed."
            }), 500
            
        # Convert to Pandas DataFrame for calculations and CSV serialization
        df = pd.DataFrame(movies)
        
        # Save DataFrame to CSV
        # Required columns: Rank, Movie Title, Release Year, IMDb Rating
        df.to_csv(CSV_PATH, index=False)
        
        # Calculate stats using Pandas
        total_movies = len(df)
        
        # Highest Rated Movie
        # If there are duplicates, pick the one with highest rank (first in list)
        idx_max = df['IMDb Rating'].idxmax()
        highest_rated_movie = df.loc[idx_max]
        highest_rated_str = f"{highest_rated_movie['Movie Title']} ({highest_rated_movie['IMDb Rating']})"
        
        # Average Rating
        avg_rating = round(df['IMDb Rating'].mean(), 2)
        
        # Oldest Movie
        # Exclude movies that have 0 or invalid year if any
        valid_years_df = df[df['Release Year'] > 0]
        if not valid_years_df.empty:
            idx_min = valid_years_df['Release Year'].idxmin()
            oldest_movie = valid_years_df.loc[idx_min]
            oldest_movie_str = f"{oldest_movie['Movie Title']} ({oldest_movie['Release Year']})"
        else:
            oldest_movie_str = "N/A"
            
        return jsonify({
            "status": "success",
            "data": movies,
            "stats": {
                "total_movies": total_movies,
                "highest_rated": highest_rated_str,
                "average_rating": avg_rating,
                "oldest_movie": oldest_movie_str
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error during scraping API call: {e}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred while scraping: {str(e)}"
        }), 500

@app.route('/download')
def download():
    """Serves the generated CSV file as an attachment download."""
    if not os.path.exists(CSV_PATH):
        return "No scraped data available to download. Please click 'Scrape Movies' first.", 404
        
    return send_file(
        CSV_PATH,
        mimetype='text/csv',
        as_attachment=True,
        download_name='imdb_top_250_movies.csv'
    )

if __name__ == '__main__':
    # Start the Flask development server on port 5000
    app.run(debug=True, host='127.0.0.1', port=5000)
