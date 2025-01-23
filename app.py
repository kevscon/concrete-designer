from flask import Flask, request, jsonify
from flask_cors import CORS
from concrete_design import ConcreteAnalyzer, ConcreteDesign

app = Flask(__name__)
CORS(app)

def extract_data(data, keys):
    return {key: float(data.get(key, 0)) if key not in ['size'] else data.get(key, '') for key in keys}

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

    beam = ConcreteAnalyzer(
        values['width'], 
        values['height'], 
        values['size'], # bar_size
        values['spacing'], # bar_spacing
        values['cover'], # bar_cover
        values['f_c'], 
        values['f_y'],
        values['concDensity']
        )

    # beam properties
    w_DL = beam.w_DL
    M_cr = beam.M_cr
    steel_area = beam.A_s
    As_per_ft = beam.As_per_ft
    # beam analysis
    beam.set_stresses(values['M_s'])
    cracked = beam.cracked
    conc_stress = beam.f_conc
    steel_stress = beam.f_steel
    epsilon_st = beam.epsilon_t
    # beam design
    design = ConcreteDesign(
        beam, 
        values['M_u'], 
        values['M_s'], 
        values['V_u'], 
        values['phi_m'], 
        values['phi_v']
        )
    A_ts = design.A_ts
    phi_Mn = design.phi_Mn
    phi_Vn = design.phi_Vn
    design.set_min_reinf()
    gamma_er = design.calc_excess_reinf()
    design.set_design_spacing()
    design.set_checks()

    return jsonify({
        'weight': round(w_DL, 2),
        'M_cr': round(M_cr, 1),
        'steel_area': round(steel_area, 3),
        'steel_area_per_ft': round(As_per_ft, 3),
        'cracked': cracked,
        'fConc': round(conc_stress, 3),
        'fSteel': round(steel_stress, 3),
        "phiMn": round(phi_Mn, 1),
        "epsilon_st": round(epsilon_st, 4),
        "phiVn": round(phi_Vn, 1),
        'A_ts': round(A_ts, 2),
        'gamma_er': round(gamma_er, 2),

        'moment_capacity': design.moment_capacity,
        'shear_capacity': design.shear_capacity,
        'min_reinf': design.min_reinf,
        'crack_control': design.crack_control,
        'ductility': design.ductility,
        'dist_reinf': design.dist_reinf
    })

if __name__ == "__main__":
    app.run(debug=True)
