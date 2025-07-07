"""
Session App Module

This module provides the new unified app architecture for managing sessions,
agents, bankers, and other components in the distributed system.

Classes:
    App: Protocol defining the core app interface
"""

from .app import App

__all__ = [
    'App',
]
