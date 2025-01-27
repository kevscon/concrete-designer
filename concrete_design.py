def calc_stress(M, y, I):
    """
    Calculates stress in beam due to bending moment (ksi).

    Parameters:
    - M: Applied moment (k-ft).
    - y: Distance from neutral access (in).
    - I: Moment of inertia (in⁴).
    """
    return M * 12 * y / I

def calc_demand_ratio(load, capacity, resistance_factor=1):
    """
    Calculates the ratio of load to capacity.
    """
    return load / (resistance_factor * capacity)

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
        - phi_Vn: Factored Shear capacity
        """
        self.phi_Mn = self.phi_m * self.beam_instance.M_n
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

    def set_min_reinf(self, gamma_1=1.6):
        """
        Calculates design moment based on minimum reinforcement criteria.

        Parameters:
        - M_cr: Cracking moment (k-ft).
        - gamma_1: AASHTO flexure cracking variation factor - 1.2 precast segmental, 1.6 other.
        - gamma_3: AASHTO yield strength to ultimate strength ratio factor.

        Returns:
        - Design moment (k-ft).
        """
        M_cr = self.beam_instance.M_cr
        gamma_3 = self.beam_instance.gamma_3
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

    def set_gamma_e(self, crack_width):
        """
        Determines factor for AASHTO crack control.

        Parameters:
        - crack_width: Maximum crack width (in).
        """
        crack_base = 0.017
        self.gamma_e = crack_width / crack_base

    def set_design_spacing(self, crack_width=0.0085):
        """
        Calculates maximum spacing for flexure reinforcement based on service stress.

        Parameters:
        - crack_width: Maximum crack width (in).
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

        if f_ct > 0.8 * f_r:
            beta_s = 1 + d_c / (0.7 * (h - d_c))
            f_ss = min(f_s, 0.6 * f_y)
            self.set_gamma_e(crack_width)
            self.s_max = 700 * self.gamma_e / (beta_s * f_ss) - 2 * d_c
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