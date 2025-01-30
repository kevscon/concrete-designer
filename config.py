import os

# numerical input
num_keys = [
    'M_u',
    'V_u',
    'M_s',
    'width',
    'height',
    'cover',
    'spacing',
    'f_c',
    'concDensity',
    'phi_m',
    'phi_v'
]
# selection input
select_keys = [
    'crackClass',
    'size',
    'steelGrade'
]

# rebar properties
local_props_path = '/data/props.csv'
# rebar grade
local_grade_path = '/data/grade.csv'

props_path = os.getcwd() + local_props_path
grade_path = os.getcwd() + local_grade_path