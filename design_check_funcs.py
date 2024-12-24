def check_capacity(capacity, load, resistance_factor=1):
    """
    Calculates the design ratio.
    """
    return resistance_factor * capacity / load

def calc_capacity_ratio(load, capacity, resistance_factor=1):
    """
    Calculates the ratio of capacity to load.
    """
    return resistance_factor * capacity / load

def calc_demand_ratio(load, capacity, resistance_factor=1):
    """
    Calculates the ratio of load to capacity.
    """
    return load / (resistance_factor * capacity)

def calc_epsilon_tl(f_y, epsilon_c=0.003):
    """
    Calculates the minimum steel strain required for a ductile section.

    Parameters:
    - f_y: Yield strength of steel (ksi).
    - epsilon_c: Design concrete compressive strain.
    """
    if f_y <= 75:
        epsilon_tl = 0.005
    else:
        epsilon_tl = (f_y - 75) / (100 - 75) * epsilon_c + 0.005
    return epsilon_tl

def determine_gamma_3(f_y):
    """
    Determine value for the AASHTO yield strength to ultimate strength ratio factor.

    Parameters:
    - f_y: Yield strength of steel (ksi).
    """
    if f_y == 75:
        gamma_3 = 0.75
    elif f_y == 80:
        gamma_3 = 0.76
    else:
        gamma_3 = 0.67
    return gamma_3

def calc_design_M(M_u, M_cr, gamma_3=0.67, gamma_1=1.6):
    """
    Calculates design moment based on minimum reinforcement criteria.

    Parameters:
    - M_u: Factored moment load (k-ft).
    - M_cr: Cracking moment (k-ft).
    - gamma_1: AASHTO flexure cracking variation factor.
    - gamma_3: AASHTO yield strength to ultimate strength ratio factor.

    Returns:
    - Design moment (k-ft).
    """
    M_design = max(min(gamma_1 * gamma_3 * M_cr, 1.33 * M_u), M_u)
    return M_design

def calc_design_spacing(f_r, f_ct, f_s, f_y, h, d_c, gamma_e=0.75):
    """
    Calculates maximum spacing for flexure reinforcement based on service stress.

    Parameters:
    - f_r: Modulus of rupture (ksi).
    - f_ct: Tensile stress in uncracked concrete section (ksi).
    - f_s: Tensile service stress in reinforcing (ksi).
    - f_y: Yield strength of steel (ksi).
    - h: Beam height (in).
    - d_c: Concrete face in tension to center of reinforcing (in).
    - gamma_e: AASHTO exposure factor.

    Returns:
    - Maximum spacing, s_max (in).
    """
    beta_s = 1 + d_c / (0.7 * (h - d_c))
    f_ss = min(f_s, 0.6 * f_y)
    if f_ct > 0.8 * f_r:
        s_max = 700 * gamma_e / (beta_s * f_ss) - 2 * d_c
    else:
        s_max = 18
    return s_max

def calc_excess_reinf(M_design, phi_Mn):
    """
    Calculates excess reinforcement factor, gamma_er.

    Parameters:
    - M_design: Design moment load (k-ft).
    - phi_Mn: Factored moment capacity (k-ft).
    """
    gamma_er = M_design / phi_Mn
    return round(gamma_er, 2)

def calc_dist_reinf(width, height, f_y):
    """
    Calculates the required distribution reinforcement for a section.

    Parameters:
    - width: Beam width in cross-section (in).
    - height: Beam height in cross-section (in).
    - f_y: Yield strength of steel (ksi).

    Returns:
    - Reinforcing area per foot (in²/ft).
    """
    A_TS = 1.3 * width * height / (2 * (width + height) * f_y)
    return round(min(max(A_TS, 0.11), 0.6), 3)