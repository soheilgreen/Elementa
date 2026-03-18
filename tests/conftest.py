"""
pytest configuration for the Elementa test suite.
"""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that require gmsh, scikit-fem, and a display (slow).",
    )
