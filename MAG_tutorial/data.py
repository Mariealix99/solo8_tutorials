import pandas as pd
import numpy as np
from datetime import datetime
from sunpy.net import Fido, attrs as a
import cdflib
from sunpy.timeseries import TimeSeries as ts
import sunpy_soar

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
        start_date : str, datetime.date, or pandas.Timestamp
            Start date (inclusive)
        end_date : str, datetime.date, or pandas.Timestamp
            End date (inclusive)
            
        Returns:
        --------
        pandas.DataFrame
            Subset of data within the date range
        """
        # Convert to timestamps if strings or date objects
        if isinstance(start_date, str):
            start_date = pd.Timestamp(start_date)
        elif hasattr(start_date, 'year') and not isinstance(start_date, pd.Timestamp):
            # Handle Python date objects
            start_date = pd.Timestamp(start_date.year, start_date.month, start_date.day)
        
        if isinstance(end_date, str):
            end_date = pd.Timestamp(end_date)
        elif hasattr(end_date, 'year') and not isinstance(end_date, pd.Timestamp):
            # Handle Python date objects
            end_date = pd.Timestamp(end_date.year, end_date.month, end_date.day)
        
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
    
    # Create search attributes
    result = Fido.search(
        a.Time(start_str, end_str),
        a.Instrument.mag,
        a.soar.Product('mag-rtn-normal-1-minute'),
        a.Level(2)
    )
    
    # Download files
    files = Fido.fetch(result)
    if isinstance(files, str):
        files = [files]
    
    # Process and combine data
    data = None
    for file in files:
        temp_df = analysis_helpers.cdf2df(file)
        if data is None:
            data = temp_df.copy()
        else:
            data = pd.concat([data, temp_df])
    
    if data is None:
        raise ValueError(f"No data files were successfully processed")
    
    # Ensure DatetimeIndex is proper
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError(f"Processed data does not have DatetimeIndex")
    
    data.sort_index(inplace=True)
    
    return data
