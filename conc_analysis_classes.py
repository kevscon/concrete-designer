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
    Calculates concrete modulus of rupture.

    Parameters:
    - f_c: Compressive strength of concrete (ksi).

    Returns:
    - Modulus of rupture (ksi).
    """
    return 0.24 * f_c ** 0.5

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


class ConcreteBeam:
    def __init__(self, width: float, height: float, d_c: float, f_c: float, conc_density: float):
        """
        Base class for concrete beam properties.
        
        Parameters:
        - width: Beam width (in).
        - height: Beam height (in).
        - d_c: Centroid of reinforcing from concrete face in tension (in).
        - f_c: Compressive strength of concrete (ksi).
        - conc_density: Concrete density (pcf).

        Initialized properties:
        - A_g: Area of uncracked concrete section (in²).
        - w_DL: Dead load due to beam self-weight (k/ft).
        - y_g: Centroid of uncracked section from concrete face in compression (in).
        - E_c: Elastic modulus of concrete (ksi).
        - d: Effective depth of reinforcing (in).
        """
        self.b = width
        self.h = height
        self.d_c = d_c
        self.f_c = f_c

        self.A_g = width * height
        self.w_DL = conc_density / 1000 * self.A_g / 144
        self.E_c = calc_Ec(f_c, conc_density)
        self.d = height - d_c

    def set_Ig(self) -> float:
        """
        Returns:
        - Moment of inertia (in⁴).
        """
        self.I_g = self.b * self.h ** 3 / 12
    
    def set_Sc(self) -> float:
        """
        Returns:
        - Section modulus (in³)
        """
        self.S_c = (1/12 * self.b * self.h ** 3) / (self.h / 2)
    
    def calc_Mcr(self) -> float:
        """
        Returns:
        - Cracking moment, M_cr (k-ft).
        """
        f_r = calc_fr(self.f_c)
        self.set_Sc()
        return f_r * self.S_c / 12
    
    def report(self) -> dict:
        return {
            'd_s': [round(self.d(), 1), 'in'],
            'w_DL': [round(self.w_DL(), 2), 'k/ft'],
            'M_cr': [round(self.M_cr, 1) if hasattr(self, 'M_cr') else None, 'k-ft'],
        }

class BeamCapacity(ConcreteBeam):
    def __init__(self, width, height, d_c, f_c, conc_density, steel_area: float, f_y: float):
        """
        Subclass to calculate beam capacity.

        Parameters:
        - steel_area, A_s: Area of steel reinforcement (in²).
        - f_y: Yield strength of steel (ksi).
        """
        super().__init__(width, height, d_c, f_c, conc_density)
        self.A_s = steel_area
        self.f_y = f_y

    def set_comp_block_depth(self) -> float:
        """
        Calculates the depth of the compressive stress block, a (in).
        """
        self.a = (self.A_s * self.f_y) / (0.85 * self.f_c * self.b)

    def calc_moment_capacity(self) -> float:
        """
        Returns:
        - Moment capacity, M_n (k-ft).
        """
        self.set_comp_block_depth()
        return self.A_s * self.f_y * (self.d - self.a / 2) / 12
    
    def calc_epsilon_t(self, epsilon_c=0.003):
        """
        Calculates design tensile strain in steel.

        Parameters:
        - epsilon_c: Design concrete compressive strain.
        """
        beta_1 = calc_beta1(self.f_c)
        self.set_comp_block_depth()
        c = self.a / beta_1
        return epsilon_c * (self.d - c) / c

    def set_dv(self):
        """
        Calculates effective shear depth, d_v (in).
        """
        beta_1 = calc_beta1(self.f_c)
        self.set_comp_block_depth()
        c = self.a / beta_1
        self.d_v = max(self.d - c / 2, 0.9 * self.d, 0.72 * self.h)

    def calc_Vc(self, gamma=1, beta=2) -> float:
        """
        Parameters:
        - lambda: Concrete density modification factor.
        - beta: Tension and shear transmission factor.

        Returns:
        - Concrete shear capacity, V_c (kips).
        """
        self.set_dv()
        return 0.0316 * beta * gamma * self.f_c ** 0.5 * self.b * self.d_v

    def calc_shear_capacity(self, V_s=0):
        """
        Returns:
        - Shear capacity, V_n (kips).
        """
        V_c = self.calc_Vc()
        max_V_n = 0.25 * self.f_c * self.b * self.d_v
        return min(V_c + V_s, max_V_n)

    def report(self) -> dict:
        return {
            'moment_capacity': [round(self.calc_moment_capacity(), 1), 'k-ft'],
            'shear_capacity': [round(self.calc_shear_capacity(), 1), 'kips'],
            'comp_block_depth': [round(self.a, 2) if hasattr(self, 'a') else None, 'in'],
            'epsilon_t': [round(self.calc_epsilon_t(), 4), ''],
            'effective_shear_depth': [round(self.d_v, 1) if hasattr(self, 'd_v') else None, 'in'],
            'concrete_shear_capacity': [round(self.calc_Vc(), 1), 'kips'],
        }
    
class BeamStress(ConcreteBeam):
    def __init__(self, width, height, d_c, f_c, conc_density, steel_area: float, E_s: float, M: float):
        """
        Subclass to calculate beam stresses.

        Parameters:
        - steel_area, A_s: Area of steel reinforcement (in²).
        - E_s: Elastic modulus of steel (ksi).
        - M: Service moment applied to beam (k-ft).

        Initializes:
        - n: Modular ratio.
        - cracked: Is beam cracked? True/False.
        """
        super().__init__(width, height, d_c, f_c, conc_density)
        self.A_s = steel_area
        self.M = M

        self.n = calc_n(E_s, self.E_c)
        M_cr = self.calc_Mcr()
        self.cracked = M >= M_cr

    def calc_rho(self) -> float:
        """
        Calculates the reinforcement ratio, rho.
        """
        return self.A_s / (self.b * self.d)

    def calc_k(self) -> float:
        """
        Calculates the compressive depth factor, k.
        """
        rho = self.calc_rho()
        return -rho * self.n + ((rho * self.n) ** 2 + 2 * rho * self.n)**0.5

    def calc_j(self) -> float:
        """
        Calculates the moment arm factor, j.
        """
        k = self.calc_k()
        return 1 - k / 3

    def set_stresses(self):
        """
        Calculates stress in concrete and steel (ksi).
        """
        if self.cracked == True:
            j = self.calc_j()
            k = self.calc_k()
            self.f_conc = 2 * self.M * 12 / (j * k * self.b * self.d**2)
            self.f_steel = self.M * 12 / (self.A_s * j * self.d)
        else:
            self.set_Ig()
            self.f_conc = calc_stress(self.M, self.h / 2, self.I_g)
            self.f_steel = self.n * calc_stress(self.M, self.d - self.h / 2, self.I_g)

    def report(self) -> dict:
        return {
            'cracked': [self.cracked, ''],
            'conc_stress': [round(self.f_conc, 2) if hasattr(self, 'f_conc') else None, 'ksi'],
            'steel_stress': [round(self.f_steel, 2) if hasattr(self, 'f_steel') else None, 'ksi'],
        }