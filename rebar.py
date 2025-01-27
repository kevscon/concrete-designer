import pandas as pd

class RebarProperties:
    """
    Class to retrieve steel rebar properties.
    """
    def __init__(self, bar_size: str, data_path: str):
        bar_props_df = pd.read_csv(data_path, dtype=str)
        prop_table = bar_props_df[bar_props_df['bar_size'] == bar_size]

        if prop_table.empty:
            raise ValueError(f"Bar size '{bar_size}' not found in the properties file.")

        self.properties = prop_table.iloc[0].to_dict()

    @property
    def bar_diameter(self):
        return float(self.properties['bar_diameter'])

    @property
    def bar_area(self):
        return float(self.properties['bar_area'])

    @property
    def bar_weight(self):
        return float(self.properties['bar_weight'])

    @property
    def bar_perimeter(self):
        return float(self.properties['bar_perimeter'])

class RebarGrade:
    """
    Class to retrieve steel rebar grade data.
    """
    def __init__(self, bar_grade: str, data_path: str):
        self.bar_grade = bar_grade
        self.bar_grade_df = pd.read_csv(data_path, dtype=str)
        prop_table = self.bar_grade_df[self.bar_grade_df['grade'] == bar_grade]

        if prop_table.empty:
            raise ValueError(f"Grade '{bar_grade}' not found in the properties file.")

        self.properties = prop_table.iloc[0].to_dict()

    @property
    def yield_strength(self):
        return float(self.properties['yield'])

    @property
    def gamma_3(self):
        return float(self.properties['gamma_3'])

class RebarLayout:
    """
    Class to calculate reinforcing layout in concrete.
    """
    def __init__(self, bar_size: str, data_path: str):
        self.bar_props_df = pd.read_csv(data_path, dtype=str)
        self.bar_diameter = self.get_bar_diameter(bar_size)
        self.bar_area = self.get_bar_area(bar_size)

    def get_bar_diameter(self, bar_size):
        prop_table = self.bar_props_df[self.bar_props_df['bar_size'] == bar_size]

        if prop_table.empty:
            raise ValueError(f"Bar size '{bar_size}' not found in the properties file.")

        properties = prop_table.iloc[0].to_dict()
        return float(properties['bar_diameter'])

    def get_bar_area(self, bar_size):
        prop_table = self.bar_props_df[self.bar_props_df['bar_size'] == bar_size]

        if prop_table.empty:
            raise ValueError(f"Bar size '{bar_size}' not found in the properties file.")

        properties = prop_table.iloc[0].to_dict()
        return float(properties['bar_area'])
        
    def calc_position(self, cover: float, trans_bar: str=None):
        """
        Calculates distance from face of concrete to center of rebar (in).

        Parameters:
        - cover: Distance from face of concrete to edge of rebar (in).
        - trans_bar: Size of transverse rebar.
        """
        if trans_bar:
            trans_diameter = self.get_bar_diameter(trans_bar)
        else:
            trans_diameter = 0
        position = cover + trans_diameter + self.bar_diameter / 2
        return position

    def calc_As_per_ft(self, spacing: float):
        """
        Calculates the area of steel per foot (in²/ft).

        Parameters:
        - spacing: Center-to-center spacing of rebar (in).
        """
        As_per_ft = self.bar_area / (spacing / 12)
        return As_per_ft

    def calc_cb(self, cover: float, spacing: float):
        """
        Calculates c_b value (in).

        Parameters:
        - cover: Distance from face of concrete to edge of rebar (in).
        - spacing: Center-to-center spacing of rebar (in).
        """
        return min(self.bar_diameter / 2 + cover, spacing / 2)

    def calc_As(self, width: float, spacing: float, offset: float=0):
        """
        Calculates the number of reinforcing bars.

        Parameters:
        - width: Width of concrete section (in).
        - spacing: Center-to-center spacing of rebar (in).
        - offset: Dimension from edge of concrete to center of first rebar (in).
        """
        if offset == 0:
            num_bars = width / spacing
        else:
            num_bars = (width - 2 * offset) / spacing + 1
        return num_bars * self.bar_area

    def calc_num_bars(self, width: float, spacing: float, offset: float=0):
        """
        Calculates the number of reinforcing bars.

        Parameters:
        - width: Width of concrete section (in).
        - spacing: Center-to-center spacing of rebar (in).
        - offset: Dimension from edge of concrete to center of first rebar (in).
        """
        if offset == 0:
            num_bars = width / spacing
        else:
            num_bars = (width - 2 * offset) / spacing + 1
        return num_bars

    def calc_spacing(self, width: float, num_bars: float, offset: float=0):
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