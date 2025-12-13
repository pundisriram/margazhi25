"""
Date parsing utilities for handling relative dates and date ranges.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import re


def parse_relative_date(date_str: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse relative date expressions like "tomorrow", "next Friday", "this weekend", etc.
    
    Args:
        date_str: Date string to parse
        reference_date: Reference date (defaults to today)
    
    Returns:
        Parsed datetime or None if parsing fails
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    date_lower = date_str.lower().strip()
    
    # Basic relative dates
    if date_lower == 'today':
        return reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_lower == 'tomorrow':
        return (reference_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_lower == 'yesterday':
        return (reference_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # "in N days"
    in_days_match = re.search(r'in\s+(\d+)\s+days?', date_lower)
    if in_days_match:
        days = int(in_days_match.group(1))
        return (reference_date + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # "next week"
    if date_lower == 'next week':
        return (reference_date + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # "this weekend" or "next weekend"
    if 'weekend' in date_lower:
        saturday, sunday = get_weekend_dates(reference_date)
        if 'next' in date_lower:
            saturday, sunday = get_weekend_dates(reference_date + timedelta(days=7))
        # Return Saturday (start of weekend)
        return saturday
    
    # "next [day]" or "this [day]"
    day_names = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    for day_name, day_num in day_names.items():
        if day_name in date_lower:
            if 'next' in date_lower:
                return get_next_weekday(reference_date, day_num)
            elif 'this' in date_lower:
                # Get this week's occurrence
                days_ahead = day_num - reference_date.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                return (reference_date + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    return None


def parse_date_range(date_str: str, reference_date: Optional[datetime] = None) -> Optional[Tuple[datetime, datetime]]:
    """
    Parse date range expressions like "Dec 15-20", "December 15 to 20", etc.
    
    Args:
        date_str: Date range string to parse
        reference_date: Reference date for relative dates
    
    Returns:
        Tuple of (start_date, end_date) or None if parsing fails
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    date_str = date_str.strip()
    
    # Try patterns like "Dec 15-20" or "December 15 to 20"
    patterns = [
        (r'(\w+)\s+(\d+)\s*-\s*(\d+)', '%b %d'),  # Dec 15-20
        (r'(\w+)\s+(\d+)\s+to\s+(\d+)', '%b %d'),  # Dec 15 to 20
        (r'(\w+)\s+(\d+)\s*-\s*(\d+)', '%B %d'),  # December 15-20
        (r'(\w+)\s+(\d+)\s+to\s+(\d+)', '%B %d'),  # December 15 to 20
    ]
    
    for pattern, date_format in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            month_str = match.group(1)
            start_day = int(match.group(2))
            end_day = int(match.group(3))
            
            # Try to parse the month
            try:
                # Get current year or infer from reference_date
                year = reference_date.year
                
                # Try parsing with abbreviated month
                try:
                    month_date = datetime.strptime(f"{month_str} {start_day}", '%b %d')
                    month = month_date.month
                except:
                    month_date = datetime.strptime(f"{month_str} {start_day}", '%B %d')
                    month = month_date.month
                
                start_date = datetime(year, month, start_day)
                end_date = datetime(year, month, end_day)
                
                return (start_date, end_date)
            except:
                continue
    
    return None


def get_weekend_dates(reference_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get Saturday and Sunday dates for the week containing reference_date.
    
    Args:
        reference_date: Reference date
    
    Returns:
        Tuple of (saturday, sunday)
    """
    # Find Saturday (weekday 5)
    days_until_saturday = (5 - reference_date.weekday()) % 7
    if days_until_saturday == 0 and reference_date.weekday() != 5:
        days_until_saturday = 7
    
    saturday = (reference_date + timedelta(days=days_until_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = saturday + timedelta(days=1)
    
    return saturday, sunday


def get_next_weekday(reference_date: datetime, target_weekday: int) -> datetime:
    """
    Get the next occurrence of a specific weekday.
    
    Args:
        reference_date: Reference date
        target_weekday: Target weekday (0=Monday, 6=Sunday)
    
    Returns:
        Next occurrence of the target weekday
    """
    days_ahead = target_weekday - reference_date.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return (reference_date + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)

