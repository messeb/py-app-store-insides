"""Module for fetching app reviews from different app stores."""

from typing import List, Dict, Any
import pandas as pd
from app_store_web_scraper import AppStoreEntry
from google_play_scraper import Sort, reviews as gp_reviews


class AppStoreFetcher:
    """Fetcher for Apple App Store reviews."""

    def __init__(self, app_id: int, country: str = "de"):
        """
        Initialize the App Store fetcher.

        Args:
            app_id: The Apple App Store ID
            country: Country code (default: "de")
        """
        self.app_id = app_id
        self.country = country
        self.app = AppStoreEntry(app_id=app_id, country=country)

    def fetch_reviews(self, limit: int) -> pd.DataFrame:
        """
        Fetch reviews from Apple App Store.

        Args:
            limit: Maximum number of reviews to fetch (None for all)

        Returns:
            DataFrame with columns: id, rating, review, date, platform
        """
        reviews_data = []
        for idx, review in enumerate(self.app.reviews()):
            if limit and idx >= limit:
                break
            reviews_data.append({
                "id": review.id,
                "rating": review.rating,
                "review": review.content,
                "date": review.date,
                "platform": "apple"
            })

        df = pd.DataFrame(reviews_data)

        # Normalize dates to timezone-naive UTC
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], utc=True)
            df["date"] = df["date"].dt.tz_localize(None)

        return df


class GooglePlayFetcher:
    """Fetcher for Google Play Store reviews."""

    def __init__(self, app_id: str, country: str = "de", lang: str = "de"):
        """
        Initialize the Google Play fetcher.

        Args:
            app_id: The Google Play app package name
            country: Country code (default: "de")
            lang: Language code (default: "de")
        """
        self.app_id = app_id
        self.country = country
        self.lang = lang

    def fetch_reviews(
        self,
        limit: int,
    ) -> pd.DataFrame:
        """
        Fetch reviews from Google Play Store.

        Args:
            limit: Number of reviews to fetch per batch

        Returns:
            DataFrame with columns: id, rating, review, date, platform
        """
        # Fetch first batch
        result, continuation_token = gp_reviews(
            self.app_id,
            lang=self.lang,
            country=self.country,
            sort=Sort.NEWEST,
            count=limit,
        )

        print(f"Fetched {len(result)} reviews from Google Play.")

        all_reviews = result if result else []

        # Convert to DataFrame
        reviews_data = []
        for review in all_reviews:
            reviews_data.append({
                "id": review.get("reviewId"),
                "rating": review.get("score"),
                "review": review.get("content"),
                "date": review.get("at"),
                "platform": "google"
            })

        df = pd.DataFrame(reviews_data)

        # Normalize dates to timezone-naive UTC
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], utc=True)
            df["date"] = df["date"].dt.tz_localize(None)

        return df


def combine_reviews(*dataframes: pd.DataFrame) -> pd.DataFrame:
    """
    Combine multiple review DataFrames.

    Args:
        *dataframes: Variable number of review DataFrames

    Returns:
        Combined DataFrame
    """
    if not dataframes:
        return pd.DataFrame()

    # Filter out empty dataframes
    non_empty_dfs = [df for df in dataframes if not df.empty]

    if not non_empty_dfs:
        return pd.DataFrame()

    combined = pd.concat(non_empty_dfs, ignore_index=True)

    # Normalize dates to handle timezone issues
    # Convert all dates to timezone-naive UTC
    if "date" in combined.columns:
        combined["date"] = pd.to_datetime(combined["date"], utc=True)
        combined["date"] = combined["date"].dt.tz_localize(None)

    return combined.sort_values("date", ascending=False).reset_index(drop=True)
