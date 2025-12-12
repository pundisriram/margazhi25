"""
Route planning between venues with time considerations.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import googlemaps
import os
from dotenv import load_dotenv
from geocoding import VenueGeocoder
from data_loader import ConcertDataLoader
import pandas as pd

load_dotenv()


class RoutePlanner:
    """Plans routes between concert venues considering time constraints."""
    
    def __init__(self, geocoder: VenueGeocoder, data_loader: ConcertDataLoader):
        """Initialize route planner with geocoder and data loader."""
        self.geocoder = geocoder
        self.data_loader = data_loader
        self.gmaps_client: Optional[googlemaps.Client] = None
        
        # Initialize Google Maps client if API key is available
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if api_key:
            self.gmaps_client = googlemaps.Client(key=api_key)
    
    def plan_route(self, concerts: List[Dict], mode: str = "driving") -> Dict:
        """
        Plan optimal route between multiple concerts.
        
        Args:
            concerts: List of concert dictionaries with Date, Time, Venue
            mode: Travel mode ('driving', 'walking', 'transit')
        
        Returns:
            Dictionary with route information:
            - 'route': ordered list of concerts
            - 'total_distance': total distance in km
            - 'total_duration': total duration in minutes
            - 'directions': detailed directions between venues
            - 'warnings': any time conflicts or issues
        """
        if len(concerts) < 2:
            return {
                'route': concerts,
                'total_distance': 0,
                'total_duration': 0,
                'directions': [],
                'warnings': []
            }
        
        # Sort concerts by date and time
        sorted_concerts = self._sort_concerts_by_time(concerts)
        
        # Check for time conflicts
        warnings = self._check_time_conflicts(sorted_concerts)
        
        # Calculate routes between consecutive venues
        directions = []
        total_distance = 0
        total_duration = 0
        
        for i in range(len(sorted_concerts) - 1):
            venue1 = sorted_concerts[i]['Venue']
            venue2 = sorted_concerts[i + 1]['Venue']
            
            route_info = self._get_route_between_venues(venue1, venue2, mode)
            
            if route_info:
                directions.append({
                    'from': venue1,
                    'to': venue2,
                    'distance': route_info['distance'],
                    'duration': route_info['duration'],
                    'steps': route_info.get('steps', [])
                })
                total_distance += route_info['distance']
                total_duration += route_info['duration']
        
        return {
            'route': sorted_concerts,
            'total_distance': round(total_distance, 2),
            'total_duration': round(total_duration, 2),
            'directions': directions,
            'warnings': warnings
        }
    
    def _sort_concerts_by_time(self, concerts: List[Dict]) -> List[Dict]:
        """Sort concerts by date and time."""
        def get_datetime(concert):
            try:
                date = pd.to_datetime(concert.get('Date'))
                time_str = str(concert.get('Time', ''))
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':')[:2])
                    return date.replace(hour=hour, minute=minute)
                return date
            except:
                return pd.to_datetime(concert.get('Date'))
        
        return sorted(concerts, key=get_datetime)
    
    def _check_time_conflicts(self, concerts: List[Dict]) -> List[str]:
        """Check for time conflicts between concerts."""
        warnings = []
        
        for i in range(len(concerts) - 1):
            concert1 = concerts[i]
            concert2 = concerts[i + 1]
            
            try:
                date1 = pd.to_datetime(concert1.get('Date'))
                date2 = pd.to_datetime(concert2.get('Date'))
                
                # Parse times
                time1_str = str(concert1.get('Time', ''))
                time2_str = str(concert2.get('Time', ''))
                
                if ':' in time1_str and ':' in time2_str:
                    hour1, minute1 = map(int, time1_str.split(':')[:2])
                    hour2, minute2 = map(int, time2_str.split(':')[:2])
                    
                    datetime1 = date1.replace(hour=hour1, minute=minute1)
                    datetime2 = date2.replace(hour=hour2, minute=minute2)
                    
                    # Estimate concert duration (default 2 hours)
                    concert_duration = timedelta(hours=2)
                    end_time1 = datetime1 + concert_duration
                    
                    # Check if concerts overlap
                    if datetime2 < end_time1:
                        warnings.append(
                            f"Time conflict: {concert1.get('Venue')} concert may overlap with "
                            f"{concert2.get('Venue')} concert"
                        )
                    
                    # Check travel time
                    if self.gmaps_client:
                        coords1 = self.geocoder.geocode(concert1.get('Venue', ''))
                        coords2 = self.geocoder.geocode(concert2.get('Venue', ''))
                        
                        if coords1 and coords2:
                            # Estimate travel time (in minutes)
                            travel_time = self._estimate_travel_time(coords1, coords2)
                            
                            if datetime2 - end_time1 < timedelta(minutes=travel_time):
                                warnings.append(
                                    f"Tight schedule: Only {datetime2 - end_time1} between "
                                    f"{concert1.get('Venue')} and {concert2.get('Venue')}. "
                                    f"Estimated travel time: {travel_time} minutes"
                                )
            except Exception as e:
                warnings.append(f"Could not check time conflict: {e}")
        
        return warnings
    
    def _get_route_between_venues(self, venue1: str, venue2: str, mode: str = "driving") -> Optional[Dict]:
        """
        Get route information between two venues.
        
        Args:
            venue1: Name of first venue
            venue2: Name of second venue
            mode: Travel mode
        
        Returns:
            Dictionary with distance (km) and duration (minutes)
        """
        if not venue1 or not venue2:
            return None
        
        coords1 = self.geocoder.geocode(venue1)
        coords2 = self.geocoder.geocode(venue2)
        
        if not coords1 or not coords2:
            # Fallback: use straight-line distance if we have at least one coordinate
            from geopy.distance import geodesic
            if coords1 and coords2:
                distance_km = geodesic(coords1, coords2).kilometers
            else:
                # If we can't geocode, return None
                return None
            # Estimate 30 km/h average speed
            duration_min = (distance_km / 30) * 60
            return {
                'distance': distance_km,
                'duration': duration_min,
                'steps': []
            }
        
        # Use Google Maps API if available
        if self.gmaps_client:
            try:
                directions_result = self.gmaps_client.directions(
                    coords1,
                    coords2,
                    mode=mode,
                    alternatives=False
                )
                
                if directions_result:
                    route = directions_result[0]
                    leg = route['legs'][0]
                    
                    distance_km = leg['distance']['value'] / 1000  # Convert to km
                    duration_min = leg['duration']['value'] / 60  # Convert to minutes
                    
                    steps = []
                    for step in leg['steps']:
                        steps.append({
                            'instruction': step['html_instructions'],
                            'distance': step['distance']['text'],
                            'duration': step['duration']['text']
                        })
                    
                    return {
                        'distance': distance_km,
                        'duration': duration_min,
                        'steps': steps
                    }
            except Exception as e:
                print(f"Error getting directions: {e}")
        
        # Fallback: calculate straight-line distance
        from geopy.distance import geodesic
        distance_km = geodesic(coords1, coords2).kilometers
        
        # Estimate duration based on mode
        if mode == "walking":
            speed_kmh = 5
        elif mode == "transit":
            speed_kmh = 20
        else:  # driving
            speed_kmh = 30
        
        duration_min = (distance_km / speed_kmh) * 60
        
        return {
            'distance': distance_km,
            'duration': duration_min,
            'steps': []
        }
    
    def _estimate_travel_time(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """Estimate travel time between two coordinates in minutes."""
        from geopy.distance import geodesic
        distance_km = geodesic(coords1, coords2).kilometers
        # Assume 30 km/h average speed
        return (distance_km / 30) * 60
    
    def suggest_optimal_sequence(self, concerts: List[Dict], max_travel_time: int = 30) -> List[Dict]:
        """
        Suggest optimal sequence of concerts considering travel time.
        
        Args:
            concerts: List of concerts to sequence
            max_travel_time: Maximum acceptable travel time between concerts (minutes)
        
        Returns:
            List of concerts in optimal order
        """
        if len(concerts) <= 1:
            return concerts
        
        # Group by date first
        concerts_by_date = {}
        for concert in concerts:
            date = str(concert.get('Date', ''))
            if date not in concerts_by_date:
                concerts_by_date[date] = []
            concerts_by_date[date].append(concert)
        
        # For each date, optimize sequence
        optimized = []
        for date in sorted(concerts_by_date.keys()):
            date_concerts = concerts_by_date[date]
            optimized.extend(self._optimize_single_day(date_concerts, max_travel_time))
        
        return optimized
    
    def _optimize_single_day(self, concerts: List[Dict], max_travel_time: int) -> List[Dict]:
        """Optimize sequence for concerts on a single day."""
        if len(concerts) <= 1:
            return concerts
        
        # Sort by time
        sorted_concerts = self._sort_concerts_by_time(concerts)
        
        # Simple greedy algorithm: start with earliest, pick next closest venue
        optimized = [sorted_concerts[0]]
        remaining = sorted_concerts[1:]
        
        while remaining:
            current_venue = optimized[-1]['Venue']
            best_next = None
            min_travel = float('inf')
            
            for concert in remaining:
                travel_time = self._estimate_travel_time(
                    self.geocoder.geocode(current_venue) or (0, 0),
                    self.geocoder.geocode(concert['Venue']) or (0, 0)
                )
                
                if travel_time < min_travel and travel_time <= max_travel_time:
                    min_travel = travel_time
                    best_next = concert
            
            if best_next:
                optimized.append(best_next)
                remaining.remove(best_next)
            else:
                # If no suitable next concert, just add the earliest remaining
                optimized.append(remaining[0])
                remaining.remove(remaining[0])
        
        return optimized

