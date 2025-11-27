"""
Analysis functions for GMR (Global Movement Records) data.
Provides zone conversion, frequency, and missing entrance analysis.
"""

import pandas as pd
from typing import Tuple


def calculate_conversion_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate conversion rates from Zone 1 (entrance) to other zones.
    
    Returns count of people who visited BOTH Zone 1 AND each other zone.
    
    Args:
        df: DataFrame with columns: global_object_id, zone_id
        
    Returns:
        DataFrame with columns: Zone ID, Conversion Count
    """
    # Get people who visited Zone 1
    zone1_visitors = set(df[df['zone_id'] == 1]['global_object_id'].unique())
    
    # Group by global_object_id to get zones visited by each person
    person_zones = df.groupby('global_object_id')['zone_id'].apply(set).to_dict()
    
    # Get all unique zones except Zone 1
    all_zones = sorted([z for z in df['zone_id'].unique() if z != 1])
    
    # Calculate conversion for each zone
    conversion_data = []
    for zone in all_zones:
        # Count people who visited both Zone 1 AND this zone
        zone_visitors = set(df[df['zone_id'] == zone]['global_object_id'].unique())
        conversion_count = len(zone1_visitors.intersection(zone_visitors))
        conversion_data.append({
            'Zone ID': int(zone),
            'Conversion Count': conversion_count
        })
    
    return pd.DataFrame(conversion_data)


def calculate_zone_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate frequency distribution of unique zones visited per person.
    Only includes people who have Zone 1 in their journey.
    
    Returns cumulative counts: 1+, 2+, 3+, 4+, 5+ zones visited.
    
    Args:
        df: DataFrame with columns: global_object_id, zone_id
        
    Returns:
        DataFrame with columns: Number of Zones, Count
    """
    # Group by global_object_id to get unique zones visited per person
    person_zones = df.groupby('global_object_id')['zone_id'].apply(lambda x: set(x))
    
    # Filter to only people who visited Zone 1
    people_with_zone1 = person_zones[person_zones.apply(lambda zones: 1 in zones)]
    
    # Count unique zones for each person
    zone_counts = people_with_zone1.apply(len)
    
    # Calculate cumulative counts (1+, 2+, 3+, etc.)
    frequency_data = []
    max_zones = max(zone_counts) if len(zone_counts) > 0 else 5
    
    # Generate cumulative counts up to at least 5+
    for threshold in range(1, max(6, max_zones + 1)):
        count = (zone_counts >= threshold).sum()
        frequency_data.append({
            'Number of Zones': f'{threshold}+',
            'Count': int(count)
        })
    
    return pd.DataFrame(frequency_data)


def calculate_missing_zone1_percentage(df: pd.DataFrame) -> Tuple[float, int, int]:
    """
    Calculate percentage of unique people who never visited Zone 1.
    
    Args:
        df: DataFrame with columns: global_object_id, zone_id
        
    Returns:
        Tuple of (percentage, people_without_zone1, total_people)
    """
    # Get all unique people
    all_people = set(df['global_object_id'].unique())
    
    # Get people who visited Zone 1
    zone1_people = set(df[df['zone_id'] == 1]['global_object_id'].unique())
    
    # People who never visited Zone 1
    people_without_zone1 = all_people - zone1_people
    
    # Calculate percentage
    total_people = len(all_people)
    missing_count = len(people_without_zone1)
    percentage = (missing_count / total_people * 100) if total_people > 0 else 0
    
    return percentage, missing_count, total_people


def get_summary_statistics(df: pd.DataFrame) -> dict:
    """
    Calculate summary statistics for the dataset.
    
    Args:
        df: DataFrame with GMR data
        
    Returns:
        Dictionary with summary statistics
    """
    stats = {
        'total_records': len(df),
        'unique_people': df['global_object_id'].nunique(),
        'unique_zones': df['zone_id'].nunique(),
        'date_range': None
    }
    
    # Try to parse date range if zone_entry_time exists and is valid
    if 'zone_entry_time' in df.columns:
        valid_times = df[df['zone_entry_time'] != '-1']['zone_entry_time']
        if len(valid_times) > 0:
            try:
                times = pd.to_datetime(valid_times)
                stats['date_range'] = (times.min(), times.max())
            except:
                pass
    
    return stats

