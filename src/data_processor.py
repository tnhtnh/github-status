"""
Data Processor module for GitHub Incident Visualizer.

This module handles processing and categorizing GitHub incident data.
It provides functionality to categorize incidents by severity and
organize them by month for visualization purposes.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles processing and categorizing GitHub incident data.
    
    This class is responsible for categorizing incidents by severity
    and organizing them by month for visualization.
    """
    
    def __init__(self):
        """Initialize the DataProcessor."""
        self.logger = logger
    
    def process_incidents(self, raw_data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """
        Process and categorize incident data by severity and time.
        
        Args:
            raw_data (dict): Raw incident data from the API
            
        Returns:
            dict: Processed data organized by month and severity
            
        Example return format:
        {
            '2025-01': {'major': 3, 'minor': 5, 'none': 1},
            '2025-02': {'major': 1, 'minor': 2, 'none': 0},
            ...
        }
        
        Raises:
            ValueError: If the raw_data is not in the expected format
        """
        if not isinstance(raw_data, dict) or 'incidents' not in raw_data:
            error_msg = "Invalid data format: 'incidents' key not found in raw data"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        incidents = raw_data['incidents']
        self.logger.info(f"Processing {len(incidents)} incidents")
        
        # Process each incident and organize by month
        return self.organize_by_month(incidents)
    
    def categorize_by_severity(self, incident: Dict[str, Any]) -> str:
        """
        Categorize an incident by its severity.
        
        Args:
            incident (dict): Single incident data
            
        Returns:
            str: Severity category ('major', 'minor', 'none', etc.)
            
        Raises:
            ValueError: If the incident doesn't have an 'impact' field
        """
        if not isinstance(incident, dict) or 'impact' not in incident:
            error_msg = "Invalid incident format: 'impact' field not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Return the impact value directly as the severity category
        # GitHub API uses 'major', 'minor', 'none', etc.
        return incident['impact']
    
    def organize_by_month(self, incidents: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Organize incidents by month and count by severity.
        
        Args:
            incidents (list): List of incident data
            
        Returns:
            dict: Incidents organized by month with counts by severity
            
        Example:
        {
            '2025-01': {'major': 3, 'minor': 5, 'none': 1},
            '2025-02': {'major': 1, 'minor': 2, 'none': 0},
            ...
        }
        """
        monthly_data = {}
        
        for incident in incidents:
            try:
                # Use the initial creation date for time categorization
                if 'created_at' not in incident:
                    self.logger.warning(f"Incident {incident.get('id', 'unknown')} missing 'created_at' field, skipping")
                    continue
                
                # Parse the date and extract the year-month
                created_date = datetime.fromisoformat(incident['created_at'].replace('Z', '+00:00'))
                month_key = f"{created_date.year}-{created_date.month:02d}"
                
                # Get the severity category
                severity = self.categorize_by_severity(incident)
                
                # Initialize the month entry if it doesn't exist
                if month_key not in monthly_data:
                    monthly_data[month_key] = {}
                
                # Initialize the severity count if it doesn't exist
                if severity not in monthly_data[month_key]:
                    monthly_data[month_key][severity] = 0
                
                # Increment the count for this severity in this month
                monthly_data[month_key][severity] += 1
                
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Error processing incident {incident.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Ensure all months have entries for all severity types
        self._normalize_severity_categories(monthly_data)
        
        self.logger.info(f"Organized incidents by month: {len(monthly_data)} months processed")
        return monthly_data
    
    def _normalize_severity_categories(self, monthly_data: Dict[str, Dict[str, int]]) -> None:
        """
        Ensure all months have entries for all severity categories.
        
        This helps ensure consistent data structure for visualization.
        
        Args:
            monthly_data (dict): Data organized by month with counts by severity
            
        Returns:
            None: The monthly_data dict is modified in place
        """
        # Find all unique severity categories across all months
        all_severities = set()
        for month_data in monthly_data.values():
            all_severities.update(month_data.keys())
        
        # Ensure each month has an entry for each severity category
        for month_key in monthly_data:
            for severity in all_severities:
                if severity not in monthly_data[month_key]:
                    monthly_data[month_key][severity] = 0