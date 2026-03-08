"""MateObserve — Simple API observability in 30 seconds 🧉"""

from mateobserve.middleware import ObserveMiddleware
from mateobserve.client import MetricsClient
from mateobserve.config import MateObserveConfig

__all__ = ["ObserveMiddleware", "MetricsClient", "MateObserveConfig"]
__version__ = "0.1.0"
