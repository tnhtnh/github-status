"""
Unit tests for the Visualizer module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt
from src.visualizer import Visualizer

class TestVisualizer:
    """Test cases for the Visualizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visualizer = Visualizer()
        self.test_output_path = "test_visualization.png"
        
        # Sample processed data with multiple months and severity types
        self.sample_data = {
            "2025-01": {"major": 3, "minor": 5, "none": 1},
            "2025-02": {"major": 1, "minor": 2, "none": 0},
            "2025-03": {"major": 0, "minor": 4, "none": 2, "maintenance": 1}
        }
        
    def teardown_method(self):
        """Clean up after tests."""
        # Remove test output file if it exists
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)
    
    @patch("matplotlib.pyplot.savefig")
    def test_generate_visualization_with_valid_data(self, mock_savefig):
        """Test visualization generation with valid data."""
        # Call the method
        self.visualizer.generate_visualization(self.sample_data, self.test_output_path)
        
        # Check that savefig was called with the correct path
        mock_savefig.assert_called_once_with(self.test_output_path, format='png')
    
    def test_generate_visualization_with_empty_data(self):
        """Test visualization generation with empty data."""
        # Test with empty dictionary
        with pytest.raises(ValueError, match="No data provided"):
            self.visualizer.generate_visualization({}, self.test_output_path)
    
    @patch("matplotlib.pyplot.savefig")
    def test_generate_visualization_with_single_month(self, mock_savefig):
        """Test visualization generation with a single month of data."""
        # Single month data
        single_month_data = {
            "2025-01": {"major": 3, "minor": 5, "none": 1}
        }
        
        # Call the method
        self.visualizer.generate_visualization(single_month_data, self.test_output_path)
        
        # Check that savefig was called with the correct path
        mock_savefig.assert_called_once_with(self.test_output_path, format='png')
    
    @patch("matplotlib.pyplot.savefig")
    def test_generate_visualization_with_single_severity(self, mock_savefig):
        """Test visualization generation with a single severity type."""
        # Single severity data
        single_severity_data = {
            "2025-01": {"major": 3},
            "2025-02": {"major": 1},
            "2025-03": {"major": 2}
        }
        
        # Call the method
        self.visualizer.generate_visualization(single_severity_data, self.test_output_path)
        
        # Check that savefig was called with the correct path
        mock_savefig.assert_called_once_with(self.test_output_path, format='png')
    
    @patch("matplotlib.pyplot.savefig", side_effect=IOError("Permission denied"))
    def test_generate_visualization_with_io_error(self, mock_savefig):
        """Test handling of IO errors when saving the visualization."""
        # Call the method and expect an exception
        with pytest.raises(IOError):
            self.visualizer.generate_visualization(self.sample_data, "/invalid/path/test.png")
    
    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.bar")
    @patch("matplotlib.pyplot.savefig")
    def test_visualization_styling_elements(self, mock_savefig, mock_bar, mock_figure):
        """Test that the visualization includes proper styling elements."""
        # Call the method
        self.visualizer.generate_visualization(self.sample_data, self.test_output_path)
        
        # Check that figure was created with appropriate size and resolution
        mock_figure.assert_called_once_with(figsize=(12, 8), dpi=100)
        
        # Check that bar was called at least once (for each severity type)
        assert mock_bar.call_count >= len(set(severity for month_data in self.sample_data.values() for severity in month_data))
    
    def test_color_generation_for_unknown_severity(self):
        """Test that colors are generated consistently for unknown severity types."""
        # Get colors for the same severity multiple times
        color1 = self.visualizer._get_color_for_severity("unknown")
        color2 = self.visualizer._get_color_for_severity("unknown")
        
        # Colors should be consistent for the same severity
        assert color1 == color2
        
        # Different severities should get different colors
        color3 = self.visualizer._get_color_for_severity("different")
        assert color1 != color3