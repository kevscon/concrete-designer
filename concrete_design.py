import pandas as pd
from config import props_path

def calc_stress(M, y, I):
    """
    Calculates stress in beam due to bending moment (ksi).

    Parameters:
    - M: Applied moment (k-ft).
    - y: Distance from neutral access (in).
    - I: Moment of inertia (in⁴).
    """
    return M * 12 * y / I

def calc_fr(f_c):
    """
    Calculates concrete modulus of rupture (ksi).

    Parameters:
    - f_c: Compressive strength of concrete (ksi).
    """
    return 0.24 * f_c ** 0.5

def calc_Ig(width, height) -> float:
    """
    Calculates moment of inertia (in⁴).

    Parameters:
        - width: Beam width (in).
        - height: Beam height (in).
    """
    return width * height ** 3 / 12

def calc_Sc(width, height) -> float:
    """
    Calculates section modulus (in³).

    Parameters:
        - width: Beam width (in).
        - height: Beam height (in).
    """
    return (1/12 * width * height ** 3) / (height / 2)

def calc_Mcr(f_r, S_c) -> float:
    """
    Parameters:
        - f_r: Modulus of rupture (ksi).
        - S_c: Section modulus (in³).

    Returns:
    - Cracking moment, M_cr (k-ft).
    """
    return f_r * S_c / 12

def calc_beta1(f_c):
    """
    Calculates concrete stress block factor.

    Parameters:
    - f_c: Compressive strength of concrete (ksi).
    """
    if f_c <= 4:
        beta_1 = 0.85
    else:
        beta_1 = max(0.85 - (f_c - 4) * 0.05, 0.65)
    return beta_1

def calc_lambda(conc_density):
    """
    Parameters:
    - conc_density: Concrete density (pcf).

    Returns:
    - lambda: Concrete density modification factor.
    """
    return min(max(7.5 * conc_density / 1000, 0.75), 1)

def calc_Ec(f_c, conc_density):
    """
    Parameters:
    - f_c: Compressive strength of concrete (ksi).
    - conc_density: Concrete density (pcf).

    Returns:
    - E_c: Elastic modulus of concrete (ksi).
    """
    return 33000 * (conc_density / 1000) ** 1.5 * f_c ** 0.5

def calc_n(E_s, E_c):
    """
    Calculates the modular ratio of steel to concrete.

    Parameters:
    - E_s: Elastic modulus of steel (ksi).
    - E_c: Elastic modulus of concrete (ksi).

    Returns:
    - Modular ratio, n.
    """
    return E_s / E_c

def calc_demand_ratio(load, capacity, resistance_factor=1):
    """
    Calculates the ratio of load to capacity.
    """
    return load / (resistance_factor * capacity)


class RebarProperties:
    """
    Class to retrieve steel rebar properties.
    """
    def __init__(self, bar_size: str, data_path: str):
        self.bar_size = bar_size
        self.bar_props_df = pd.read_csv(data_path, dtype=str)
        prop_table = self.bar_props_df[self.bar_props_df['bar_size'] == bar_size]
        if prop_table.empty:
            raise ValueError(f"Bar size '{bar_size}' not found in the properties file.")
        self.bar_diameter = float(prop_table['bar_diameter'].values[0])
        self.bar_area = float(prop_table['bar_area'].values[0])
        self.bar_weight = float(prop_table['bar_weight'].values[0])
        self.bar_perimeter = float(prop_table['bar_perimeter'].values[0])

    def calc_position(self, cover: float, trans_bar: str=None):
        """
        Calculates distance from face of concrete to center of rebar (in).

        Parameters:
        - cover: Distance from face of concrete to edge of rebar (in).
        - trans_bar: Size of transverse bar.
        """
        if trans_bar:
            prop_table = self.bar_props_df[self.bar_props_df['bar_size'] == trans_bar]
            if prop_table.empty:
                raise ValueError(f"Bar size '{trans_bar}' not found in the properties file.")
            trans_diameter = float(prop_table['bar_diameter'].values[0])
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

    def calc_As(self, width: float, spacing: float, offset: float=0):
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
        return num_bars * self.bar_area

    def calc_num_bars(self, width: float, spacing: float, offset: float=0):
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

class ConcreteAnalyzer:
    def __init__(self, width: float, height: float, bar_size: str, spacing: float, cover: float, f_c: float, f_y: float, conc_density: float, E_s: float=29000):
        """
        Base class for concrete beam analysis.
        
        Parameters:
        - width: Beam width (in).
        - height: Beam height (in).
        - bar_size: Standard bar size label (#).
        - spacing: Center-to-center spacing of rebar (in).
        - cover: Distance from concrete face to edge of reinforcing bar (in).
        - f_c: Compressive strength of concrete (ksi).
        - f_y: Yield strength of steel (ksi).
        - conc_density: Concrete density (pcf).
        - E_s: Elastic modulus of steel (ksi).

        Initialized properties:
        - A_s: Area of reinforcing steel (in²).
        - As_per_ft: Area of reinforcing steel per foot (in²/ft).
        - d_c: Centroid of reinforcing from concrete face in tension (in).

        - A_g: Area of uncracked concrete section (in²).
        - w_DL: Dead load due to beam self-weight (k/ft).
        - E_c: Elastic modulus of concrete (ksi).
        - n: Modular ratio.
        - d_s: Effective depth of reinforcing (in).

        - f_r: Modulus of rupture (ksi).
        - I_g: Moment of inertia (in⁴).
        - S_c: Section modulus (in³).
        - M_cr: Cracking moment (k-ft).

        - a: Depth of the compressive stress block (in).
        - d_v: Effective shear depth (in).
        """

        self.b = width
        self.h = height
        self.spacing = spacing
        self.f_c = f_c
        self.f_y = f_y
        self.conc_density = conc_density

        rebar = RebarProperties(bar_size, props_path)
        self.A_s = rebar.calc_As(width, spacing)
        self.As_per_ft = rebar.calc_As_per_ft(spacing)
        self.d_c = rebar.calc_position(cover)

        self.A_g = width * height
        self.w_DL = conc_density / 1000 * self.A_g / 144
        self.E_c = calc_Ec(f_c, conc_density)
        self.n = calc_n(E_s, self.E_c)
        self.d_s = height - self.d_c

        self.f_r = calc_fr(f_c)
        self.I_g = calc_Ig(width, height)
        self.S_c = calc_Sc(width, height)
        self.M_cr = calc_Mcr(self.f_r, self.S_c)

        self.a = (self.A_s * self.f_y) / (0.85 * self.f_c * self.b)
        beta_1 = calc_beta1(self.f_c)
        self.c = self.a / beta_1
        self.d_v = max(self.d_s - self.c / 2, 0.9 * self.d_s, 0.72 * self.h)
        
        self.set_moment_capacity()
        self.set_epsilon_t()
        self.set_shear_capacity()

    def set_moment_capacity(self) -> float:
        """
        Returns:
        - Moment capacity, M_n (k-ft).
        """
        self.M_n = self.A_s * self.f_y * (self.d_s - self.a / 2) / 12

    def set_epsilon_t(self, epsilon_c=0.003):
        """
        Calculates design tensile strain in steel.

        Parameters:
        - epsilon_c: Design concrete compressive strain.
        """
        beta_1 = calc_beta1(self.f_c)
        c = self.a / beta_1
        self.epsilon_t = epsilon_c * (self.d_s - c) / c

    def set_Vc(self) -> float:
        """
        Assumes simplified procedure.

        Parameters:
        - d_v: Effective shear depth (in).
        - lambda: Concrete density modification factor.
        - beta: Tension and shear transmission factor.

        Returns:
        - Concrete shear capacity, V_c (kips).
        """
        lambda_ = calc_lambda(self.conc_density)
        beta = 2
        self.V_c = 0.0316 * beta * lambda_ * self.f_c ** 0.5 * self.b * self.d_v

    def set_shear_capacity(self, V_s=0):
        """
        Parameters: 
        - V_s: Reinforcing shear capacity (kips).

        Returns:
        - Shear capacity, V_n (kips).
        """
        self.set_Vc()
        max_V_n = 0.25 * self.f_c * self.b * self.d_v
        self.V_n = min(self.V_c + V_s, max_V_n)

    def set_stresses(self, M):
        """
        Parameters:
        - M: Service moment applied to beam (k-ft).

        Sets:
        - f_conc: Stress in concrete (ksi).
        - f_steel: Stress in steel (ksi).
        """
        self.cracked = M >= self.M_cr
        if self.cracked == True:
            rho = self.A_s / (self.b * self.d_s)
            k = -rho * self.n + ((rho * self.n) ** 2 + 2 * rho * self.n)**0.5
            j = 1 - k / 3
            self.f_conc = 2 * M * 12 / (j * k * self.b * self.d_s**2)
            self.f_steel = M * 12 / (self.A_s * j * self.d_s)
        else:
            self.f_conc = calc_stress(M, self.h / 2, self.I_g)
            self.f_steel = self.n * calc_stress(M, self.d_s - self.h / 2, self.I_g)

class ConcreteDesign:

    def __init__(self, beam_instance, M_u, M_s, V_u, phi_m, phi_v):
        """
        Subclass for concrete beam design.

        Parameters:
        - beam_instance: Instance of ConcreteAnalyzer class.
        - M_u: Factored moment load (k-ft).
        - M_s: Service moment load (k-ft).
        - V_u: Factored shear load (k-ft).
        - phi_m: Moment resistance factor.
        - phi_v: Shear resistance factor.
        """
        self.beam_instance = beam_instance
        self.M_u = M_u
        self.M_s = M_s
        self.V_u = V_u
        self.phi_m = phi_m
        self.phi_v = phi_v

        self.set_dist_reinf()
        self.set_capacities()
        self.set_epsilon_tl()

    def set_dist_reinf(self):
        """
        Calculates the required distribution reinforcement for a section.

        Parameters:
        - width: Beam width in cross-section (in).
        - height: Beam height in cross-section (in).
        - f_y: Yield strength of steel (ksi).

        Returns:
        - Reinforcing area per foot (in²/ft).
        """
        width = self.beam_instance.b
        height = self.beam_instance.h
        f_y = self.beam_instance.f_y
        A_reqd = 1.3 * width * height / (2 * (width + height) * f_y)
        self.A_ts = min(max(A_reqd, 0.11), 0.6)

    def set_capacities(self):
        """
        Calculates:
        - phi_Mn: Factored moment capacity (k-ft).
        - epsilon_tl: Design strain in steel.
        - phi_Vn: Factored Shear capacity
        """
        self.phi_Mn = self.phi_m * self.beam_instance.M_n
        self.set_epsilon_tl()
        self.phi_Vn = self.phi_v * self.beam_instance.V_n

    def set_epsilon_tl(self, epsilon_c=0.003):
        """
        Calculates the minimum steel strain required for a ductile section.

        Parameters:
        - f_y: Yield strength of steel (ksi).
        - epsilon_c: Design concrete compressive strain.
        """
        f_y = self.beam_instance.f_y
        if f_y <= 75:
            self.epsilon_tl = 0.005
        else:
            self.epsilon_tl = (f_y - 75) / (100 - 75) * epsilon_c + 0.005

    def set_gamma_3(self):
        """
        Determine value for the AASHTO yield strength to ultimate strength ratio factor.

        Parameters:
        - f_y: Yield strength of steel (ksi).
        """
        f_y = self.beam_instance.f_y
        if f_y == 75:
            self.gamma_3 = 0.75
        elif f_y == 80:
            self.gamma_3 = 0.76
        else:
            self.gamma_3 = 0.67

    def set_min_reinf(self, gamma_1=1.6, gamma_3=None):
        """
        Calculates design moment based on minimum reinforcement criteria.

        Parameters:
        - M_cr: Cracking moment (k-ft).
        - gamma_1: AASHTO flexure cracking variation factor - 1.2 precast, 1.6 RC.
        - gamma_3: AASHTO yield strength to ultimate strength ratio factor.

        Returns:
        - Design moment (k-ft).
        """
        M_cr = self.beam_instance.M_cr
        if not gamma_3:
            self.set_gamma_3()
            gamma_3 = self.gamma_3
        self.min_reinf_M = min(gamma_1 * gamma_3 * M_cr, 1.33 * self.M_u)

    def calc_excess_reinf(self):
        """
        Calculates excess reinforcement factor, gamma_er.

        Parameters:
        - M_design: Design moment load (k-ft).
        - phi_Mn: Factored moment capacity (k-ft).
        """
        M_design = max(self.M_u, self.min_reinf_M)
        gamma_er = M_design / self.phi_Mn
        return round(gamma_er, 2)

    def set_design_spacing(self, gamma_e=0.75):
        """
        Calculates maximum spacing for flexure reinforcement based on service stress.

        Parameters:
        - gamma_e: AASHTO exposure factor - 0.75 important, 1.0 other.
        - f_r: Modulus of rupture (ksi).
        - f_s: Tensile service stress in reinforcing (ksi).
        - f_y: Yield strength of steel (ksi).
        - h: Beam height (in).
        - d_c: Concrete face in tension to center of reinforcing (in).
        - f_ct: Tensile stress in uncracked concrete section (ksi).

        Returns:
        - Maximum spacing, s_max (in).
        """
        f_r = self.beam_instance.f_r
        f_s = self.beam_instance.f_steel
        f_y = self.beam_instance.f_y
        h = self.beam_instance.h
        d_c = self.beam_instance.d_c
        I_g = self.beam_instance.I_g
        f_ct = calc_stress(self.M_s, h / 2, I_g)

        beta_s = 1 + d_c / (0.7 * (h - d_c))
        f_ss = min(f_s, 0.6 * f_y)
        if f_ct > 0.8 * f_r:
            self.s_max = 700 * gamma_e / (beta_s * f_ss) - 2 * d_c
        else:
            self.s_max = None

    def set_checks(self):
        """
        Sets True/False value for each design check.
        """
        self.moment_capacity = self.phi_Mn >= self.M_u
        self.shear_capacity = self.phi_Vn >= self.V_u
        self.min_reinf = self.phi_Mn >= self.min_reinf_M
        self.crack_control = self.beam_instance.spacing <= self.s_max if self.s_max else True
        self.ductility = self.beam_instance.epsilon_t > self.epsilon_tl
        self.dist_reinf = self.beam_instance.As_per_ft >= self.A_ts