"""Tests for Streamlit API compatibility.

These tests ensure that dashboard code uses Streamlit API parameters
compatible with the pinned version (streamlit==1.37.0).
"""

import re
from pathlib import Path

import pytest


class TestStreamlit137Compatibility:
    """Tests for Streamlit 1.37 API compatibility."""

    @pytest.fixture
    def dashboard_pages(self):
        """Get all dashboard page files."""
        dashboard_dir = Path(__file__).parent.parent / "dashboard" / "pages"
        return list(dashboard_dir.glob("*.py"))

    def test_no_width_stretch_string(self, dashboard_pages):
        """Test that width='stretch' is not used (Streamlit 1.37 incompatibility).

        Streamlit 1.37 does not support width='stretch' string.
        For st.dataframe and st.plotly_chart, use use_container_width=True instead.
        """
        forbidden_pattern = r'width\s*=\s*["\']stretch["\']'

        for page_file in dashboard_pages:
            content = page_file.read_text()
            matches = re.findall(forbidden_pattern, content)

            if matches:
                pytest.fail(
                    f"Found {len(matches)} occurrence(s) of width='stretch' in {page_file.name}. "
                    f"Streamlit 1.37 does not support width='stretch'. "
                    f"Use use_container_width=True for st.dataframe and st.plotly_chart instead."
                )

    def test_use_container_width_for_dataframes(self, dashboard_pages):
        """Test that st.dataframe calls use use_container_width=True instead of width."""
        dataframe_pattern = r"st\.dataframe\([^)]*\)"

        for page_file in dashboard_pages:
            content = page_file.read_text()
            matches = re.findall(dataframe_pattern, content)

            for match in matches:
                # Check if width parameter is used (not allowed in 1.37)
                if "width=" in match and "use_container_width=True" not in match:
                    pytest.fail(
                        f"Found st.dataframe with width parameter in {page_file.name}. "
                        f"Streamlit 1.37 requires use_container_width=True instead of width."
                    )

    def test_use_container_width_for_plotly_charts(self, dashboard_pages):
        """Test that st.plotly_chart calls use use_container_width=True instead of width."""
        plotly_pattern = r"st\.plotly_chart\([^)]*\)"

        for page_file in dashboard_pages:
            content = page_file.read_text()
            matches = re.findall(plotly_pattern, content)

            for match in matches:
                # Check if width parameter is used (not allowed in 1.37)
                if "width=" in match and "use_container_width=True" not in match:
                    pytest.fail(
                        f"Found st.plotly_chart with width parameter in {page_file.name}. "
                        f"Streamlit 1.37 requires use_container_width=True instead of width."
                    )
