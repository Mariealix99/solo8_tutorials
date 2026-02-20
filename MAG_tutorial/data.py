"""
Data handling module for MAG sonification.

Provides utilities for loading and filtering magnetic field data by date range.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Data availability constants
MIN_DATA_YEAR = 2020
MIN_DATA_MONTH = 4
MIN_DATA_DATE = pd.Timestamp(f"{MIN_DATA_YEAR:04d}-{MIN_DATA_MONTH:02d}-01")


class DataManager:
    """
    Manages magnetic field data with date range filtering capabilities.
    
    Provides access to full time series data and allows extraction of
    subsets by date range for sonification.
    """
    
    def __init__(self, data_df):
        """
        Initialize the DataManager with a full dataset.
        
        Parameters:
        -----------
        data_df : pandas.DataFrame
            DataFrame with DatetimeIndex and columns: |B|, BR, BT, BN
        """
        self.data = data_df.copy()
        self._validate_data()
    
    def _validate_data(self):
        """Validate that data has required structure."""
        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        required_cols = {'|B|', 'BR', 'BT', 'BN'}
        missing_cols = required_cols - set(self.data.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def get_date_range(self):
        """
        Get the available date range in the dataset.
        
        Returns:
        --------
        tuple
            (min_date, max_date) as pandas Timestamps
        """
        return self.data.index.min(), self.data.index.max()
    
    def extract_by_dates(self, start_date, end_date):
        """
        Extract data for a given date range.
        
        Parameters:
        -----------
        start_date : str or pandas.Timestamp
            Start date (inclusive)
        end_date : str or pandas.Timestamp
            End date (inclusive)
            
        Returns:
        --------
        pandas.DataFrame
            Subset of data within the date range
        """
        # Convert to timestamps if strings
        if isinstance(start_date, str):
            start_date = pd.Timestamp(start_date)
        if isinstance(end_date, str):
            end_date = pd.Timestamp(end_date)
        
        # Ensure valid range
        if start_date > end_date:
            raise ValueError("start_date must be before end_date")
        
        # Extract data
        mask = (self.data.index >= start_date) & (self.data.index <= end_date)
        extracted = self.data[mask].copy()
        
        if len(extracted) == 0:
            raise ValueError(f"No data found between {start_date} and {end_date}")
        
        return extracted
    
    def get_available_months(self):
        """
        Get list of unique months available in the dataset.
        
        Returns:
        --------
        list
            List of (year, month) tuples with available data
        """
        months = []
        for date in self.data.index:
            ym = (date.year, date.month)
            if ym not in months:
                months.append(ym)
        return sorted(months)
    
    def get_month_name_and_range(self, year, month, month_names):
        """
        Get a friendly name and date range for a given month.
        
        Parameters:
        -----------
        year : int
            Year
        month : int
            Month (1-12)
        month_names : list
            List of 12 month names
            
        Returns:
        --------
        tuple
            (display_name, start_date, end_date)
        """
        month_name = month_names[month - 1]
        
        # Find first and last day of month in the dataset
        mask = (self.data.index.year == year) & (self.data.index.month == month)
        month_data = self.data[mask]
        
        if len(month_data) == 0:
            raise ValueError(f"No data for {year}-{month:02d}")
        
        start_date = month_data.index.min()
        end_date = month_data.index.max()
        
        return f"{month_name} {year}", start_date, end_date


def fetch_soar_data(start_year, start_month, start_day, end_year, end_month, end_day, analysis_helpers):
    """
    Fetch MAG data from SOAR using Fido search and download.
    
    Parameters:
    -----------
    start_year : int
        Start year (e.g., 2025)
    start_month : int
        Start month (1-12)
    start_day : int
        Start day (1-31)
    end_year : int
        End year (e.g., 2025)
    end_month : int
        End month (1-12)
    end_day : int
        End day (1-31)
    analysis_helpers : module
        analysis_helpers module with cdf2df function
        
    Returns:
    --------
    pandas.DataFrame
        Combined DataFrame with DatetimeIndex and columns: |B|, BR, BT, BN
        
    Raises:
    -------
    ValueError
        If dates are before April 2020 (when data became available)
    """
    from sunpy.net import Fido, attrs as a
    
    # Format dates as strings (YYYY-MM-DD)
    start_str = f"{start_year:04d}-{start_month:02d}-{start_day:02d}"
    end_str = f"{end_year:04d}-{end_month:02d}-{end_day:02d}"
    
    # Validate dates are not before minimum data availability
    start_date_obj = pd.Timestamp(start_str)
    if start_date_obj < MIN_DATA_DATE:
        raise ValueError(
            f"Data is only available from {MIN_DATA_DATE.strftime('%Y-%m-%d')} onwards. "
            f"Requested start date {start_str} is too early."
        )
    
    print(f"Fetching SOAR data from {start_str} to {end_str}...")
    
    # Create search attributes
    instrument = a.Instrument('MAG')
    time = a.Time(start_str, end_str)
    level = a.Level(2)
    product = a.soar.Product('MAG-RTN-NORMAL-1-MINUTE')
    
    # Do search
    print("Searching for available data...")
    result = Fido.search(time & level & product)
    print(f"Found {len(result)} files. Downloading...")
    
    # Download files
    files = Fido.fetch(result)
    if isinstance(files, str):
        files = [files]
    
    print(f"Downloaded {len(files)} files. Processing...")
    
    # Process and combine data
    data = pd.DataFrame()
    for i, file in enumerate(files):
        print(f"  Processing file {i+1}/{len(files)}...", end='\r')
        temp_df = analysis_helpers.cdf2df(file)
        data = pd.concat([data, temp_df])
    
    data.sort_index(inplace=True)
    print(f"\nCombined {len(data)} data points successfully!")
    
    return data
