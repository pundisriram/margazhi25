"""
Data loading and search functions for concert schedules.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any


class ConcertDataLoader:
    """Manages loading and searching concert schedule data."""
    
    def __init__(self, csv_path: str = "combined_schedules.csv"):
        """Initialize the data loader with the CSV file path."""
        self.csv_path = Path(csv_path)
        self.df: Optional[pd.DataFrame] = None
        self._load_data()
    
    def _load_data(self):
        """Load the CSV file into a DataFrame."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Schedule file not found: {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path)
        
        # Convert Date column to datetime
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
        
        # Extract date components for easier filtering
        self.df['Year'] = self.df['Date'].dt.year
        self.df['Month'] = self.df['Date'].dt.month
        self.df['Day'] = self.df['Date'].dt.day
        self.df['DayOfWeek'] = self.df['Date'].dt.day_name()
        
        # Parse time for sorting
        self.df['TimeParsed'] = pd.to_datetime(
            self.df['Date'].dt.strftime('%Y-%m-%d') + ' ' + self.df['Time'].astype(str),
            errors='coerce'
        )
    
    def search_by_date(self, date: str) -> pd.DataFrame:
        """
        Search concerts by date.
        
        Args:
            date: Date string in various formats:
                - 'YYYY-MM-DD' (e.g., '2025-12-15')
                - 'Dec 15' or 'December 15'
                - '15 Dec' or '15 December'
                - 'MM/DD/YYYY' or 'DD/MM/YYYY'
                - Relative: 'today', 'tomorrow', 'yesterday'
        
        Returns:
            DataFrame with matching concerts
        """
        if self.df is None:
            return pd.DataFrame()
        
        from datetime import datetime, timedelta
        
        # Handle relative dates
        date_lower = date.lower().strip()
        if date_lower == 'today':
            target_date = datetime.now()
        elif date_lower == 'tomorrow':
            target_date = datetime.now() + timedelta(days=1)
        elif date_lower == 'yesterday':
            target_date = datetime.now() - timedelta(days=1)
        else:
            # Try multiple date formats
            date_formats = [
                '%Y-%m-%d',      # 2025-12-15
                '%b %d',          # Dec 15
                '%B %d',          # December 15
                '%d %b',          # 15 Dec
                '%d %B',          # 15 December
                '%m/%d/%Y',       # 12/15/2025
                '%d/%m/%Y',       # 15/12/2025
                '%m-%d-%Y',       # 12-15-2025
                '%d-%m-%Y',       # 15-12-2025
            ]
            
            target_date = None
            for fmt in date_formats:
                try:
                    target_date = datetime.strptime(date, fmt)
                    break
                except:
                    continue
            
            # If no format worked, try pandas flexible parsing
            if target_date is None:
                try:
                    target_date = pd.to_datetime(date)
                except:
                    return pd.DataFrame()
        
        # If we have a full date with year, match exactly
        if target_date.year != 1900:  # Default year when only month/day provided
            try:
                result = self.df[self.df['Date'] == target_date]
                if len(result) > 0:
                    return result.sort_values('TimeParsed').copy()
            except:
                pass
        
        # Match by month and day (for queries like "Dec 15" without year)
        result = self.df[
            (self.df['Month'] == target_date.month) & 
            (self.df['Day'] == target_date.day)
        ]
        
        return result.sort_values('TimeParsed').copy()
    
    def search_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Search concerts within a date range.
        
        Args:
            start_date: Start date string
            end_date: End date string
        
        Returns:
            DataFrame with matching concerts
        """
        if self.df is None:
            return pd.DataFrame()
        
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            result = self.df[(self.df['Date'] >= start) & (self.df['Date'] <= end)]
            return result.sort_values(['Date', 'TimeParsed']).copy()
        except:
            return pd.DataFrame()
    
    def search_by_artist(self, artist_name: str, case_sensitive: bool = False) -> pd.DataFrame:
        """
        Search concerts by artist name.
        
        Args:
            artist_name: Artist name to search for
            case_sensitive: Whether search should be case sensitive
        
        Returns:
            DataFrame with matching concerts
        """
        if self.df is None:
            return pd.DataFrame()
        
        if case_sensitive:
            mask = self.df['Artist(s)'].str.contains(artist_name, na=False)
        else:
            mask = self.df['Artist(s)'].str.contains(artist_name, case=False, na=False)
        
        result = self.df[mask].copy()
        return result.sort_values(['Date', 'TimeParsed'])
    
    def search_by_venue(self, venue_name: str, case_sensitive: bool = False) -> pd.DataFrame:
        """
        Search concerts by venue name.
        
        Args:
            venue_name: Venue name to search for
            case_sensitive: Whether search should be case sensitive
        
        Returns:
            DataFrame with matching concerts
        """
        if self.df is None:
            return pd.DataFrame()
        
        if case_sensitive:
            mask = self.df['Venue'].str.contains(venue_name, na=False)
        else:
            mask = self.df['Venue'].str.contains(venue_name, case=False, na=False)
        
        result = self.df[mask].copy()
        return result.sort_values(['Date', 'TimeParsed'])
    
    def search_by_location(self, area_name: str, case_sensitive: bool = False) -> pd.DataFrame:
        """
        Search concerts by location/area name (searches in venue names).
        
        Args:
            area_name: Area/location name (e.g., 'Mylapore', 'T. Nagar')
            case_sensitive: Whether search should be case sensitive
        
        Returns:
            DataFrame with matching concerts
        """
        if self.df is None:
            return pd.DataFrame()
        
        if case_sensitive:
            mask = self.df['Venue'].str.contains(area_name, na=False)
        else:
            mask = self.df['Venue'].str.contains(area_name, case=False, na=False)
        
        result = self.df[mask].copy()
        return result.sort_values(['Date', 'TimeParsed'])
    
    def get_concerts_on_date(self, date: str) -> pd.DataFrame:
        """Alias for search_by_date for backward compatibility."""
        return self.search_by_date(date)
    
    def search_by_time_of_day(self, time_of_day: str) -> pd.DataFrame:
        """
        Search concerts by time of day (morning, afternoon, evening, night).
        
        Args:
            time_of_day: 'morning', 'afternoon', 'evening', or 'night'
        
        Returns:
            DataFrame with matching concerts
        """
        if self.df is None:
            return pd.DataFrame()
        
        # Extract hour from time
        def get_hour(time_str):
            try:
                if ':' in str(time_str):
                    return int(str(time_str).split(':')[0])
                return None
            except:
                return None
        
        self.df['Hour'] = self.df['Time'].apply(get_hour)
        
        time_ranges = {
            'morning': (6, 12),
            'afternoon': (12, 17),
            'evening': (17, 21),
            'night': (21, 24)
        }
        
        if time_of_day.lower() not in time_ranges:
            return pd.DataFrame()
        
        start_hour, end_hour = time_ranges[time_of_day.lower()]
        mask = (self.df['Hour'] >= start_hour) & (self.df['Hour'] < end_hour)
        result = self.df[mask].copy()
        return result.sort_values(['Date', 'TimeParsed'])
    
    def combine_filters(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Combine multiple filters for complex queries.
        
        Args:
            filters: Dictionary with filter keys:
                - 'date': date string
                - 'date_range': tuple of (start_date, end_date)
                - 'artist': artist name
                - 'venue': venue name
                - 'location': area name
                - 'time_of_day': 'morning', 'afternoon', 'evening', 'night'
        
        Returns:
            DataFrame with concerts matching all filters
        """
        if self.df is None:
            return pd.DataFrame()
        
        result = self.df.copy()
        
        if 'date' in filters and filters['date']:
            date_result = self.search_by_date(filters['date'])
            if len(date_result) > 0:
                result = result[result.index.isin(date_result.index)]
            else:
                return pd.DataFrame()
        
        if 'date_range' in filters and filters['date_range']:
            start, end = filters['date_range']
            range_result = self.search_by_date_range(start, end)
            if len(range_result) > 0:
                result = result[result.index.isin(range_result.index)]
            else:
                return pd.DataFrame()
        
        if 'artist' in filters and filters['artist']:
            artist_result = self.search_by_artist(filters['artist'])
            if len(artist_result) > 0:
                result = result[result.index.isin(artist_result.index)]
            else:
                return pd.DataFrame()
        
        if 'venue' in filters and filters['venue']:
            venue_result = self.search_by_venue(filters['venue'])
            if len(venue_result) > 0:
                result = result[result.index.isin(venue_result.index)]
            else:
                return pd.DataFrame()
        
        if 'location' in filters and filters['location']:
            location_result = self.search_by_location(filters['location'])
            if len(location_result) > 0:
                result = result[result.index.isin(location_result.index)]
            else:
                return pd.DataFrame()
        
        if 'time_of_day' in filters and filters['time_of_day']:
            time_result = self.search_by_time_of_day(filters['time_of_day'])
            if len(time_result) > 0:
                result = result[result.index.isin(time_result.index)]
            else:
                return pd.DataFrame()
        
        return result.sort_values(['Date', 'TimeParsed']).copy()
    
    def get_all_venues(self) -> List[str]:
        """Get list of all unique venues."""
        if self.df is None:
            return []
        return sorted(self.df['Venue'].dropna().unique().tolist())
    
    def get_all_artists(self) -> List[str]:
        """Get list of all unique artists (may have duplicates due to multiple artists per concert)."""
        if self.df is None:
            return []
        artists = []
        for artist_str in self.df['Artist(s)'].dropna():
            # Split by common separators
            for sep in [';', ',', '&', 'and']:
                if sep in str(artist_str):
                    artists.extend([a.strip() for a in str(artist_str).split(sep)])
                    break
            else:
                artists.append(str(artist_str).strip())
        return sorted(list(set(artists)))
    
    def get_date_range(self) -> tuple:
        """Get the date range of all concerts."""
        if self.df is None or len(self.df) == 0:
            return None, None
        return self.df['Date'].min(), self.df['Date'].max()
    
    def get_concert_by_index(self, index: int) -> Optional[Dict]:
        """Get a single concert by its index."""
        if self.df is None or index not in self.df.index:
            return None
        
        row = self.df.loc[index]
        return {
            'Date': row['Date'],
            'Time': row['Time'],
            'Artist': row['Artist(s)'],
            'Instruments': row['Instruments/Details'],
            'Venue': row['Venue'],
            'Source': row['Source']
        }

