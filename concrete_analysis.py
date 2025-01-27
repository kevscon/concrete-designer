from config import props_path, grade_path
from rebar import RebarGrade, RebarLayout

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

def calc_compression_block(width, A_s, f_c, f_y):
    """
    Calculates concrete compression block (in).

    Parameters:
    - width: Beam width (in).
    - A_s: Area of reinforcing steel (in²).
    - f_c: Compressive strength of concrete (ksi).
    - f_y: Yield strength of steel (ksi).
    """
    return (A_s * f_y) / (0.85 * f_c * width)

def calc_dv(height, d_s, c):
    """
    Calculates effective shear depth (in).

    - height: Beam height (in).
    - d_s: Effective depth of reinforcing (in).
    - c: Depth of neutral axis (in).
    """
    return max(d_s - c / 2, 0.9 * d_s, 0.72 * height)


class ConcreteAnalyzer:
    def __init__(self, width: float, height: float, bar_size: str, spacing: float, cover: float, f_c: float, steel_grade: str, conc_density: float, E_s: float=29000):
        """
        Base class for concrete beam analysis.
        
        Parameters:
        - width: Beam width (in).
        - height: Beam height (in).
        - bar_size: Standard bar size label (#).
        - spacing: Center-to-center spacing of rebar (in).
        - cover: Distance from concrete face to edge of reinforcing bar (in).
        - f_c: Compressive strength of concrete (ksi).
        - steel_grade: Spec and grade of reinforcing steel.
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
        - c: Depth of neutral axis (in).
        - d_v: Effective shear depth (in).
        - lambda: Concrete density modification factor.
        """

        self.b = width
        self.h = height
        self.spacing = spacing
        self.f_c = f_c
        rebar_grade = RebarGrade(steel_grade, grade_path)
        self.f_y = rebar_grade.yield_strength
        self.gamma_3 = rebar_grade.gamma_3
        self.conc_density = conc_density
        self.lambda_ = calc_lambda(conc_density)

        rebar = RebarLayout(bar_size, props_path)
        self.bar_diameter = rebar.bar_diameter
        self.As_per_ft = rebar.calc_As_per_ft(spacing)
        self.A_s = rebar.calc_As(width, spacing)
        self.d_c = rebar.calc_position(cover)
        self.c_b = rebar.calc_cb(cover, spacing)
        self.d_s = height - self.d_c

        self.A_g = width * height
        self.w_DL = conc_density / 1000 * self.A_g / 144
        self.E_c = calc_Ec(f_c, conc_density)
        self.n = calc_n(E_s, self.E_c)

        self.f_r = calc_fr(f_c)
        self.I_g = calc_Ig(width, height)
        self.S_c = calc_Sc(width, height)
        self.M_cr = calc_Mcr(self.f_r, self.S_c)

        self.a = calc_compression_block(width, self.A_s, f_c, self.f_y)
        beta_1 = calc_beta1(f_c)
        self.c = self.a / beta_1
        self.d_v = calc_dv(height, self.d_s, self.c)
        
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
        self.epsilon_t = epsilon_c * (self.d_s - self.c) / self.c

    def set_Vc(self) -> float:
        """
        Assumes simplified procedure.

        Parameters:
        - d_v: Effective shear depth (in).
        - beta: Tension and shear transmission factor.

        Returns:
        - Concrete shear capacity, V_c (kips).
        """
        beta = 2
        self.V_c = 0.0316 * beta * self.lambda_ * self.f_c ** 0.5 * self.b * self.d_v

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