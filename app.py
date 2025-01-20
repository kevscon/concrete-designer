from flask import Flask, request, jsonify
from flask_cors import CORS
from config import props_path
import rebar_props
from conc_analysis_classes import calc_stress, ConcreteBeam, BeamStress, BeamCapacity
import design_check_funcs

app = Flask(__name__)
CORS(app)

def extract_data(data, keys):
    return {key: float(data.get(key, 0)) if key not in ['size'] else data.get(key, '') for key in keys}

def calculate_rebar_properties(bar_size):
    rebar = rebar_props.RebarProperties(bar_size, props_path)
    return rebar.bar_diameter, rebar.bar_area

@app.route('/beam-analysis', methods=['POST'])
def beam_analysis():
    data = request.json
    keys = [
        'M_u',
        'M_s',
        'V_u',
        'width',
        'height',
        'cover',
        'size',
        'spacing',
        'f_y',
        'f_c',
        'concDensity',
        'phi_m',
        'phi_v'
    ]
    values = extract_data(data, keys)

    bar_size = values['size']
    bar_diameter, bar_area = calculate_rebar_properties(bar_size)
    num_bars = values['width'] / values['spacing']
    steel_area = num_bars * bar_area
    steel_area_per_ft = rebar_props.calc_As_per_ft(bar_area, values['spacing'])
    d_c = rebar_props.calc_position(values['cover'], bar_diameter)

    beam = ConcreteBeam(
        values['width'], 
        values['height'], 
        d_c, 
        values['f_c'], 
        values['concDensity']
        )
    f_r = beam.calc_fr()
    beam.set_Ig()
    M_cr = beam.calc_Mcr()
    cracked = values['M_s'] >= M_cr

    stress_analyzer = BeamStress(
        values['width'], 
        values['height'], 
        d_c, 
        values['f_c'], 
        values['concDensity'], 
        steel_area, 
        values['M_s']
        )
    stress_analyzer.set_stresses()

    capacity_analyzer = BeamCapacity(
        values['width'], 
        values['height'], 
        d_c, 
        values['f_c'], 
        values['concDensity'], 
        steel_area, values['f_y']
        )
    M_n = capacity_analyzer.calc_moment_capacity()
    phi_Mn = values['phi_m'] * M_n
    epsilon_st = capacity_analyzer.calc_epsilon_t()
    V_n = capacity_analyzer.calc_shear_capacity()
    phi_Vn = values['phi_v'] * V_n

    gamma_3 = design_check_funcs.determine_gamma_3(values['f_y'])
    gamma_1 = 1.6
    M_design = design_check_funcs.calc_design_M(values['M_u'], M_cr, gamma_1, gamma_3)
    f_ct = calc_stress(values['M_s'], values['height'] / 2, beam.I_g)
    s_max = design_check_funcs.calc_design_spacing(f_r, f_ct, stress_analyzer.f_steel, values['f_y'], values['height'], d_c, gamma_e=0.75)
    epsilon_tl = design_check_funcs.calc_epsilon_tl(values['f_y'])
    A_ts = design_check_funcs.calc_dist_reinf(values['width'], values['height'], values['f_y'])
    gamma_er = design_check_funcs.calc_excess_reinf(M_design, phi_Mn)

    moment_capacity = phi_Mn >= values['M_u']
    shear_capacity = phi_Vn >= values['V_u']
    min_reinf = phi_Mn >= M_design
    crack_control = values['spacing'] <= s_max
    ductility = epsilon_st > epsilon_tl
    dist_reinf = steel_area_per_ft >= A_ts

    return jsonify({
        'weight': round(beam.w_DL, 2),
        'M_cr': round(M_cr, 1),
        'steel_area': round(steel_area, 3),
        'steel_area_per_ft': round(steel_area_per_ft, 3),
        'cracked': cracked,
        'fConc': round(stress_analyzer.f_conc, 3),
        'fSteel': round(stress_analyzer.f_steel, 3),
        "phiMn": round(phi_Mn, 1),
        "epsilon_st": round(epsilon_st, 4),
        "phiVn": round(phi_Vn, 1),
        'A_ts': round(A_ts, 2),
        'gamma_er': round(gamma_er, 2),
        'moment_capacity': moment_capacity,
        'shear_capacity': shear_capacity,
        'min_reinf': min_reinf,
        'crack_control': crack_control,
        'ductility': ductility,
        'dist_reinf': dist_reinf
    })

if __name__ == "__main__":
    app.run(debug=True)
