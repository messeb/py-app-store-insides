"""Module for classifying app feedback using OpenAI."""

import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv


class FeedbackClassifier:
    """Classifier for categorizing app feedback using OpenAI."""

    def __init__(self):
        """
        Initialize the feedback classifier.

        Args:
            api_key: OpenAI API key (if None, loads from environment)
            model: OpenAI model to use (if None, loads from environment or defaults)
        """
        load_dotenv()

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY in .env file or pass as parameter."
            )

        self.model = os.getenv("OPENAI_MODEL")
        self.client = OpenAI(api_key=self.api_key)

    def classify_feedback(
        self,
        review_text: str,
        rating: int | None = None
    ) -> Dict[str, str]:
        """
        Classify a single feedback review.

        Args:
            review_text: The review text to classify
            rating: Optional rating (1-5)

        Returns:
            Dictionary with 'category' and 'explanation'
        """
        prompt = self._build_classification_prompt(review_text, rating)

        try:
            # Build API parameters - only include supported ones for gpt-4o-mini
            api_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert at analyzing app store reviews. "
                            "Classify reviews into categories and provide clear, concise explanations. "
                            "Be consistent in your classifications."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_completion_tokens": 200
            }

            response = self.client.chat.completions.create(**api_params)

            result = response.choices[0].message.content.strip()
            return self._parse_classification_result(result)

        except Exception as e:
            return {
                "category": "Other",
                "explanation": f"Classification failed: {str(e)}"
            }

    def classify_batch(
        self,
        df: pd.DataFrame,
        review_column: str = "review",
        rating_column: str = "rating",
        max_workers: int = 10
    ) -> pd.DataFrame:
        """
        Classify multiple reviews in a DataFrame with parallel processing.

        Args:
            df: DataFrame containing reviews
            review_column: Name of the column containing review text
            rating_column: Name of the column containing ratings
            max_workers: Maximum number of parallel workers (default: 10)

        Returns:
            DataFrame with added 'category' and 'explanation' columns
        """
        def classify_single_review(idx_row):
            """Helper function to classify a single review."""
            idx, row = idx_row
            review_text = row[review_column]
            rating = row.get(rating_column) if rating_column in df.columns else None

            # Skip empty reviews
            if pd.isna(review_text) or not str(review_text).strip():
                return idx, {
                    "category": "Other",
                    "explanation": "No review text provided"
                }

            classification = self.classify_feedback(str(review_text), rating)
            return idx, classification

        # Prepare data for parallel processing
        reviews_to_process = list(df.iterrows())
        classifications = [None] * len(df)
        completed_count = 0

        # Process reviews in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(classify_single_review, idx_row): idx_row[0]
                for idx_row in reviews_to_process
            }

            # Collect results as they complete
            for future in as_completed(future_to_idx):
                idx, classification = future.result()
                classifications[idx] = classification
                completed_count += 1

                # Progress indicator
                if completed_count % 10 == 0 or completed_count == len(df):
                    print(f"Classified {completed_count}/{len(df)} reviews...")

        # Add classifications to DataFrame
        result_df = df.copy()
        result_df["category"] = [c["category"] for c in classifications]
        result_df["explanation"] = [c["explanation"] for c in classifications]

        return result_df

    def get_category_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get distribution of feedback categories.

        Args:
            df: DataFrame with 'category' column

        Returns:
            DataFrame with category counts and percentages
        """
        if "category" not in df.columns:
            raise ValueError("DataFrame must have 'category' column")

        distribution = df["category"].value_counts().reset_index()
        distribution.columns = ["Category", "Count"]
        distribution["Percentage"] = (
            distribution["Count"] / distribution["Count"].sum() * 100
        ).round(2)

        return distribution

    def _build_classification_prompt(
        self,
        review_text: str,
        rating: int | None
    ) -> str:
        """Build the classification prompt."""
        rating_context = f" (Rating: {rating}/5)" if rating else ""

        # Build category list with descriptions
        categories_text = ""
        for idx, category in enumerate(self.CATEGORIES, 1):
            description = self.CATEGORY_DESCRIPTIONS.get(
                category,
                "No description available"
            )
            categories_text += f"{idx}. {category}: {description}\n"

        return f"""Classify the following app review into ONE of these categories:

{categories_text}
Review{rating_context}: {review_text}

Respond in this exact format:
Category: [chosen category]
Explanation: [brief explanation of why this category was chosen]"""

    def _parse_classification_result(self, result: str) -> Dict[str, str]:
        """Parse the classification result from OpenAI."""
        lines = result.strip().split("\n")
        category = "Other"
        explanation = ""

        for line in lines:
            if line.startswith("Category:"):
                category = line.replace("Category:", "").strip()
            elif line.startswith("Explanation:"):
                explanation = line.replace("Explanation:", "").strip()

        # Validate category
        if category not in self.CATEGORIES:
            category = "Other"
            explanation = f"Invalid category detected. {explanation}"

        return {
            "category": category,
            "explanation": explanation
        }
