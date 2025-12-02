"""
Analysis functions for GMR (Global Matching Records) data.
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
        DataFrame with columns: Zone ID, Unique Conversion Count
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
            'Unique Conversion Count': conversion_count
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
        'unique_objects': df['global_object_id'].nunique(),
        'unique_zones': df['zone_id'].nunique(),
        'unique_property_enter': 0,
        'date_range': None
    }
    
    # Calculate unique property enter (unique global IDs that have '1' in them)
    unique_ids_with_1 = df[df['zone_id'] == 1]['global_object_id'].nunique()
    stats['unique_property_enter'] = unique_ids_with_1
    
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


def calculate_records_distribution(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Calculate distribution of records per global_object_id.
    
    Args:
        df: DataFrame with GMR data
        
    Returns:
        Tuple of (distribution_df, stats_dict)
        - distribution_df: DataFrame with record count categories and their frequencies
        - stats_dict: Dictionary with mean, median, min, max, std
    """
    # Group by global_object_id and count records
    group_sizes = df.groupby('global_object_id').size()
    
    # Calculate statistics
    stats = {
        'mean': group_sizes.mean(),
        'median': group_sizes.median(),
        'min': group_sizes.min(),
        'max': group_sizes.max(),
        'std': group_sizes.std()
    }
    
    # Create distribution categories
    total = len(group_sizes)
    distribution_data = []
    
    categories = [
        ('1', lambda x: x == 1),
        ('2-5', lambda x: (x >= 2) & (x <= 5)),
        ('6-10', lambda x: (x >= 6) & (x <= 10)),
        ('11-20', lambda x: (x >= 11) & (x <= 20)),
        ('21-50', lambda x: (x >= 21) & (x <= 50)),
        ('>50', lambda x: x > 50)
    ]
    
    for category_name, condition in categories:
        count = condition(group_sizes).sum()
        percentage = (count / total * 100) if total > 0 else 0
        distribution_data.append({
            'Records per Object': category_name,
            'Number of Objects': int(count),
            'Percentage': percentage
        })
    
    return pd.DataFrame(distribution_data), stats


def calculate_enter_exit_analysis(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Analyze records with enter/exit status by distribution categories.
    
    Args:
        df: DataFrame with columns: global_object_id, zone_exit_time
        
    Returns:
        Tuple of (analysis_df, summary_dict)
        - analysis_df: DataFrame with enter/exit breakdown by record count categories
        - summary_dict: Overall summary statistics
    """
    # Identify records with exit time
    df['has_exit'] = ~((df['zone_exit_time'] == -1) | (df['zone_exit_time'] == '-1'))
    
    # Group by global_object_id
    group_sizes = df.groupby('global_object_id').size()
    
    # Overall statistics
    total_records = len(df)
    records_with_exit = df['has_exit'].sum()
    records_without_exit = total_records - records_with_exit
    
    summary = {
        'total_records': total_records,
        'with_exit': int(records_with_exit),
        'without_exit': int(records_without_exit),
        'exit_percentage': (records_with_exit / total_records * 100) if total_records > 0 else 0
    }
    
    # Analyze by category
    categories = [
        ('1', lambda x: x == 1),
        ('2-5', lambda x: (x >= 2) & (x <= 5)),
        ('6-10', lambda x: (x >= 6) & (x <= 10)),
        ('11-20', lambda x: (x >= 11) & (x <= 20)),
        ('21-50', lambda x: (x >= 21) & (x <= 50)),
        ('>50', lambda x: x > 50)
    ]
    
    analysis_data = []
    for category_name, condition in categories:
        object_ids = group_sizes[condition(group_sizes)].index
        if len(object_ids) == 0:
            continue
            
        category_records = df[df['global_object_id'].isin(object_ids)]
        total_cat_records = len(category_records)
        with_exit = category_records['has_exit'].sum()
        without_exit = total_cat_records - with_exit
        
        analysis_data.append({
            'Records per Object': category_name,
            'Total Records': int(total_cat_records),
            'With Exit': int(with_exit),
            'Without Exit': int(without_exit),
            'Exit %': (with_exit / total_cat_records * 100) if total_cat_records > 0 else 0
        })
    
    return pd.DataFrame(analysis_data), summary


def get_group_size_histogram_data(df: pd.DataFrame, max_value: int = 50) -> pd.DataFrame:
    """
    Get histogram data for group sizes (records per object).
    
    Args:
        df: DataFrame with GMR data
        max_value: Maximum value to include (values above are grouped as '>max_value')
        
    Returns:
        DataFrame with columns: Records, Frequency
    """
    group_sizes = df.groupby('global_object_id').size()
    
    # Create histogram data
    hist_data = []
    for i in range(1, max_value + 1):
        count = (group_sizes == i).sum()
        if count > 0:
            hist_data.append({
                'Records': i,
                'Frequency': int(count)
            })
    
    # Add >max_value category if exists
    above_max = (group_sizes > max_value).sum()
    if above_max > 0:
        hist_data.append({
            'Records': f'>{max_value}',
            'Frequency': int(above_max)
        })
    
    return pd.DataFrame(hist_data)

