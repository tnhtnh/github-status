#!/usr/bin/env python3
"""
Main module for GitHub Incident Visualizer.

This module serves as the entry point for the GitHub Incident Visualizer tool,
orchestrating the workflow between data fetching, processing, and visualization.
It handles command-line arguments, logging configuration, and the overall
execution flow of the application.
"""
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, NoReturn

from data_fetcher import DataFetcher, RequestError, ParseError
from data_processor import DataProcessor
from visualizer import Visualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"github_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the application.
    
    This function sets up the argument parser with all available command-line
    options and their descriptions, default values, and help text.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="GitHub Incident Visualizer - Generate visualizations of GitHub incidents by severity over time"
    )
    
    parser.add_argument(
        "--api-url",
        default="https://www.githubstatus.com/api/v2/incidents.json",
        help="URL of the GitHub Status API (default: %(default)s)"
    )
    
    parser.add_argument(
        "--output",
        default="github_incidents_visualization.png",
        help="Path where the visualization will be saved (default: %(default)s)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: %(default)s)"
    )
    
    # Caching options
    parser.add_argument(
        "--cache-dir",
        default=".cache",
        help="Directory to store cached API responses (default: %(default)s)"
    )
    
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="Cache time-to-live in seconds (default: %(default)s)"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching and always fetch fresh data"
    )
    
    # Keep the old cache-file argument for backward compatibility
    parser.add_argument(
        "--cache-file",
        default=None,
        help="Path to a JSON file to cache API responses (deprecated, use --cache-dir instead)"
    )
    
    # Visualization options
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="DPI (dots per inch) for the output image (default: %(default)s)"
    )
    
    parser.add_argument(
        "--fig-width",
        type=int,
        default=12,
        help="Width of the figure in inches (default: %(default)s)"
    )
    
    parser.add_argument(
        "--fig-height",
        type=int,
        default=8,
        help="Height of the figure in inches (default: %(default)s)"
    )
    
    return parser.parse_args()


def setup_logging(log_level: str) -> None:
    """
    Configure logging with the specified level.
    
    This function sets the root logger's level based on the provided log_level
    string. It validates the log level and updates the logger configuration.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Raises:
        ValueError: If the provided log_level is not a valid logging level
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Update the root logger's level
    logging.getLogger().setLevel(numeric_level)
    logger.info(f"Logging level set to {log_level}")


def load_cached_data(cache_file: str) -> Optional[Dict[str, Any]]:
    """
    Load cached incident data from a JSON file.
    
    This function attempts to read and parse a JSON file containing
    previously cached incident data. If the file doesn't exist or
    cannot be parsed, it returns None.
    
    Args:
        cache_file (str): Path to the cache file
        
    Returns:
        Optional[Dict[str, Any]]: Cached data if available, None otherwise
    """
    import json
    
    if not os.path.exists(cache_file):
        logger.info(f"Cache file {cache_file} not found")
        return None
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
            logger.info(f"Loaded cached data from {cache_file}")
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cache file {cache_file}: {str(e)}")
        return None


def save_cached_data(data: Dict[str, Any], cache_file: str) -> None:
    """
    Save incident data to a JSON cache file.
    
    This function serializes the provided incident data to JSON format
    and saves it to the specified cache file. It creates any necessary
    directories in the path if they don't exist.
    
    Args:
        data (Dict[str, Any]): Incident data to cache
        cache_file (str): Path to the cache file
    """
    import json
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else '.', exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            logger.info(f"Cached data saved to {cache_file}")
    except IOError as e:
        logger.warning(f"Failed to save cache file {cache_file}: {str(e)}")


def main() -> int:
    """
    Main entry point that orchestrates the workflow.
    
    This function coordinates the entire process:
    1. Parse command-line arguments
    2. Set up logging with the specified level
    3. Fetch data from GitHub Status API (or load from cache)
    4. Process and categorize the data
    5. Generate visualization
    6. Save the visualization to the specified location
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging with the specified level
    setup_logging(args.log_level)
    
    logger.info("Starting GitHub Incident Visualizer")
    
    try:
        # Initialize components
        data_fetcher = DataFetcher(
            api_url=args.api_url,
            cache_dir=args.cache_dir,
            cache_ttl=args.cache_ttl
        )
        data_processor = DataProcessor()
        visualizer = Visualizer(
            dpi=args.dpi,
            fig_width=args.fig_width,
            fig_height=args.fig_height
        )
        
        # Determine whether to use caching
        use_cache = not args.no_cache
        
        # Handle legacy cache file option for backward compatibility
        raw_data = None
        if args.cache_file and use_cache:
            logger.warning("--cache-file is deprecated, please use --cache-dir instead")
            raw_data = load_cached_data(args.cache_file)
        
        # Fetch data using the enhanced caching mechanism if not loaded from legacy cache
        if raw_data is None:
            logger.info(f"Fetching incident data from GitHub Status API (use_cache={use_cache})")
            raw_data = data_fetcher.fetch_incidents(use_cache=use_cache)
            
            # Save to legacy cache file if specified (for backward compatibility)
            if args.cache_file and use_cache:
                save_cached_data(raw_data, args.cache_file)
        
        # Process the incident data
        logger.info("Processing incident data")
        processed_data = data_processor.process_incidents(raw_data)
        
        # Generate the visualization
        logger.info(f"Generating visualization and saving to {args.output}")
        visualizer.generate_visualization(processed_data, args.output)
        
        logger.info("GitHub Incident Visualizer completed successfully")
        return 0
        
    except RequestError as e:
        logger.error(f"API request error: {str(e)}")
        return 1
    except ParseError as e:
        logger.error(f"API response parsing error: {str(e)}")
        return 1
    except ValueError as e:
        logger.error(f"Data processing error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())