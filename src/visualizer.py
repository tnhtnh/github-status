"""
Visualizer module for GitHub Incident Visualizer.

This module handles the generation of visualizations from processed incident data.
It creates visual representations of GitHub incidents by severity over time
using matplotlib to generate charts and graphs.
"""
import logging
import os
from typing import Dict, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import matplotlib.colors as mcolors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Visualizer:
    """
    Handles generation of visualizations from processed incident data.
    
    This class is responsible for creating visual representations of GitHub
    incidents by severity over time.
    """
    
    def __init__(self, dpi: int = 150, fig_width: int = 12, fig_height: int = 8):
        """
        Initialize the Visualizer with customizable visualization parameters.
        
        Args:
            dpi (int): Dots per inch for the output image. Higher values result in larger, more detailed images.
            fig_width (int): Width of the figure in inches.
            fig_height (int): Height of the figure in inches.
        """
        self.logger = logger
        self.dpi = dpi
        self.fig_width = fig_width
        self.fig_height = fig_height
        
        # Define a color map for different severity types with improved accessibility
        # These colors are chosen to be distinguishable for people with color vision deficiencies
        self.color_map = {
            'major': '#E63946',    # Bright red - stands out for critical issues
            'minor': '#FFB703',    # Amber yellow - visible but less alarming
            'none': '#2A9D8F',     # Teal green - calming color for no severity
            'maintenance': '#457B9D', # Steel blue - neutral for planned maintenance
            'critical': '#9D0208',   # Dark red - very serious issues
        }
        
    def generate_visualization(self, processed_data: Dict[str, Dict[str, int]], output_path: str) -> None:
        """
        Generate a PNG visualization of incidents by severity over time.
        
        Args:
            processed_data (dict): Processed incident data organized by month and severity
            output_path (str): Path where the PNG image will be saved
            
        Returns:
            None
            
        Raises:
            ValueError: If the processed_data is empty or not in the expected format
            IOError: If there's an issue saving the image to the specified path
        """
        if not processed_data:
            error_msg = "Cannot generate visualization: No data provided"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.info(f"Generating visualization with {len(processed_data)} months of data")
        
        try:
            # Use plt.style for a more modern and readable appearance
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Create a new figure with appropriate size and resolution
            plt.figure(figsize=(self.fig_width, self.fig_height), dpi=self.dpi)
            
            # Sort months chronologically
            sorted_months = sorted(processed_data.keys())
            
            if not sorted_months:
                error_msg = "Cannot generate visualization: No month data available"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Convert month strings to datetime objects for better x-axis formatting
            x_dates = [datetime.strptime(month, "%Y-%m") for month in sorted_months]
            
            # Get all unique severity types across all months
            all_severities = set()
            for month_data in processed_data.values():
                all_severities.update(month_data.keys())
            
            # Sort severities by importance for better visual hierarchy
            # This ensures critical/major incidents are at the bottom of the stack and more visible
            severity_order = ['critical', 'major', 'minor', 'maintenance', 'none']
            sorted_severities = sorted(
                all_severities,
                key=lambda x: severity_order.index(x) if x in severity_order else 999
            )
            
            # Create a stacked bar chart
            bottom = [0] * len(sorted_months)
            bars = []
            
            # Plot each severity type as a layer in the stack
            for severity in sorted_severities:
                # Extract counts for this severity across all months
                counts = [processed_data[month].get(severity, 0) for month in sorted_months]
                
                # Get color for this severity, or generate one if not in our map
                color = self.color_map.get(severity, self._get_color_for_severity(severity))
                
                # Plot this severity layer with improved styling
                bar = plt.bar(
                    x_dates, 
                    counts, 
                    bottom=bottom, 
                    label=severity.capitalize(), 
                    color=color,
                    edgecolor='white',  # Add white edges for better separation
                    linewidth=0.5,      # Thin edge lines
                    alpha=0.9           # Slight transparency for better layering
                )
                bars.append(bar)
                
                # Update the bottom values for the next layer
                bottom = [b + c for b, c in zip(bottom, counts)]
            
            # Configure the x-axis to show months nicely
            ax = plt.gca()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45, ha='right')  # Improved readability with right alignment
            
            # Add grid lines for better readability of values
            ax.yaxis.grid(True, linestyle='--', alpha=0.7)
            
            # Add data labels for better readability
            self._add_data_labels(bars, x_dates, processed_data, sorted_months, sorted_severities)
            
            # Add labels and title with improved styling
            plt.xlabel('Month', fontsize=12, fontweight='bold')
            plt.ylabel('Number of Incidents', fontsize=12, fontweight='bold')
            plt.title('GitHub Incidents by Severity Over Time', fontsize=16, fontweight='bold', pad=20)
            
            # Add a legend with improved positioning and styling
            legend = plt.legend(
                title='Severity',
                title_fontsize=12,
                fontsize=10,
                loc='upper right',
                frameon=True,
                framealpha=0.9,
                edgecolor='lightgray'
            )
            
            # Add a text annotation with the total number of incidents
            total_incidents = sum(sum(month_data.values()) for month_data in processed_data.values())
            plt.figtext(
                0.02, 0.02, 
                f'Total incidents: {total_incidents}', 
                fontsize=9, 
                style='italic'
            )
            
            # Adjust layout to make room for the rotated x-axis labels and annotations
            plt.tight_layout()
            
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Save the figure with optimized settings
            plt.savefig(
                output_path, 
                format='png',
                dpi=self.dpi,
                bbox_inches='tight',  # Trim extra whitespace
                optimize=True         # Apply optimization
            )
            self.logger.info(f"Visualization saved to {output_path}")
            
            # Close the figure to free memory
            plt.close()
            
        except Exception as e:
            error_msg = f"Error generating visualization: {str(e)}"
            self.logger.error(error_msg)
            raise
    
    def _add_data_labels(self, bars, x_dates, processed_data, sorted_months, sorted_severities):
        """
        Add data labels to the bars for better readability.
        
        This method adds count labels to bars that are large enough to be significant.
        
        Args:
            bars: List of bar container objects from plt.bar()
            x_dates: List of datetime objects for the x-axis
            processed_data: The processed incident data
            sorted_months: List of sorted month strings
            sorted_severities: List of sorted severity types
        """
        # Calculate the total height of each stack
        totals = [sum(processed_data[month].values()) for month in sorted_months]
        max_total = max(totals) if totals else 0
        
        # Only add labels to bars that are significant enough (at least 10% of the max height)
        threshold = max_total * 0.1
        
        for i, severity in enumerate(sorted_severities):
            for j, month in enumerate(sorted_months):
                count = processed_data[month].get(severity, 0)
                if count >= threshold:  # Only label significant bars
                    # Get the y position (middle of the bar)
                    height = bars[i][j].get_height()
                    y_pos = bars[i][j].get_y() + height / 2
                    
                    # Add the label
                    plt.text(
                        x_dates[j], y_pos,
                        str(count),
                        ha='center',
                        va='center',
                        fontsize=9,
                        fontweight='bold',
                        color='white'
                    )
            
    def _get_color_for_severity(self, severity: str) -> Tuple[float, float, float]:
        """
        Generate a color for a severity type not in the predefined color map.
        
        This method creates a consistent color based on the severity name
        for any severity types not included in the predefined color map.
        The colors are chosen to be distinguishable and accessible.
        
        Args:
            severity (str): The severity type name
            
        Returns:
            Tuple[float, float, float]: An RGB color tuple
        """
        # Use a hash of the severity name to generate a consistent color
        # We use a different approach to ensure better color separation
        severity_hash = hash(severity) % 1000 / 1000.0
        
        # Use a color palette that's more accessible and distinguishable
        # Adjust saturation and value for better visibility
        hue = severity_hash
        saturation = 0.7 + (hash(severity) % 300) / 1000.0  # Range: 0.7-0.999
        value = 0.8 + (hash(severity[::-1]) % 200) / 1000.0  # Range: 0.8-0.999
        
        return mcolors.hsv_to_rgb([hue, saturation, value])