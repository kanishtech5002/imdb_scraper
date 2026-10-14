
import logging
import re

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMDB_URL = "https://www.imdb.com/chart/top/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_imdb_top_250():
    """Fetch and parse IMDb Top 250 movie data."""

    logger.info("Requesting IMDb Top 250 page...")

    try:
        response = requests.get(
            IMDB_URL,
            headers=HEADERS,
            timeout=25,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        logger.exception("Failed to fetch IMDb page")
        raise RuntimeError(
            f"Could not access IMDb: {exc}"
        ) from exc

    soup = BeautifulSoup(response.text, "html.parser")

    movie_items = soup.select(
        "li.ipc-metadata-list-summary-item"
    )

    if not movie_items:
        movie_items = soup.select(
            "ul.ipc-metadata-list > li"
        )

    if not movie_items:
        raise RuntimeError(
            "IMDb returned no movie entries. "
            "The page may be blocked or its layout changed."
        )

    movies_data = []

    for index, item in enumerate(movie_items, start=1):
        try:
            title_element = item.select_one(
                "h3.ipc-title__text"
            )

            if not title_element:
                continue

            header_text = title_element.get_text(
                " ", strip=True
            )

            match = re.match(
                r"^\s*(\d+)\.\s*(.+)$",
                header_text,
            )

            if match:
                rank = int(match.group(1))
                title = match.group(2).strip()
            else:
                rank = index
                title = header_text

            # Release year
            year = 0

            metadata = item.select_one(
                ".cli-title-metadata"
            )

            if metadata:
                for element in metadata.select("li, span"):
                    year_match = re.search(
                        r"\b(19\d{2}|20\d{2})\b",
                        element.get_text(" ", strip=True),
                    )

                    if year_match:
                        year = int(year_match.group(1))
                        break

            if not year:
                year_match = re.search(
                    r"\b(19\d{2}|20\d{2})\b",
                    item.get_text(" ", strip=True),
                )

                if year_match:
                    year = int(year_match.group(1))

            # IMDb rating
            rating = 0.0

            rating_element = item.select_one(
                ".ipc-rating-star"
            )

            if rating_element:
                rating_text = rating_element.get_text(
                    " ", strip=True
                )

                rating_match = re.search(
                    r"(?<!\d)(10(?:\.0)?|[0-9]\.[0-9])"
                    r"(?!\d)",
                    rating_text,
                )

                if rating_match:
                    rating = float(rating_match.group(1))

            movies_data.append({
                "Rank": rank,
                "Movie Title": title,
                "Release Year": year,
                "IMDb Rating": rating,
            })

        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning(
                "Skipping movie entry %s: %s",
                index,
                exc,
            )

    movies_data.sort(key=lambda movie: movie["Rank"])

    if not movies_data:
        raise RuntimeError(
            "Movie entries were found, but no valid "
            "movie data could be extracted."
        )

    logger.info(
        "Successfully extracted %s movies.",
        len(movies_data),
    )

    return movies_data


if __name__ == "__main__":
    try:
        movies = scrape_imdb_top_250()
        print(f"Movies extracted: {len(movies)}")

        for movie in movies[:5]:
            print(movie)

    except Exception as exc:
        print(f"Scraping failed: {exc}")
