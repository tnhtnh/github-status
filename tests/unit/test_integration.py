"""
Integration tests for GitHub Incident Visualizer.

This module contains tests that verify the end-to-end functionality
of the GitHub Incident Visualizer tool using mock data.
"""
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import sys
import matplotlib
# Use non-interactive backend for testing
matplotlib.use('Agg')

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from data_fetcher import DataFetcher
from data_processor import DataProcessor
from visualizer import Visualizer
import main


class TestIntegration(unittest.TestCase):
    """Integration tests for the GitHub Incident Visualizer."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample mock data that matches the GitHub Status API format
        self.mock_data = {
            "page": {
                "id": "kctbh9vrtdwd",
                "name": "GitHub",
                "url": "https://www.githubstatus.com",
                "time_zone": "Etc/UTC",
                "updated_at": "2025-06-18T22:01:45.541Z"
            },
            "incidents": [
                {
                    "id": "9qcwpy3ckdrf",
                    "name": "Partial Actions Cache degradation",
                    "status": "resolved",
                    "created_at": "2025-06-18T16:46:25.922Z",
                    "updated_at": "2025-06-18T18:47:45.532Z",
                    "monitoring_at": None,
                    "resolved_at": "2025-06-18T18:47:45.515Z",
                    "impact": "minor",
                    "shortlink": "https://stspg.io/p4t2vlt0z8w9",
                    "started_at": "2025-06-18T16:46:25.914Z",
                    "page_id": "kctbh9vrtdwd",
                    "incident_updates": []
                },
                {
                    "id": "7kltzm6r774q",
                    "name": "Partial Degradation in Issues Experience",
                    "status": "resolved",
                    "created_at": "2025-05-18T16:21:00.833Z",
                    "updated_at": "2025-05-18T17:42:18.035Z",
                    "monitoring_at": None,
                    "resolved_at": "2025-05-18T17:42:18.022Z",
                    "impact": "minor",
                    "shortlink": "https://stspg.io/qvwwzdnyvlj4",
                    "started_at": "2025-05-18T16:21:00.827Z",
                    "page_id": "kctbh9vrtdwd",
                    "incident_updates": []
                },
                {
                    "id": "y7lb2rg4btd7",
                    "name": "Incident with multiple GitHub services",
                    "status": "resolved",
                    "created_at": "2025-04-17T19:42:56.663Z",
                    "updated_at": "2025-04-18T22:01:45.538Z",
                    "monitoring_at": None,
                    "resolved_at": "2025-04-17T20:22:50.000Z",
                    "impact": "major",
                    "shortlink": "https://stspg.io/8h22csvk9l0x",
                    "started_at": "2025-04-17T20:22:50.000Z",
                    "page_id": "kctbh9vrtdwd",
                    "incident_updates": []
                }
            ]
        }

    def test_end_to_end_workflow(self):
        """Test the complete workflow from data fetching to visualization."""
        # Create a temporary file for the output visualization
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_output:
            # Mock the DataFetcher to return our sample data
            with patch.object(DataFetcher, 'fetch_incidents', return_value=self.mock_data):
                # Run the main function with mocked arguments
                with patch('sys.argv', ['main.py', '--output', temp_output.name]):
                    # Execute the main function
                    exit_code = main.main()
                    
                    # Check that the main function completed successfully
                    self.assertEqual(exit_code, 0)
                    
                    # Check that the output file was created and has content
                    self.assertTrue(os.path.exists(temp_output.name))
                    self.assertGreater(os.path.getsize(temp_output.name), 0)

    def test_workflow_with_cache(self):
        """Test the workflow with caching functionality."""
        # Create temporary files for the cache and output
        with tempfile.NamedTemporaryFile(suffix='.json') as temp_cache:
            with tempfile.NamedTemporaryFile(suffix='.png') as temp_output:
                # First run: fetch from API and save to cache
                with patch.object(DataFetcher, 'fetch_incidents', return_value=self.mock_data):
                    with patch('sys.argv', [
                        'main.py',
                        '--output', temp_output.name,
                        '--cache-file', temp_cache.name
                    ]):
                        # Execute the main function
                        exit_code = main.main()
                        self.assertEqual(exit_code, 0)
                
                # Second run: should load from cache instead of calling the API
                mock_fetcher = MagicMock()
                with patch.object(DataFetcher, 'fetch_incidents', mock_fetcher):
                    with patch('sys.argv', [
                        'main.py',
                        '--output', temp_output.name,
                        '--cache-file', temp_cache.name
                    ]):
                        # Execute the main function again
                        exit_code = main.main()
                        self.assertEqual(exit_code, 0)
                        
                        # Verify that fetch_incidents was not called
                        mock_fetcher.assert_not_called()

    def test_error_handling(self):
        """Test error handling in the workflow."""
        # Create a temporary file for the output visualization
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_output:
            # Test handling of RequestError
            with patch.object(DataFetcher, 'fetch_incidents', side_effect=Exception("API connection failed")):
                with patch('sys.argv', ['main.py', '--output', temp_output.name]):
                    # Execute the main function
                    exit_code = main.main()
                    
                    # Check that the main function returned an error code
                    self.assertEqual(exit_code, 1)

    def test_command_line_arguments(self):
        """Test parsing of command-line arguments."""
        # Test with custom API URL and output path
        with patch('sys.argv', [
            'main.py',
            '--api-url', 'https://custom-api.example.com',
            '--output', 'custom-output.png',
            '--log-level', 'DEBUG'
        ]):
            args = main.parse_arguments()
            self.assertEqual(args.api_url, 'https://custom-api.example.com')
            self.assertEqual(args.output, 'custom-output.png')
            self.assertEqual(args.log_level, 'DEBUG')


if __name__ == '__main__':
    unittest.main()