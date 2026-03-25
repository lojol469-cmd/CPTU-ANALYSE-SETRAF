import sys, io, os
sys.path.insert(0, 'app')
import pandas as pd
import numpy as np
from tools.cptu_svg_animator import generate_cptu_animation, _detect_layers

path = r'C:\Users\Admin\Documents\LABOFICHE\donnée CPTU\CPTU1.txt'

with open(path, encoding='utf-8', errors='replace') as f:
    raw = f.read().replace(',', '.')

df = pd.read_csv(io.StringIO(raw), sep='\t')
df.columns = ['Depth', 'qc', 'fs']
df = df.apply(pd.to_numeric, errors='coerce').dropna()
print('Rows:', len(df))
print(df.head(3).to_string())

layers = _detect_layers(df)
print(f'\nCouches detectees: {len(layers)}')
for la in layers:
    print(f"  {la['start_m']:.2f}-{la['end_m']:.2f} m  {la['label']}  qc={la['avg_qc']} MPa")

svg = generate_cptu_animation(df, title='CPTU1 SETRAF ANALYSE')
out = 'app/cptu1_test.svg'
with open(out, 'w', encoding='utf-8') as f:
    f.write(svg)
print(f'\nSVG genere: {len(svg)} chars -> {out}')
