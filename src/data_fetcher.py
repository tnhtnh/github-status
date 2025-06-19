"""
Data Fetcher module for GitHub Incident Visualizer.

This module handles retrieving incident data from the GitHub Status API.
It provides functionality to make HTTP requests to the GitHub Status API
and handle any errors that may occur during the process.
"""
import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RequestError(Exception):
    """Exception raised when API request fails.
    
    This exception is raised when there is an issue with the HTTP request
    to the GitHub Status API, such as network connectivity problems,
    timeout issues, or server errors.
    """
    pass


class ParseError(Exception):
    """Exception raised when API response cannot be parsed.
    
    This exception is raised when the response from the GitHub Status API
    cannot be parsed as JSON or does not have the expected structure.
    """
    pass


class CacheError(Exception):
    """Exception raised when there is an issue with the cache operations.
    
    This exception is raised when there is a problem reading from or writing to
    the cache file, such as permission issues, disk space problems, or
    corruption of the cache file.
    """
    pass


class DataFetcher:
    """
    Handles fetching incident data from the GitHub Status API.
    
    This class is responsible for making HTTP requests to the GitHub Status API
    and handling any errors that may occur during the process. It also provides
    caching functionality to reduce API calls for frequent runs.
    """
    
    def __init__(self, api_url: str = "https://www.githubstatus.com/api/v2/incidents.json", 
                 cache_dir: str = ".cache", 
                 cache_ttl: int = 3600):
        """
        Initialize the DataFetcher with the GitHub Status API URL and caching options.
        
        Args:
            api_url (str): The URL of the GitHub Status API. Defaults to the official endpoint.
            cache_dir (str): Directory to store cache files. Defaults to ".cache".
            cache_ttl (int): Cache time-to-live in seconds. Defaults to 1 hour (3600 seconds).
        """
        self.api_url = api_url
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl
        self.logger = logger
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                self.logger.info(f"Created cache directory: {self.cache_dir}")
            except OSError as e:
                self.logger.warning(f"Failed to create cache directory: {str(e)}")
    
    def _get_cache_path(self) -> str:
        """
        Generate a cache file path based on the API URL.
        
        Returns:
            str: Path to the cache file
        """
        # Create a filename based on the API URL (removing special characters)
        filename = self.api_url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')
        return os.path.join(self.cache_dir, f"{filename}.json")
    
    def _load_from_cache(self) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Load incident data from cache if available and not expired.
        
        Returns:
            Tuple[Optional[Dict[str, Any]], bool]: Tuple containing:
                - The cached data if available and valid, None otherwise
                - Boolean indicating if the cache was used
        """
        cache_path = self._get_cache_path()
        
        if not os.path.exists(cache_path):
            self.logger.debug(f"Cache file not found: {cache_path}")
            return None, False
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
                # Check if the cache has metadata
                if not isinstance(cache_data, dict) or 'timestamp' not in cache_data or 'data' not in cache_data:
                    self.logger.warning("Cache file has invalid format, ignoring")
                    return None, False
                
                # Check if the cache is expired
                cache_time = datetime.fromtimestamp(cache_data['timestamp'])
                current_time = datetime.now()
                
                if (current_time - cache_time).total_seconds() > self.cache_ttl:
                    self.logger.info(f"Cache expired (created {cache_time.isoformat()})")
                    return None, False
                
                self.logger.info(f"Using cached data from {cache_time.isoformat()}")
                return cache_data['data'], True
                
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load cache file: {str(e)}")
            return None, False
    
    def _save_to_cache(self, data: Dict[str, Any]) -> bool:
        """
        Save incident data to cache.
        
        Args:
            data (Dict[str, Any]): The data to cache
            
        Returns:
            bool: True if the data was successfully cached, False otherwise
        """
        cache_path = self._get_cache_path()
        
        try:
            # Create a cache object with metadata
            cache_data = {
                'timestamp': time.time(),
                'data': data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
                
            self.logger.info(f"Data cached successfully at {cache_path}")
            return True
            
        except IOError as e:
            self.logger.warning(f"Failed to save data to cache: {str(e)}")
            return False
    
    def fetch_incidents(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetches incident data from GitHub Status API or from cache if available.
        
        Args:
            use_cache (bool): Whether to use cached data if available. Defaults to True.
        
        Returns:
            dict: Raw incident data from the API or cache
        
        Raises:
            RequestError: If the API request fails
            ParseError: If the response cannot be parsed
            CacheError: If there is an issue with cache operations
        """
        # Try to load from cache first if caching is enabled
        if use_cache:
            try:
                cached_data, cache_used = self._load_from_cache()
                if cache_used and cached_data is not None:
                    return cached_data
            except Exception as e:
                # Log the error but continue to fetch from API
                self.logger.warning(f"Cache error: {str(e)}")
        
        # If cache is not used or not available, fetch from API
        self.logger.info(f"Fetching incidents from {self.api_url}")
        
        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch data from GitHub Status API: {str(e)}"
            self.logger.error(error_msg)
            raise RequestError(error_msg) from e
        
        try:
            data = response.json()
            
            # Validate that the response has the expected structure
            if "incidents" not in data:
                error_msg = "Unexpected API response format: 'incidents' key not found"
                self.logger.error(error_msg)
                raise ParseError(error_msg)
                
            self.logger.info(f"Successfully fetched {len(data['incidents'])} incidents")
            
            # Save to cache if caching is enabled
            if use_cache:
                self._save_to_cache(data)
                
            return data
            
        except ValueError as e:
            error_msg = f"Failed to parse API response as JSON: {str(e)}"
            self.logger.error(error_msg)
            raise ParseError(error_msg) from e