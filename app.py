
import os
import pandas as pd
from flask import Flask, render_template, jsonify, send_file
from scraper import scrape_imdb_top_250

app = Flask(__name__)

# Vercel writable temporary directory
DOWNLOADS_DIR = "/tmp"
CSV_PATH = os.path.join(
    DOWNLOADS_DIR,
    "imdb_top_250_movies.csv"
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["GET", "POST"])
def scrape():
    try:
        # Scrape IMDb Top 250 movies
        movies = scrape_imdb_top_250()

        if not movies:
            return jsonify({
                "status": "error",
                "message": "No movies extracted from IMDb."
            }), 500

        df = pd.DataFrame(movies)

        # Validate required columns
        required_columns = [
            "Rank",
            "Movie Title",
            "Release Year",
            "IMDb Rating"
        ]

        missing = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing:
            return jsonify({
                "status": "error",
                "message": f"Missing columns: {missing}"
            }), 500

        # Save CSV to writable temporary storage
        df.to_csv(CSV_PATH, index=False)

        # Dashboard statistics
        total_movies = len(df)

        ratings = pd.to_numeric(
            df["IMDb Rating"], errors="coerce"
        )

        if ratings.notna().any():
            idx_max = ratings.idxmax()
            highest = df.loc[idx_max]

            highest_rated = (
                f"{highest['Movie Title']} "
                f"({ratings.loc[idx_max]})"
            )

            average_rating = round(
                ratings.mean(), 2
            )
        else:
            highest_rated = "N/A"
            average_rating = 0.0

        years = pd.to_numeric(
            df["Release Year"], errors="coerce"
        )

        valid_years = years[years > 0]

        if not valid_years.empty:
            idx_min = valid_years.idxmin()
            oldest = df.loc[idx_min]

            oldest_movie = (
                f"{oldest['Movie Title']} "
                f"({int(years.loc[idx_min])})"
            )
        else:
            oldest_movie = "N/A"

        return jsonify({
            "status": "success",
            "data": movies,
            "stats": {
                "total_movies": total_movies,
                "highest_rated": highest_rated,
                "average_rating": average_rating,
                "oldest_movie": oldest_movie
            }
        })

    except Exception:
        app.logger.exception("Scraping failed")

        return jsonify({
            "status": "error",
            "message": (
                "Scraping failed. Check Vercel "
                "Function Logs for details."
            )
        }), 500


@app.route("/download")
def download():
    if not os.path.exists(CSV_PATH):
        return (
            "No CSV available. Scrape movies first.",
            404
        )

    return send_file(
        CSV_PATH,
        mimetype="text/csv",
        as_attachment=True,
        download_name="imdb_top_250_movies.csv"
    )


if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
