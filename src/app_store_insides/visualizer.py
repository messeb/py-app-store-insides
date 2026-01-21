"""Module for visualizing app feedback data."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Any


class RatingVisualizer:
    """Visualizer for app ratings and feedback distribution."""

    @staticmethod
    def plot_rating_distribution(
        df: pd.DataFrame,
        rating_column: str = "rating",
        title: str | None = None
    ) -> go.Figure:
        """
        Create a bar chart showing rating distribution.

        Args:
            df: DataFrame containing ratings
            rating_column: Name of the column containing ratings
            title: Custom title for the chart

        Returns:
            Plotly figure object
        """
        if rating_column not in df.columns:
            raise ValueError(f"Column '{rating_column}' not found in DataFrame")

        # Calculate average rating
        average_rating = df[rating_column].mean()

        # Get rating counts
        rating_counts = df[rating_column].value_counts().reset_index()
        rating_counts.columns = ["Rating", "Count"]
        rating_counts = rating_counts.sort_values("Rating")

        # Create bar chart
        chart_title = title or f"Rating Distribution (Average: {average_rating:.2f})"
        fig = px.bar(
            rating_counts,
            x="Rating",
            y="Count",
            title=chart_title,
            labels={"Count": "Number of Reviews", "Rating": "Rating"},
            text="Count",
            color="Rating",
            color_continuous_scale="RdYlGn"
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            showlegend=False
        )

        return fig

    @staticmethod
    def plot_category_distribution(
        df: pd.DataFrame,
        category_column: str = "category",
        title: str = "Feedback Category Distribution"
    ) -> go.Figure:
        """
        Create a pie chart showing category distribution.

        Args:
            df: DataFrame containing categories
            category_column: Name of the column containing categories
            title: Chart title

        Returns:
            Plotly figure object
        """
        if category_column not in df.columns:
            raise ValueError(f"Column '{category_column}' not found in DataFrame")

        # Get category counts
        category_counts = df[category_column].value_counts().reset_index()
        category_counts.columns = ["Category", "Count"]

        # Create pie chart
        fig = px.pie(
            category_counts,
            values="Count",
            names="Category",
            title=title,
            hole=0.3
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        return fig

    @staticmethod
    def plot_category_bar_chart(
        df: pd.DataFrame,
        category_column: str = "category",
        title: str = "Feedback Category Distribution"
    ) -> go.Figure:
        """
        Create a horizontal bar chart showing category distribution.

        Args:
            df: DataFrame containing categories
            category_column: Name of the column containing categories
            title: Chart title

        Returns:
            Plotly figure object
        """
        if category_column not in df.columns:
            raise ValueError(f"Column '{category_column}' not found in DataFrame")

        # Get category counts
        category_counts = df[category_column].value_counts().reset_index()
        category_counts.columns = ["Category", "Count"]
        category_counts = category_counts.sort_values("Count", ascending=True)

        # Create horizontal bar chart
        fig = px.bar(
            category_counts,
            x="Count",
            y="Category",
            orientation="h",
            title=title,
            text="Count",
            color="Count",
            color_continuous_scale="Blues"
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)

        return fig

    @staticmethod
    def plot_rating_by_category(
        df: pd.DataFrame,
        category_column: str = "category",
        rating_column: str = "rating",
        title: str = "Average Rating by Category"
    ) -> go.Figure:
        """
        Create a bar chart showing average rating per category.

        Args:
            df: DataFrame containing categories and ratings
            category_column: Name of the column containing categories
            rating_column: Name of the column containing ratings
            title: Chart title

        Returns:
            Plotly figure object
        """
        required_cols = [category_column, rating_column]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        # Calculate average rating per category
        avg_ratings = df.groupby(category_column)[rating_column].agg(
            ["mean", "count"]
        ).reset_index()
        avg_ratings.columns = ["Category", "Average Rating", "Count"]
        avg_ratings = avg_ratings.sort_values("Average Rating", ascending=True)

        # Create bar chart
        fig = px.bar(
            avg_ratings,
            x="Average Rating",
            y="Category",
            orientation="h",
            title=title,
            text="Average Rating",
            color="Average Rating",
            color_continuous_scale="RdYlGn",
            hover_data=["Count"]
        )

        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )
        fig.update_layout(
            xaxis=dict(range=[0, 5.5]),
            showlegend=False
        )

        return fig

    @staticmethod
    def plot_rating_over_time(
        df: pd.DataFrame,
        date_column: str = "date",
        rating_column: str = "rating",
        title: str = "Rating Trend Over Time",
        rolling_window: int = 10
    ) -> go.Figure:
        """
        Create a line chart showing rating trends over time.

        Args:
            df: DataFrame containing dates and ratings
            date_column: Name of the column containing dates
            rating_column: Name of the column containing ratings
            title: Chart title
            rolling_window: Window size for rolling average

        Returns:
            Plotly figure object
        """
        required_cols = [date_column, rating_column]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        # Sort by date
        df_sorted = df.sort_values(date_column).copy()
        df_sorted[date_column] = pd.to_datetime(df_sorted[date_column])

        # Calculate rolling average
        df_sorted["rolling_avg"] = df_sorted[rating_column].rolling(
            window=rolling_window,
            min_periods=1
        ).mean()

        # Create line chart
        fig = go.Figure()

        # Add scatter plot for individual ratings
        fig.add_trace(go.Scatter(
            x=df_sorted[date_column],
            y=df_sorted[rating_column],
            mode="markers",
            name="Individual Ratings",
            marker=dict(size=4, opacity=0.3),
            showlegend=True
        ))

        # Add rolling average line
        fig.add_trace(go.Scatter(
            x=df_sorted[date_column],
            y=df_sorted["rolling_avg"],
            mode="lines",
            name=f"{rolling_window}-Review Rolling Avg",
            line=dict(color="red", width=2),
            showlegend=True
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Rating",
            yaxis=dict(range=[0, 5.5]),
            hovermode="x unified"
        )

        return fig
