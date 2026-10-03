"""Unit tests for dashboard data_loader module."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from dashboard.utils.data_loader import (
    _demo_path,
    load_calibration_curves,
    load_device_funnel,
    load_logistic_coefficients,
    load_model_features,
    load_model_metrics,
    load_pr_curves,
    load_test_deciles,
    load_tracking_alerts,
    load_validation_comparison,
    load_weekly_conversion,
)


class TestDemoPath:
    """Tests for _demo_path helper function."""

    def test_demo_path_returns_path(self):
        """Test that _demo_path returns a Path object."""
        with patch("dashboard.utils.data_loader._DEMO", Path("/fake/demo")):
            result = _demo_path("test.csv")
            assert isinstance(result, Path)
            assert result.name == "test.csv"

    @patch("dashboard.utils.data_loader.st")
    def test_demo_path_missing_file_shows_error(self, mock_st):
        """Test that missing file triggers Streamlit error."""
        with patch("dashboard.utils.data_loader._DEMO", Path("/nonexistent/path")):
            _demo_path("missing.csv")
            assert mock_st.error.called
            assert mock_st.stop.called


class TestSmallCSVLoaders:
    """Tests for small CSV loader functions."""

    @pytest.fixture
    def mock_csv_data(self):
        """Create mock CSV data for testing."""
        return pd.DataFrame({
            "device_category": ["mobile", "desktop", "tablet"],
            "overall_purchase_rate": [6.26, 5.91, 5.50],
        })

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_device_funnel(self, mock_read_csv, mock_demo_path, mock_csv_data):
        """Test device funnel loader."""
        mock_demo_path.return_value = Path("device_funnel.csv")
        mock_read_csv.return_value = mock_csv_data

        result = load_device_funnel()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "device_category" in result.columns
        mock_read_csv.assert_called_once()

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_weekly_conversion_parsing(self, mock_read_csv, mock_demo_path):
        """Test weekly conversion loader with date parsing."""
        mock_csv = pd.DataFrame({
            "week_start": ["2020-11-01", "2020-11-08"],
            "purchase_conversion_rate": [7.5, 8.0],
        })
        mock_demo_path.return_value = Path("weekly_conversion.csv")
        mock_read_csv.return_value = mock_csv

        result = load_weekly_conversion()

        assert isinstance(result, pd.DataFrame)
        assert pd.api.types.is_datetime64_any_dtype(result["week_start"])
        mock_read_csv.assert_called_once_with(
            mock_demo_path.return_value,
            parse_dates=["week_start"],
        )

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_tracking_alerts_parsing(self, mock_read_csv, mock_demo_path):
        """Test tracking alerts loader with date parsing."""
        mock_csv = pd.DataFrame({
            "date": ["2020-11-21", "2020-11-22"],
            "event_volume_ratio": [0.0, 0.0],
        })
        mock_demo_path.return_value = Path("tracking_alerts.csv")
        mock_read_csv.return_value = mock_csv

        result = load_tracking_alerts()

        assert isinstance(result, pd.DataFrame)
        assert pd.api.types.is_datetime64_any_dtype(result["date"])


class TestModelArtifactLoaders:
    """Tests for model artifact loader functions."""

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("builtins.open")
    def test_load_model_metrics(self, mock_open, mock_demo_path):
        """Test model metrics JSON loader."""
        mock_metrics = {
            "test_pr_auc": 0.1402,
            "test_roc_auc": 0.7876,
            "brier_score": 0.0457,
        }
        mock_demo_path.return_value = Path("model_metrics.json")
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_metrics)

        result = load_model_metrics()

        assert isinstance(result, dict)
        assert result["test_pr_auc"] == 0.1402
        assert len(result) == 3

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_validation_comparison(self, mock_read_csv, mock_demo_path):
        """Test validation comparison loader."""
        mock_csv = pd.DataFrame({
            "model": ["Dummy", "LogisticRegression", "RandomForest"],
            "pr_auc": [0.05, 0.12, 0.14],
        })
        mock_demo_path.return_value = Path("model_validation_comparison.csv")
        mock_read_csv.return_value = mock_csv

        result = load_validation_comparison()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "model" in result.columns

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_pr_curves(self, mock_read_csv, mock_demo_path):
        """Test PR curves loader."""
        mock_csv = pd.DataFrame({
            "model": ["LogisticRegression", "RandomForest"],
            "recall": [0.5, 0.6],
            "precision": [0.7, 0.8],
        })
        mock_demo_path.return_value = Path("model_pr_curves.csv")
        mock_read_csv.return_value = mock_csv

        result = load_pr_curves()

        assert isinstance(result, pd.DataFrame)
        assert "recall" in result.columns
        assert "precision" in result.columns

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_calibration_curves(self, mock_read_csv, mock_demo_path):
        """Test calibration curves loader."""
        mock_csv = pd.DataFrame({
            "calibration_type": ["uncalibrated", "sigmoid_calibrated"],
            "mean_predicted_probability": [0.1, 0.2],
            "observed_positive_fraction": [0.15, 0.18],
        })
        mock_demo_path.return_value = Path("model_calibration_curves.csv")
        mock_read_csv.return_value = mock_csv

        result = load_calibration_curves()

        assert isinstance(result, pd.DataFrame)
        assert "calibration_type" in result.columns

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_test_deciles(self, mock_read_csv, mock_demo_path):
        """Test test deciles loader."""
        mock_csv = pd.DataFrame({
            "risk_decile": list(range(1, 11)),
            "purchase_rate": [0.05 + i * 0.01 for i in range(10)],
            "overall_test_purchase_rate": [0.05] * 10,
        })
        mock_demo_path.return_value = Path("model_test_deciles.csv")
        mock_read_csv.return_value = mock_csv

        result = load_test_deciles()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10
        assert "risk_decile" in result.columns

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    def test_load_logistic_coefficients(self, mock_read_csv, mock_demo_path):
        """Test logistic coefficients loader."""
        mock_csv = pd.DataFrame({
            "feature": ["feature1", "feature2"],
            "coefficient": [0.5, -0.3],
            "absolute_coefficient": [0.5, 0.3],
            "direction": ["positive", "negative"],
        })
        mock_demo_path.return_value = Path("model_logistic_coefficients.csv")
        mock_read_csv.return_value = mock_csv

        result = load_logistic_coefficients()

        assert isinstance(result, pd.DataFrame)
        assert "feature" in result.columns
        assert "coefficient" in result.columns


class TestLargeFeatureFile:
    """Tests for large model features file loader."""

    @patch("dashboard.utils.data_loader._demo_path")
    @patch("dashboard.utils.data_loader.pd.read_csv")
    @patch("dashboard.utils.data_loader.st.cache_data")
    def test_load_model_features_with_compression(self, mock_cache, mock_read_csv, mock_demo_path):
        """Test model features loader with gzip compression."""
        mock_csv = pd.DataFrame({
            "session_date": pd.to_datetime(["2020-11-01", "2020-11-02"]),
            "purchased_later_in_session": [0, 1],
        })
        mock_demo_path.return_value = Path("model_features.csv.gz")
        mock_read_csv.return_value = mock_csv
        mock_cache.return_value.__call__ = lambda f: f

        result = load_model_features()

        assert isinstance(result, pd.DataFrame)
        assert pd.api.types.is_datetime64_any_dtype(result["session_date"])
        mock_read_csv.assert_called_once()
        call_kwargs = mock_read_csv.call_args[1]
        assert call_kwargs["compression"] == "gzip"
