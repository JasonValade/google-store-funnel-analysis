"""Unit tests for dashboard charts module."""

import pandas as pd
import pytest
from plotly.graph_objects import Figure

from dashboard.utils.charts import (
    C,
    calibration_chart,
    coefficient_chart,
    decile_chart,
    device_bar_chart,
    funnel_chart,
    pr_curves_chart,
    tracking_scatter,
    weekly_conversion_chart,
)


class TestBaseLayout:
    """Tests for base layout helper."""

    def test_base_layout_returns_dict(self):
        """Test that _base_layout returns a dictionary."""
        from dashboard.utils.charts import _base_layout
        result = _base_layout()
        assert isinstance(result, dict)
        assert "font" in result
        assert "template" in result


class TestApplyTheme:
    """Tests for apply_theme function."""

    def test_apply_theme_returns_figure(self):
        """Test that apply_theme returns a Figure object."""
        from dashboard.utils.charts import apply_theme
        fig = Figure()
        result = apply_theme(fig, "Test Title")
        assert isinstance(result, Figure)
        assert result.layout.title.text == "Test Title"


class TestFunnelChart:
    """Tests for funnel chart function."""

    def test_funnel_chart_basic(self):
        """Test basic funnel chart creation."""
        stages = ["View", "Cart", "Checkout", "Purchase"]
        values = [10000, 5000, 2000, 1000]
        fig = funnel_chart(stages, values)
        assert isinstance(fig, Figure)
        assert len(fig.data) == 1
        assert fig.layout.title.text == "Purchase Funnel"

    def test_funnel_chart_custom_title(self):
        """Test funnel chart with custom title."""
        stages = ["View", "Purchase"]
        values = [10000, 1000]
        fig = funnel_chart(stages, values, title="Custom Funnel")
        assert fig.layout.title.text == "Custom Funnel"


class TestWeeklyConversionChart:
    """Tests for weekly conversion chart function."""

    @pytest.fixture
    def weekly_data(self):
        """Create mock weekly conversion data."""
        return pd.DataFrame({
            "week_start": pd.to_datetime([
                "2020-11-01", "2020-11-08", "2020-11-15",
                "2020-11-22", "2020-11-29", "2020-12-06", "2020-12-13",
            ]),
            "purchase_conversion_rate": [7.0, 7.5, 8.0, 8.5, 8.93, 8.5, 8.0],
        })

    def test_weekly_conversion_chart_basic(self, weekly_data):
        """Test basic weekly conversion chart."""
        fig = weekly_conversion_chart(weekly_data)
        assert isinstance(fig, Figure)
        assert len(fig.data) >= 1  # At least the line trace
        assert fig.layout.xaxis.title.text == "Week starting"

    def test_weekly_conversion_chart_with_peak(self, weekly_data):
        """Test weekly conversion chart with peak annotation."""
        fig = weekly_conversion_chart(weekly_data, peak_week="2020-12-06")
        assert isinstance(fig, Figure)
        # Check that annotations exist
        assert len(fig.layout.annotations) > 0


class TestDeviceBarChart:
    """Tests for device bar chart function."""

    @pytest.fixture
    def device_data(self):
        """Create mock device data."""
        return pd.DataFrame({
            "device_category": ["mobile", "desktop", "tablet"],
            "overall_purchase_rate": [6.26, 5.91, 5.50],
        })

    def test_device_bar_chart_basic(self, device_data):
        """Test basic device bar chart."""
        fig = device_bar_chart(device_data)
        assert isinstance(fig, Figure)
        assert len(fig.data) == 1
        assert fig.layout.xaxis.title.text == "Device"
        assert fig.layout.yaxis.title.text == "Overall purchase conversion rate (%)"


class TestTrackingScatter:
    """Tests for tracking scatter chart function."""

    @pytest.fixture
    def tracking_data(self):
        """Create mock tracking alert data."""
        return pd.DataFrame({
            "date": pd.to_datetime(["2020-11-21", "2020-11-22", "2020-11-23"]),
            "event_volume_ratio": [0.0, 0.0, 0.0],
            "page_view_ratio": [0.8, 0.9, 1.0],
            "traffic_adjusted_event_ratio": [0.0, 0.0, 0.0],
            "event_label": ["add_to_cart", "add_to_cart", "add_to_cart"],
            "status_label": ["CRITICAL", "CRITICAL", "CRITICAL"],
            "event_name": ["add_to_cart", "add_to_cart", "add_to_cart"],
            "tracking_status": ["outage", "outage", "outage"],
        })

    def test_tracking_scatter_basic(self, tracking_data):
        """Test basic tracking scatter chart."""
        fig = tracking_scatter(tracking_data)
        assert isinstance(fig, Figure)
        # Should have 3 traces (one for each ratio)
        assert len(fig.data) == 3
        assert fig.layout.xaxis.title.text == "Alert date"
        assert fig.layout.yaxis.title.text == "Ratio (1.0 = expected)"


class TestPRCurvesChart:
    """Tests for PR curves chart function."""

    @pytest.fixture
    def pr_data(self):
        """Create mock PR curve data."""
        data = []
        for model in ["LogisticRegression", "RandomForest"]:
            for recall in [i / 10 for i in range(11)]:
                data.append({
                    "model": model,
                    "recall": recall,
                    "precision": recall * 0.8 + 0.1,
                })
        return pd.DataFrame(data)

    def test_pr_curves_chart_basic(self, pr_data):
        """Test basic PR curves chart."""
        fig = pr_curves_chart(pr_data, no_skill=0.05)
        assert isinstance(fig, Figure)
        # Should have baseline + model curves
        assert len(fig.data) >= 2
        assert fig.layout.xaxis.title.text == "Recall"
        assert fig.layout.yaxis.title.text == "Precision"


class TestCalibrationChart:
    """Tests for calibration chart function."""

    @pytest.fixture
    def calibration_data(self):
        """Create mock calibration data."""
        data = []
        for cal_type in ["uncalibrated", "sigmoid_calibrated"]:
            for i in range(10):
                pred = (i + 1) / 10
                data.append({
                    "calibration_type": cal_type,
                    "mean_predicted_probability": pred,
                    "observed_positive_fraction": pred * 0.95 + 0.02,
                })
        return pd.DataFrame(data)

    def test_calibration_chart_basic(self, calibration_data):
        """Test basic calibration chart."""
        fig = calibration_chart(calibration_data)
        assert isinstance(fig, Figure)
        # Should have perfect calibration line + 2 curves
        assert len(fig.data) == 3
        assert fig.layout.xaxis.title.text == "Mean predicted probability"
        assert fig.layout.yaxis.title.text == "Observed positive fraction"


class TestDecileChart:
    """Tests for decile chart function."""

    @pytest.fixture
    def decile_data(self):
        """Create mock decile data."""
        data = []
        for i in range(1, 11):
            data.append({
                "risk_decile": i,
                "purchase_rate": 0.05 + (11 - i) * 0.01,
                "session_count": 1000,
                "purchase_count": int(1000 * (0.05 + (11 - i) * 0.01)),
                "lift": 1.0 + (11 - i) * 0.2,
                "overall_test_purchase_rate": 0.05,
            })
        return pd.DataFrame(data)

    def test_decile_chart_basic(self, decile_data):
        """Test basic decile chart."""
        fig = decile_chart(decile_data)
        assert isinstance(fig, Figure)
        assert len(fig.data) == 1
        assert fig.layout.xaxis.title.text == "Risk decile (1 = highest predicted risk)"
        assert fig.layout.yaxis.title.text == "Purchase rate (%)"


class TestCoefficientChart:
    """Tests for coefficient chart function."""

    @pytest.fixture
    def coefficient_data(self):
        """Create mock coefficient data."""
        return pd.DataFrame({
            "feature": [
                "first_item_name_Android_Wear_Wristband",
                "country_United_States",
                "device_category_mobile",
                "seconds_log1p",
            ],
            "coefficient": [0.5, 0.3, -0.2, -0.1],
            "absolute_coefficient": [0.5, 0.3, 0.2, 0.1],
            "direction": ["positive", "positive", "negative", "negative"],
        })

    def test_coefficient_chart_basic(self, coefficient_data):
        """Test basic coefficient chart."""
        fig = coefficient_chart(coefficient_data)
        assert isinstance(fig, Figure)
        assert len(fig.data) == 1
        assert fig.layout.xaxis.title.text == "Logistic regression coefficient"
        assert fig.layout.yaxis.title.text == ""

    def test_coefficient_chart_coloring(self, coefficient_data):
        """Test that coefficients are colored by direction."""
        fig = coefficient_chart(coefficient_data)
        # Check that the chart has colored bars
        assert len(fig.data) == 1
        colors = fig.data[0].marker.color
        assert len(colors) == 4
