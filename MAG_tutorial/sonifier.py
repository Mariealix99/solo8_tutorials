"""
Sonification generation module for MAG data.

Handles the creation of sonifications from magnetic field data,
including plotting and STRAUSS synthesis.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from strauss.sonification import Sonification
from strauss.sources import Objects
from strauss.score import Score
from strauss.generator import Synthesizer


# Plotting constants
PLOT_FIGSIZE = (8, 4)
PLOT_DPI = 100


class Sonifier:
    """
    Generates sonifications of magnetic field data.
    
    This class encapsulates the logic for creating visualizations and
    audio sonifications from MAG data based on user-selected parameters.
    """

    def __init__(self, data_manager):
        """
        Initialize the Sonifier.
        
        Parameters:
        -----------
        data_manager : DataManager
            DataManager instance providing access to full time series data
        """
        self.data_manager = data_manager

    def generate(self, start_date, end_date, data_1, prop_1, data_2='-', prop_2=None, length=10):
        """
        Create and return a sonification based on user selections.
        
        Parameters:
        -----------
        start_date : str or pandas.Timestamp
            Start date (inclusive) for data range
        end_date : str or pandas.Timestamp
            End date (inclusive) for data range
        data_1 : str
            Primary data variable (|B|, BR, BT, BN)
        prop_1 : str
            Sound property to map to data_1
        data_2 : str, optional
            Secondary data variable (default: '-' for single data mode)
        prop_2 : str, optional
            Sound property to map to data_2
        length : int
            Sonification duration in seconds (default: 10)
            
        Returns:
        --------
        tuple
            (Sonification object, mode string)
        """
        # Extract data for the date range
        data_range = self.data_manager.extract_by_dates(start_date, end_date)
        
        date_str = f"{start_date} to {end_date}" if start_date != end_date else f"{start_date}"
        print(f"Generating sonification for {date_str}...")
        print(f"  Data 1: {data_1} → {prop_1}")

        # Extract and clean Data 1
        d1 = data_range[data_1].values.copy()
        d1 = d1[~np.isnan(d1)]
        time = np.arange(len(d1))

        # Single or dual data sonification
        if data_2 == '-':
            self._plot_single_data(data_range, data_1, prop_1)
            soni = self._create_single_sonification(d1, time, prop_1, length)
            mode = "single"
        else:
            print(f"  Data 2: {data_2} → {prop_2}")
            d2 = data_range[data_2].values.copy()
            d2 = d2[~np.isnan(d2)]
            self._plot_dual_data(data_range, data_1, data_2, prop_1, prop_2)
            soni = self._create_dual_sonification(d1, d2, time, prop_1, prop_2, length)
            mode = "dual"

        return soni, mode

    def _plot_single_data(self, data_range, data_1, prop_1):
        """
        Plot a single magnetic field component.
        
        Parameters:
        -----------
        data_range : pandas.DataFrame
            DataFrame with DatetimeIndex containing data for selected date range
        data_1 : str
            Data variable name (e.g., '|B|', 'BR')
        prop_1 : str
            Sound property being mapped to this data
        """
        plt.figure(figsize=PLOT_FIGSIZE, dpi=PLOT_DPI)
        plt.plot(data_range[data_1], color='black', label=data_1, linewidth=0.5)
        plt.ylabel('(nT)', fontsize=10)
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend(fontsize=9)
        plt.tight_layout()
        plt.show()

    def _plot_dual_data(self, data_range, data_1, data_2, prop_1, prop_2):
        """
        Plot two magnetic field components overlaid.
        
        Parameters:
        -----------
        data_range : pandas.DataFrame
            DataFrame with DatetimeIndex containing data for selected date range
        data_1, data_2 : str
            Data variable names
        prop_1, prop_2 : str
            Sound properties being mapped to each data variable
        """
        plt.figure(figsize=PLOT_FIGSIZE, dpi=PLOT_DPI)
        plt.plot(data_range[data_1], color='black', label=data_1, linewidth=0.5)
        plt.plot(data_range[data_2], color='red', label=data_2, linewidth=0.5)
        plt.ylabel('(nT)', fontsize=10)
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend(fontsize=9)
        plt.tight_layout()
        plt.show()

    def _create_single_sonification(self, data1_vals, time, prop_1, length):
        """
        Create a mono sonification mapping one data variable to a sound property.
        
        Parameters:
        -----------
        data1_vals : np.ndarray
            Data values (will be normalized to 0-1)
        time : np.ndarray
            Time indices for the data
        prop_1 : str
            Target sound property (e.g., 'pitch_shift', 'cutoff')
        length : int
            Sonification duration in seconds
            
        Returns:
        --------
        Sonification
            STRAUSS Sonification object ready to render
        """
        system = "mono"
        generator = Synthesizer()
        generator.load_preset('pitch_mapper')
        generator.modify_preset({
            'filter': 'on',
            "pitch_hi": -1, 
            "pitch_lo": 1,
            "pitch_lfo": {"use": "on", "amount": 1 * ("pitch_lfo" in prop_1), "freq": 3, "phase": 0.25},
            "volume_lfo": {"use": "on", "amount": 1 * ("volume_lfo" in prop_1), "freq": 3, "phase": 0}
        })
        
        notes = [["E3"]]
        score = Score(notes, length)

        # Normalize data to 0-1 range
        d1_norm = (data1_vals - data1_vals.min()) / (data1_vals.max() - data1_vals.min())

        data_dict = {'pitch': 0, 'time_evo': time, 'theta': 0.5, prop_1: d1_norm}
        sources = Objects(data_dict.keys())
        sources.fromdict(data_dict)
        
        lims = {
            'time_evo': ('0%', '100%'), 'pitch_shift': ('0%', '100%'), 'cutoff': ('0%', '100%'),
            "volume": ('0%', '100%'), "phi": (-0.5, 1.5),
            "volume_lfo/amount": ('0%', '100%'), "volume_lfo/freq_shift": ('0%', '100%'),
            "pitch_lfo/amount": ('0%', '100%'), "pitch_lfo/freq_shift": ('0%', '100%')
        }
        plims = {'cutoff': (0.4, 1)}
        sources.apply_mapping_functions(map_lims=lims, param_lims=plims)

        return Sonification(score, sources, generator, system)

    def _create_dual_sonification(self, data1_vals, data2_vals, time, prop_1, prop_2, length):
        """
        Create a stereo sonification mapping two data variables to separate sound properties.
        
        Parameters:
        -----------
        data1_vals, data2_vals : np.ndarray
            Data arrays (automatically normalized to 0-1)
        time : np.ndarray
            Time indices
        prop_1, prop_2 : str
            Target sound properties for each data variable
        length : int
            Sonification duration in seconds
            
        Returns:
        --------
        Sonification
            STRAUSS Sonification object ready to render
        """
        system = "stereo"
        generator = Synthesizer()
        generator.load_preset('pitch_mapper')
        generator.modify_preset({
            'filter': 'on',
            "pitch_hi": -1, 
            "pitch_lo": 1,
            "pitch_lfo": {
                "use": "on", 
                "amount": 1 * ("pitch_lfo" in prop_1 or "pitch_lfo" in prop_2), 
                "freq": 3, 
                "phase": 0.25
            },
            "volume_lfo": {
                "use": "on", 
                "amount": 1 * ("volume_lfo" in prop_1 or "volume_lfo" in prop_2), 
                "freq": 3, 
                "phase": 0
            }
        })
        
        notes = [["A2", "E3"]]
        score = Score(notes, length)

        # Normalize data to 0-1 range
        d1_norm = (data1_vals - data1_vals.min()) / (data1_vals.max() - data1_vals.min())
        d2_norm = (data2_vals - data2_vals.min()) / (data2_vals.max() - data2_vals.min())

        data_dict = {
            'pitch': [0, 1], 
            'time_evo': [time] * 2, 
            'theta': [0.5] * 2, 
            prop_1: [d1_norm] * 2, 
            prop_2: [d2_norm] * 2
        }
        sources = Objects(data_dict.keys())
        sources.fromdict(data_dict)
        
        lims = {
            'time_evo': ('0%', '100%'), 'pitch_shift': ('0%', '100%'), 'cutoff': ('0%', '100%'),
            "volume": ('0%', '100%'), "phi": (-0.5, 1.5),
            "volume_lfo/amount": ('0%', '100%'), "volume_lfo/freq_shift": ('0%', '100%'),
            "pitch_lfo/amount": ('0%', '100%'), "pitch_lfo/freq_shift": ('0%', '100%')
        }
        plims = {'cutoff': (0.4, 1)}
        sources.apply_mapping_functions(map_lims=lims, param_lims=plims)

        return Sonification(score, sources, generator, system)
