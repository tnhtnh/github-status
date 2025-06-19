"""
Simple script to test the DataFetcher class.
"""
from data_fetcher import DataFetcher

def main():
    """Test the DataFetcher class by fetching incidents from GitHub Status API."""
    fetcher = DataFetcher()
    try:
        data = fetcher.fetch_incidents()
        print(f"Successfully fetched {len(data['incidents'])} incidents")
        print(f"First incident: {data['incidents'][0]['name']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()