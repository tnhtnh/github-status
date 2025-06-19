"""
Unit tests for the DataProcessor class.
"""
import unittest
from datetime import datetime
from src.data_processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    """Test cases for the DataProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.data_processor = DataProcessor()
        
        # Sample valid response data
        self.valid_response_data = {
            "page": {
                "id": "kctbh9vrtdwd",
                "name": "GitHub",
                "url": "https://www.githubstatus.com",
                "updated_at": "2023-01-01T00:00:00Z"
            },
            "incidents": [
                {
                    "id": "incident-1",
                    "name": "Major Incident",
                    "status": "resolved",
                    "created_at": "2025-01-15T00:00:00Z",
                    "updated_at": "2025-01-15T01:00:00Z",
                    "impact": "major",
                    "incident_updates": []
                },
                {
                    "id": "incident-2",
                    "name": "Minor Incident",
                    "status": "resolved",
                    "created_at": "2025-01-20T00:00:00Z",
                    "updated_at": "2025-01-20T01:00:00Z",
                    "impact": "minor",
                    "incident_updates": []
                },
                {
                    "id": "incident-3",
                    "name": "Another Minor Incident",
                    "status": "resolved",
                    "created_at": "2025-02-05T00:00:00Z",
                    "updated_at": "2025-02-05T01:00:00Z",
                    "impact": "minor",
                    "incident_updates": []
                },
                {
                    "id": "incident-4",
                    "name": "No Impact Incident",
                    "status": "resolved",
                    "created_at": "2025-02-10T00:00:00Z",
                    "updated_at": "2025-02-10T01:00:00Z",
                    "impact": "none",
                    "incident_updates": []
                }
            ]
        }

    def test_categorize_by_severity(self):
        """Test that incidents are correctly categorized by severity."""
        # Test major incident
        major_incident = {
            "id": "test-incident-1",
            "impact": "major"
        }
        self.assertEqual(self.data_processor.categorize_by_severity(major_incident), "major")
        
        # Test minor incident
        minor_incident = {
            "id": "test-incident-2",
            "impact": "minor"
        }
        self.assertEqual(self.data_processor.categorize_by_severity(minor_incident), "minor")
        
        # Test none impact incident
        none_incident = {
            "id": "test-incident-3",
            "impact": "none"
        }
        self.assertEqual(self.data_processor.categorize_by_severity(none_incident), "none")

    def test_categorize_by_severity_invalid_incident(self):
        """Test handling of invalid incidents without impact field."""
        invalid_incident = {
            "id": "test-incident-4",
            # Missing 'impact' field
        }
        with self.assertRaises(ValueError):
            self.data_processor.categorize_by_severity(invalid_incident)

    def test_organize_by_month(self):
        """Test that incidents are correctly organized by month."""
        incidents = self.valid_response_data["incidents"]
        result = self.data_processor.organize_by_month(incidents)
        
        # Check the structure of the result
        self.assertIn("2025-01", result)
        self.assertIn("2025-02", result)
        
        # Check the counts for January 2025
        self.assertEqual(result["2025-01"]["major"], 1)
        self.assertEqual(result["2025-01"]["minor"], 1)
        self.assertEqual(result["2025-01"]["none"], 0)  # Normalized by _normalize_severity_categories
        
        # Check the counts for February 2025
        self.assertEqual(result["2025-02"]["major"], 0)  # Normalized by _normalize_severity_categories
        self.assertEqual(result["2025-02"]["minor"], 1)
        self.assertEqual(result["2025-02"]["none"], 1)

    def test_process_incidents(self):
        """Test the complete incident processing workflow."""
        result = self.data_processor.process_incidents(self.valid_response_data)
        
        # Check the structure of the result
        self.assertIn("2025-01", result)
        self.assertIn("2025-02", result)
        
        # Check that all severity categories are present in all months
        for month in result:
            self.assertIn("major", result[month])
            self.assertIn("minor", result[month])
            self.assertIn("none", result[month])
        
        # Check the total counts
        total_major = sum(month_data["major"] for month_data in result.values())
        total_minor = sum(month_data["minor"] for month_data in result.values())
        total_none = sum(month_data["none"] for month_data in result.values())
        
        self.assertEqual(total_major, 1)
        self.assertEqual(total_minor, 2)
        self.assertEqual(total_none, 1)

    def test_process_incidents_invalid_data(self):
        """Test handling of invalid data format."""
        invalid_data = {"page": {"id": "kctbh9vrtdwd"}}  # Missing 'incidents' key
        with self.assertRaises(ValueError):
            self.data_processor.process_incidents(invalid_data)

    def test_handle_missing_created_at(self):
        """Test handling of incidents with missing created_at field."""
        incidents = [
            {
                "id": "incident-1",
                "name": "Valid Incident",
                "created_at": "2025-01-15T00:00:00Z",
                "impact": "major"
            },
            {
                "id": "incident-2",
                "name": "Invalid Incident",
                # Missing 'created_at' field
                "impact": "minor"
            }
        ]
        
        result = self.data_processor.organize_by_month(incidents)
        
        # Only the valid incident should be processed
        self.assertIn("2025-01", result)
        self.assertEqual(result["2025-01"]["major"], 1)
        self.assertEqual(result["2025-01"]["minor"], 0)  # Normalized by _normalize_severity_categories

    def test_handle_invalid_date_format(self):
        """Test handling of incidents with invalid date format."""
        incidents = [
            {
                "id": "incident-1",
                "name": "Valid Incident",
                "created_at": "2025-01-15T00:00:00Z",
                "impact": "major"
            },
            {
                "id": "incident-2",
                "name": "Invalid Date Format",
                "created_at": "not-a-date",  # Invalid date format
                "impact": "minor"
            }
        ]
        
        result = self.data_processor.organize_by_month(incidents)
        
        # Only the valid incident should be processed
        self.assertIn("2025-01", result)
        self.assertEqual(result["2025-01"]["major"], 1)
        self.assertEqual(result["2025-01"]["minor"], 0)  # Normalized by _normalize_severity_categories

    def test_normalize_severity_categories(self):
        """Test that severity categories are normalized across months."""
        # Create data with different severity categories in different months
        monthly_data = {
            "2025-01": {"major": 1, "minor": 2},
            "2025-02": {"minor": 1, "none": 1},
            "2025-03": {"major": 2, "critical": 1}
        }
        
        # Normalize the data
        self.data_processor._normalize_severity_categories(monthly_data)
        
        # Check that all months have all severity categories
        for month in monthly_data:
            self.assertIn("major", monthly_data[month])
            self.assertIn("minor", monthly_data[month])
            self.assertIn("none", monthly_data[month])
            self.assertIn("critical", monthly_data[month])


if __name__ == '__main__':
    unittest.main()