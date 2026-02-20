import ipywidgets as widgets
from ipywidgets import (
    Label, Layout, Box, VBox, HBox, GridBox, Button,
    IntSlider, FloatSlider, FloatLogSlider, ToggleButton,
    Accordion, Text, FloatText, IntText, BoundedFloatText,
    ToggleButtons, Checkbox, DatePicker, Output, HTML
)
from IPython.display import clear_output, display
from sonifier import Sonifier
from data import DataManager


# ============================================================================
# STYLING CONSTANTS
# ============================================================================
CARD_STYLE = dict(
    border='1px solid #ccc',
    padding='10px',
    margin='5px',
    flex_flow='column',
    align_items='stretch',
    justify_content='flex-start',
    width='100%',
    overflow='visible'
)

CARD_TITLE_STYLE = dict(font_weight='bold', font_size='14px')
LABEL_STYLE = dict(font_weight='bold', font_size='11px')
MUTED_LABEL_STYLE = dict(font_size='12px', color='#666')


class SonificationUI:
    """
    Interactive UI for designing and generating sonifications of MAG data.
    
    This class provides a flexible, responsive interface for users to:
    - Select which month to sonify
    - Choose which data variables to sonify
    - Map data to evolvable sound properties
    - Configure sonification duration
    - Generate and display sonifications with accompanying plots
    
    Attributes:
    -----------
    monthly_data : dict
        Dictionary where keys are month numbers (1-12) and values are DataFrames
    month_names : list
        List of 12 month names
    data_labels : list
        Available magnetic field components: |B|, BR, BT, BN
    evolvable_properties : list
        Sound properties that can be mapped to data: pitch_shift, cutoff, volume, etc.
    """

    def __init__(self, monthly_data, month_names):
        """
        Initialize the SonificationUI.
        
        Parameters:
        -----------
        monthly_data : dict
            Dictionary with month numbers (1-12) as keys, DataFrames as values
        month_names : list
            List of 12 month name strings
        """
        self.monthly_data = monthly_data
        self.month_names = month_names
        self.data_labels = ['|B|', 'BR', 'BT', 'BN']
        self.evolvable_properties = [
            "pitch_shift", "cutoff", "volume", "phi",
            "volume_lfo/amount", "volume_lfo/freq_shift",
            "pitch_lfo/amount", "pitch_lfo/freq_shift"
        ]

        self._create_widgets()
        self._setup_callbacks()

    def _create_widgets(self):
        """Create all UI components organized into cards."""
        # Output area for plots and sonification display
        self.output_area = widgets.Output(layout=Layout(
            flex='1 1 auto',
            overflow='auto',
            border='0',
            min_width='400px',
            min_height='300px'
        ))

        # Build individual cards
        self._create_date_card()
        self._create_data_card()
        self._create_settings_card()
        
        # Stack cards vertically with flexible sizing
        self.selector_panel = VBox([
            self.date_card,
            self.data_card,
            self.settings_card
        ], layout=Layout(
            flex='0 0 auto',
            overflow='visible',
            border='0'
        ))

    def _create_card(self, title, children, tag):
        """
        Helper method to create a styled card widget.
        
        Parameters:
        -----------
        title : str
            Card title text
        children : list
            List of child widgets to place in the card
        tag : str
            Identifier tag for finding the card later
            
        Returns:
        --------
        Box
            Styled card widget
        """
        title_widget = Label(value=title, style=CARD_TITLE_STYLE)
        
        card = Box(
            children=[title_widget] + children,
            layout=Layout(**CARD_STYLE)
        )
        card.tag = tag
        return card

    def _create_date_card(self):
        """Create month selection card with a slider."""
        # Month slider (1-12)
        self.month_slider = IntSlider(
            value=1,
            min=1,
            max=12,
            step=1,
            description='Month:',
            layout=Layout(width='100%')
        )
        self.month_slider.tag = 'month_slider'
        
        # Month display label
        self.month_display = Label(
            value=f'Selected: {self.month_names[0]}',
            style=MUTED_LABEL_STYLE
        )
        self.month_display.tag = 'month_display'
        
        # Combine into card
        self.date_card = self._create_card(
            'Select Month to Sonify',
            [self.month_slider, self.month_display],
            'date_card'
        )

    def _create_data_card(self):
        """Create data selection and property mapping card."""
        data_options = ['-'] + self.data_labels
        
        # Data 1 section: selector + property mapping
        self.data_selector_1 = widgets.Dropdown(
            options=data_options, value='|B|',
            layout=Layout(width='100%', overflow='visible')
        )
        self.data_selector_1.tag = 'data_selector_1'
        
        self.property_selector_1 = widgets.Dropdown(
            options=self.evolvable_properties, value='pitch_shift',
            layout=Layout(width='100%', overflow='visible')
        )
        self.property_selector_1.tag = 'property_selector_1'
        
        data1_section = VBox([
            Label(value='Data 1:', style=LABEL_STYLE),
            self.data_selector_1,
            Label(value='Map to:', style=LABEL_STYLE),
            self.property_selector_1
        ], layout=Layout(width='100%', overflow='visible'))
        
        # Data 2 section: selector + property mapping (conditionally shown)
        self.data_selector_2 = widgets.Dropdown(
            options=data_options, value='-',
            layout=Layout(width='100%', overflow='visible')
        )
        self.data_selector_2.tag = 'data_selector_2'
        
        self.prop2_label = Label(
            value='Map to:',
            style=LABEL_STYLE
        )
        
        self.property_selector_2 = widgets.Dropdown(
            options=self.evolvable_properties, value='volume',
            layout=Layout(width='100%', overflow='visible')
        )
        self.property_selector_2.tag = 'property_selector_2'
        
        data2_section = VBox([
            Label(value='Data 2:', style=LABEL_STYLE),
            self.data_selector_2,
            self.prop2_label,
            self.property_selector_2
        ], layout=Layout(width='100%', overflow='visible'))
        
        self.data_card = self._create_card(
            'Data & Mappings',
            [data1_section, data2_section],
            'data_card'
        )

    def _create_settings_card(self):
        """Create sonification settings card with duration and generate button."""
        self.length_selector = IntText(
            value=10,
            layout=Layout(width='100%')
        )
        self.length_selector.tag = 'length_selector'
        
        length_section = VBox([
            Label(value='Duration (s):', style=LABEL_STYLE),
            self.length_selector
        ], layout=Layout(width='100%', overflow='visible'))
        
        self.generate_button = Button(
            description='Generate', 
            button_style='info',
            tooltip='Generate sonification',
            icon='play',
            layout=Layout(width='100%')
        )
        self.generate_button.tag = 'generate_button'
        
        self.settings_card = self._create_card(
            'Settings',
            [length_section, self.generate_button],
            'settings_card'
        )

    def _setup_callbacks(self):
        """Connect widget observers to their callback methods."""
        self.month_slider.observe(self._update_month_display, names='value')
        self.data_selector_2.observe(self._update_data_visibility, names='value')
        self.generate_button.on_click(self._on_generate_click)

    def _update_month_display(self, change):
        """Update the month display label when slider changes."""
        month_num = change['new']
        self.month_display.value = f'Selected: {self.month_names[month_num - 1]}'

    def _update_data_visibility(self, change):
        """Show/hide Data 2 property selector based on data selection."""
        is_data2_selected = change['new'] != '-'
        self.prop2_label.layout.display = 'block' if is_data2_selected else 'none'
        self.property_selector_2.layout.display = 'block' if is_data2_selected else 'none'

    def _on_generate_click(self, button):
        """Handle Generate button click event."""
        with self.output_area:
            clear_output(wait=True)
            
            # Get selected month
            month_num = self.month_slider.value
            
            # Check if month has data
            if month_num not in self.monthly_data:
                print(f"Error: No data for month {month_num}")
                return
            
            data_1 = self.data_selector_1.value
            data_2 = self.data_selector_2.value
            prop_1 = self.property_selector_1.value
            prop_2 = self.property_selector_2.value
            length = int(self.length_selector.value)
            
            # Get data for the selected month
            month_df = self.monthly_data[month_num]
            
            # Create temporary DataManager for this month
            temp_dm = DataManager(month_df)
            temp_sonifier = Sonifier(temp_dm)
            
            # Get date range from month data
            min_date, max_date = temp_dm.get_date_range()
            
            # Generate sonification
            soni, mode = temp_sonifier.generate(
                min_date, max_date, data_1, prop_1, data_2, prop_2, length
            )
            
            # Render and display
            soni.render()
            soni.notebook_display(show_waveform=0)



    def display(self):
        """Display plot on left, selector panel on right with flexible sizing."""
        # Ensure property_selector_2 visibility reflects current data_2 selection
        self._update_data_visibility({'new': self.data_selector_2.value})

        # Flexible layout containers
        output_box = Box([self.output_area], layout=Layout(
            flex='1 1 auto',
            overflow='auto',
            min_width='400px'
        ))
        controls_box = Box([self.selector_panel], layout=Layout(
            flex='0 0 auto',
            overflow='visible',
            min_width='250px'
        ))

        # Side-by-side with flexible sizing
        display(HBox([output_box, controls_box], layout=Layout(
            display='flex',
            flex_flow='row',
            align_items='flex-start',
            width='100%',
            height='auto'
        )))


def find_widget_by_tag(container, tag):
    """
    Recursively search through a container for a widget with a specific custom tag.
    
    Parameters:
    -----------
    container : widget
        A widget container (e.g., VBox, HBox, Box).
    tag : str
        The custom tag to search for.
    
    Returns:
    --------
    widget or None
        The widget if found, otherwise None.
    """
    # Check if the container itself has the tag
    if hasattr(container, 'tag') and container.tag == tag:
        return container

    # If the container has children, search recursively
    if hasattr(container, 'children'):
        for child in container.children:
            found_widget = find_widget_by_tag(child, tag)
            if found_widget:
                return found_widget
    
    return None

