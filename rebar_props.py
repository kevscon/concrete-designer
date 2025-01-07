import pandas as pd

class RebarProperties:
    """
    Class to retrieve steel rebar properties.
    """
    def __init__(self, bar_size: str, data_path: str):
        self.bar_size = bar_size
        bar_props_df = pd.read_csv(data_path, dtype=str)
        self.prop_table = bar_props_df[bar_props_df['bar_size'] == bar_size]
        if self.prop_table.empty:
            raise ValueError(f"Bar size {bar_size} not found in the properties file.")
        self.bar_diameter = float(self.prop_table['bar_diameter'].values[0])
        self.bar_area = float(self.prop_table['bar_area'].values[0])
        self.bar_weight = float(self.prop_table['bar_weight'].values[0])
        self.bar_perimeter = float(self.prop_table['bar_perimeter'].values[0])

    def return_props_dict(self):
        """
        Returns all properties as a dictionary.
        """
        return {
            'Bar Diameter (in)': self.bar_diameter,
            'Bar Area (in²)': self.bar_area,
            'Bar Weight (plf)': self.bar_weight,
            'Bar Perimeter (in)': self.bar_perimeter
        }

    
def calc_position(cover: float, bar_diameter: float, trans_diameter:float=0) -> float:
    """
    Calculates distance from face of concrete to center of rebar (in).

    Parameters:
    - cover: Distance from face of concrete to edge of rebar (in).
    - bar_diameter: Diameter of longitudinal rebar (in).
    - trans_diameter: Diameter of transverse reinforcing (in).
    """
    position = cover + trans_diameter + bar_diameter / 2
    return position

def calc_spacing(width: float, num_bars: float, offset: float=0):
    """
    Calculates the spacing of reinforcing (in).

    Parameters:
    - width: Width of concrete section (in).
    - num_bars: Number of reinforcing bars.
    - offset: Dimension from edge of concrete to center of first rebar (in).
    """
    if offset == 0:
        spacing = width / num_bars
    else:
        spacing = (width - 2 * offset) / (num_bars - 1)
    return spacing

def calc_num_bars(width: float, spacing: float, offset: float=0):
    """
    Calculates the number of reinforcing bars.

    Parameters:
    - width: Width of concrete section (in).
    - spacing: Spacing of reinforcing bars (in).
    - offset: Dimension from edge of concrete to center of first rebar (in).
    """
    if offset == 0:
        num_bars = width / spacing
    else:
        num_bars = (width - 2 * offset) / spacing + 1
    return num_bars

def calc_As_per_ft(bar_area: float, spacing: float) -> float:
    """
    Calculates the area of steel per foot (in²/ft).

    Parameters:
    - bar_area: Area of steel rebar (in²).
    - spacing: Center-to-center spacing of rebar (in).
    """
    As_per_ft = bar_area / (spacing / 12)
    return As_per_ft