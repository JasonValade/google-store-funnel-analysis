"""Tests for Streamlit API compatibility.

These tests ensure that dashboard code uses Streamlit API parameters
compatible with the current version (width='stretch' instead of use_container_width).
"""

import re
from pathlib import Path

import pytest


class TestStreamlitCompatibility:
    """Tests for Streamlit API compatibility."""

    @pytest.fixture
    def dashboard_pages(self):
        """Get all dashboard page files."""
        dashboard_dir = Path(__file__).parent.parent / "dashboard" / "pages"
        return list(dashboard_dir.glob("*.py"))

    def test_width_stretch_for_dataframes(self, dashboard_pages):
        """Test that st.dataframe calls use width='stretch' instead of use_container_width."""
        dataframe_pattern = r"st\.dataframe\([^)]*\)"

        for page_file in dashboard_pages:
            content = page_file.read_text()
            matches = re.findall(dataframe_pattern, content)

            for match in matches:
                # Check if use_container_width is used (deprecated)
                if "use_container_width=" in match:
                    pytest.fail(
                        f"Found st.dataframe with use_container_width in {page_file.name}. "
                        f"Streamlit now requires width='stretch' instead of use_container_width."
                    )

    def test_width_stretch_for_plotly_charts(self, dashboard_pages):
        """Test that st.plotly_chart calls use width='stretch' instead of use_container_width."""
        plotly_pattern = r"st\.plotly_chart\([^)]*\)"

        for page_file in dashboard_pages:
            content = page_file.read_text()
            matches = re.findall(plotly_pattern, content)

            for match in matches:
                # Check if use_container_width is used (deprecated)
                if "use_container_width=" in match:
                    pytest.fail(
                        f"Found st.plotly_chart with use_container_width in {page_file.name}. "
                        f"Streamlit now requires width='stretch' instead of use_container_width."
                    )
