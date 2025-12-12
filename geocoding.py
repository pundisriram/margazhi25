"""
Geocoding service for venue locations with caching.
"""

import json
import os
from pathlib import Path
from typing import Optional, Tuple, Dict
from geopy.geocoders import GoogleV3
from geopy.distance import geodesic
from dotenv import load_dotenv

load_dotenv()


class VenueGeocoder:
    """Handles geocoding of venue names to coordinates with caching."""
    
    def __init__(self, cache_file: str = "geocoding_cache.json"):
        """Initialize the geocoder with cache file."""
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Dict] = self._load_cache()
        self.geocoder: Optional[GoogleV3] = None
        
        # Initialize Google Geocoding API if key is available
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if api_key:
            self.geocoder = GoogleV3(api_key=api_key)
    
    def _load_cache(self) -> Dict:
        """Load geocoding cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save geocoding cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def geocode(self, venue_name: str, city: str = "Chennai, India") -> Optional[Tuple[float, float]]:
        """
        Geocode a venue name to coordinates.
        
        Args:
            venue_name: Name of the venue
            city: City name to help with geocoding (default: Chennai, India)
        
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Check cache first
        cache_key = f"{venue_name}_{city}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return (cached['lat'], cached['lon'])
        
        # Try to geocode
        if not self.geocoder:
            # Fallback: return None if no API key
            return None
        
        try:
            # Try with city context first
            query = f"{venue_name}, {city}"
            location = self.geocoder.geocode(query, timeout=10)
            
            if location:
                coords = (location.latitude, location.longitude)
                # Cache the result
                self.cache[cache_key] = {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'address': location.address
                }
                self._save_cache()
                return coords
            
            # Try without city context
            location = self.geocoder.geocode(venue_name, timeout=10)
            if location:
                coords = (location.latitude, location.longitude)
                self.cache[cache_key] = {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'address': location.address
                }
                self._save_cache()
                return coords
        except Exception as e:
            print(f"Geocoding error for {venue_name}: {e}")
        
        return None
    
    def get_coordinates(self, venue_name: str, city: str = "Chennai, India") -> Optional[Tuple[float, float]]:
        """Alias for geocode method."""
        return self.geocode(venue_name, city)
    
    def get_address(self, venue_name: str, city: str = "Chennai, India") -> Optional[str]:
        """
        Get full address for a venue.
        
        Args:
            venue_name: Name of the venue
            city: City name
        
        Returns:
            Full address string or None
        """
        cache_key = f"{venue_name}_{city}"
        if cache_key in self.cache and 'address' in self.cache[cache_key]:
            return self.cache[cache_key]['address']
        
        # If not in cache, geocode to get address
        coords = self.geocode(venue_name, city)
        if coords:
            cache_key = f"{venue_name}_{city}"
            if cache_key in self.cache and 'address' in self.cache[cache_key]:
                return self.cache[cache_key]['address']
        
        return None
    
    def calculate_distance(self, venue1: str, venue2: str, city: str = "Chennai, India") -> Optional[float]:
        """
        Calculate distance between two venues in kilometers.
        
        Args:
            venue1: Name of first venue
            venue2: Name of second venue
            city: City name
        
        Returns:
            Distance in kilometers or None if venues can't be geocoded
        """
        coords1 = self.geocode(venue1, city)
        coords2 = self.geocode(venue2, city)
        
        if coords1 and coords2:
            return geodesic(coords1, coords2).kilometers
        
        return None
    
    def batch_geocode(self, venue_names: list, city: str = "Chennai, India") -> Dict[str, Optional[Tuple[float, float]]]:
        """
        Geocode multiple venues at once.
        
        Args:
            venue_names: List of venue names
            city: City name
        
        Returns:
            Dictionary mapping venue names to coordinates
        """
        results = {}
        for venue in venue_names:
            results[venue] = self.geocode(venue, city)
        return results
    
    def get_cached_venues(self) -> list:
        """Get list of all venues in cache."""
        venues = []
        for key in self.cache.keys():
            # Extract venue name (before the city part)
            venue = key.split('_')[0] if '_' in key else key
            if venue not in venues:
                venues.append(venue)
        return venues

