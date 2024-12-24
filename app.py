from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/weight', methods=['POST'])
def calc_weight():
    data = request.json
    width = float(data.get('width', 0))
    height = float(data.get('height', 0))
    conc_density = float(data.get('concDensity', 0))
    weight = conc_density / 1000 * width / 12 * height / 12
    return jsonify({'weight': round(weight, 2)})

@app.route('/steelArea', methods=['POST'])
def steel_area():
    data = request.json
    width = float(data.get('width', 0))
    bar_size = data.get('size', '')
    spacing = float(data.get('spacing', 0))

    import rebar_props
    rebar = rebar_props.RebarProperties(bar_size)
    bar_area = rebar.bar_area
    num_bars = width / spacing
    steel_area = num_bars * bar_area
    steel_area_per_ft = rebar_props.calc_As_per_ft(bar_area, spacing)
    return jsonify({
        "steel_area": round(steel_area, 3),
        "steel_area_per_ft": round(steel_area_per_ft, 3)
        })

@app.route('/slabStress', methods=['POST'])
def return_stress():
    data = request.json

    M_s = float(data.get('M_s', 0))

    width = float(data.get('width', 0))
    height = float(data.get('height', 0))
    cover = float(data.get('cover', 0))

    bar_size = data.get('size', '')
    spacing = float(data.get('spacing', 0))
    
    f_c = float(data.get('f_c', 0))
    E_s = float(data.get('E_s', 0))
    conc_density = float(data.get('concDensity', 0))

    import rebar_props
    rebar = rebar_props.RebarProperties(bar_size)
    bar_diameter = rebar.bar_diameter
    d_c = rebar_props.calc_position(cover, bar_diameter)
    bar_area = rebar.bar_area
    num_bars = width / spacing
    steel_area = num_bars * bar_area

    from conc_analysis_classes import BeamStress
    stress_analyzer = BeamStress(width, height, d_c, f_c, conc_density, steel_area, E_s, M_s)
    stress_analyzer.set_stresses()
    cracked = stress_analyzer.cracked
    f_conc = stress_analyzer.f_conc
    f_steel = stress_analyzer.f_steel

    return jsonify({
        "cracked": cracked,
        "fConc": round(f_conc, 3),
        "fSteel": round(f_steel, 3)
        })

@app.route('/slabCapacity', methods=['POST'])
def return_capacity():
    data = request.json

    width = float(data.get('width', 0))
    height = float(data.get('height', 0))
    cover = float(data.get('cover', 0))

    bar_size = data.get('size', '')
    spacing = float(data.get('spacing', 0))
    
    f_y = float(data.get('f_y', 0))
    f_c = float(data.get('f_c', 0))
    conc_density = float(data.get('concDensity', 0))

    phi_m = float(data.get('phi_m', 0))
    phi_v = float(data.get('phi_v', 0))

    import rebar_props
    rebar = rebar_props.RebarProperties(bar_size)
    bar_diameter = rebar.bar_diameter
    d_c = rebar_props.calc_position(cover, bar_diameter)
    bar_area = rebar.bar_area
    num_bars = width / spacing
    steel_area = num_bars * bar_area

    from conc_analysis_classes import BeamCapacity
    capacity_analyzer = BeamCapacity(width, height, d_c, f_c, conc_density, steel_area, f_y)
    M_n = capacity_analyzer.calc_moment_capacity()
    epsilon_st = capacity_analyzer.calc_epsilon_t()
    V_n = capacity_analyzer.calc_shear_capacity()
    return jsonify({
        "phiMn": round(phi_m * M_n, 1),
        "epsilon_st": round(epsilon_st, 4),
        "phiVn": round(phi_v * V_n, 1)
        })

if __name__ == "__main__":
    app.run(debug=True)
