"""App Store Insides - A tool for analyzing app store feedback."""

from .data_fetcher import AppStoreFetcher, GooglePlayFetcher
from .classifier import FeedbackClassifier
from .visualizer import RatingVisualizer

__version__ = "0.1.0"
__all__ = [
    "AppStoreFetcher",
    "GooglePlayFetcher",
    "FeedbackClassifier",
    "RatingVisualizer",
]
