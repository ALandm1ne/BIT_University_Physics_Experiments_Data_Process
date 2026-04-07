"""太阳能电池实验数据处理脚本。

功能概览：
1. 基于 data1 绘制 I-U 与 ln(I)-U 曲线。
2. 基于 data2 / data3 绘制 P-Rx 曲线。
3. 若 data2 或 data3 缺少功率行（第4行），自动按 P=U*I 回填（mW）。
4. 将 data2 与 data3 合并，统一计算填充因子 FF。

单位约定：
- U: V
- I: mA
- P: mW（因为 V * mA = mW）
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA1_FILE = BASE_DIR / 'data1_U-I-ln(I).csv'
DATA2_FILE = BASE_DIR / 'data2_Rx-U-I_100Ω步长.csv'
DATA3_FILE = BASE_DIR / 'data3_Rx-U-I_10Ω步长.csv'
RESULT_FILE = BASE_DIR / 'result.txt'


def read_data1(file_path: Path):
	"""读取 data1: 第1行 U, 第2行 I, 第3行 ln(I)。"""
	data = pd.read_csv(file_path, header=None)
	if data.shape[0] < 3:
		raise ValueError('data1 至少需要 3 行：U、I、ln(I)')

	u = data.iloc[0].astype(float).to_numpy()
	i = data.iloc[1].astype(float).to_numpy()
	ln_i = data.iloc[2].astype(float).to_numpy()
	return u, i, ln_i


def read_power_dataset(file_path: Path):
	"""读取功率数据集（data2/data3），必要时自动回填第4行功率。"""
	data = pd.read_csv(file_path, header=None)
	if data.shape[0] < 3:
		raise ValueError(f'{file_path.name} 至少需要 3 行：Rx、U、I')

	rx = data.iloc[0].astype(float).to_numpy()
	u = data.iloc[1].astype(float).to_numpy()
	i = data.iloc[2].astype(float).to_numpy()

	# 若功率行缺失，则按 P=U*I（mW）计算并回填 CSV
	if data.shape[0] < 4:
		p_mw = u * i
		data.loc[3] = p_mw
		data.to_csv(file_path, header=False, index=False)
	else:
		p_mw = data.iloc[3].astype(float).to_numpy()

	return data, rx, u, i, p_mw


def compute_fill_factor(u_all, i_all, p_all_mw):
	"""按 FF = Pmax / (Voc * Isc) 计算填充因子。"""
	p_max_mw = p_all_mw.max()
	isc_ma = i_all.max()

	# Voc 优先取 I=0 的测点电压；若无 I=0 点，则退化为 U 最大值。
	zero_current_idx = i_all == 0
	if zero_current_idx.any():
		voc_v = float(u_all[zero_current_idx][0])
	else:
		voc_v = u_all.max()

	ff = p_max_mw / (voc_v * isc_ma)
	return p_max_mw, voc_v, isc_ma, ff


def main():
	"""主流程：读数、绘图、合并计算 FF、输出结果。"""
	# ---------- data1: I-U 与 ln(I)-U ----------
	u, i, ln_i = read_data1(DATA1_FILE)

	# ln(I)-U 线性回归：ln(I) = k*U + b
	k, b = np.polyfit(u, ln_i, 1)
	ln_i_fit = k * u + b
	ss_res = np.sum((ln_i - ln_i_fit) ** 2)
	ss_tot = np.sum((ln_i - np.mean(ln_i)) ** 2)
	r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 1.0
	b_sign = '+' if b >= 0 else '-'
	b_abs = abs(b)

	plt.figure(figsize=(8, 6))
	plt.plot(u, i, 'o-', markersize=3, linewidth=1.5, label='I-U Data')
	plt.xlabel('U (V)', fontsize=12)
	plt.ylabel('I (mA)', fontsize=12)
	plt.title('I-U Characteristic Curve', fontsize=14)
	plt.grid(True, linestyle='--', alpha=0.6)
	plt.legend()
	plt.tight_layout()
	plt.savefig(BASE_DIR / 'I-U_curve.png', dpi=300)

	plt.figure(figsize=(8, 6))
	plt.plot(u, ln_i, 's-', markersize=3, linewidth=1.5, color='tab:red', label='ln(I)-U Data')
	plt.plot(u, ln_i_fit, '--', linewidth=1.5, color='tab:blue', label='Linear Fit')
	plt.xlabel('U (V)', fontsize=12)
	plt.ylabel('ln(I)', fontsize=12)
	plt.title('ln(I)-U Curve', fontsize=14)
	plt.grid(True, linestyle='--', alpha=0.6)
	plt.legend()
	plt.tight_layout()
	plt.savefig(BASE_DIR / 'lnI-U_curve.png', dpi=300)

	# ---------- data2 / data3: P-Rx ----------
	data2, rx2, u2, i2, p2_mw = read_power_dataset(DATA2_FILE)
	_, rx3, u3, i3, p3_mw = read_power_dataset(DATA3_FILE)

	# data2 最后一列为极大电阻测点，绘图时忽略。
	rx2_plot = rx2[:-1]
	p2_plot_mw = p2_mw[:-1]

	# 将 data2 与 data3 合并为同一条 P-Rx 曲线（按 Rx 升序连接）
	rx_merge_plot = np.concatenate([rx2_plot, rx3])
	p_merge_plot = np.concatenate([p2_plot_mw, p3_mw])
	sort_idx = np.argsort(rx_merge_plot)
	rx_merge_plot = rx_merge_plot[sort_idx]
	p_merge_plot = p_merge_plot[sort_idx]
	p_max_idx_plot = int(np.argmax(p_merge_plot))
	rx_pmax_plot = float(rx_merge_plot[p_max_idx_plot])
	p_pmax_plot = float(p_merge_plot[p_max_idx_plot])
	x_mid = float((np.min(rx_merge_plot) + np.max(rx_merge_plot)) / 2)
	y_mid = float((np.min(p_merge_plot) + np.max(p_merge_plot)) / 2)
	offset_x = -110 if rx_pmax_plot >= x_mid else 28
	offset_y = -34 if p_pmax_plot >= y_mid else 28
	ha = 'right' if rx_pmax_plot >= x_mid else 'left'
	va = 'top' if p_pmax_plot >= y_mid else 'bottom'

	plt.figure(figsize=(8, 6))
	plt.plot(rx_merge_plot, p_merge_plot, 'o-', markersize=3, linewidth=1.4, color='tab:green', label='merged P-Rx')
	plt.scatter(rx_pmax_plot, p_pmax_plot, color='tab:red', s=35, zorder=5, label='Pmax point')
	plt.annotate(
		f'Pmax({rx_pmax_plot:.0f} ohm, {p_pmax_plot:.3f} mW)',
		xy=(rx_pmax_plot, p_pmax_plot),
		xytext=(offset_x, offset_y),
		textcoords='offset points',
		fontsize=10,
		color='tab:red',
		ha=ha,
		va=va,
		bbox={
			'boxstyle': 'round,pad=0.25',
			'fc': 'white',
			'ec': 'tab:red',
			'alpha': 0.9
		},
		arrowprops={
			'arrowstyle': '->',
			'color': 'tab:red',
			'lw': 1.0,
			'shrinkA': 2,
			'shrinkB': 2
		}
	)
	plt.xlabel('Rx (ohm)', fontsize=12)
	plt.ylabel('P (mW)', fontsize=12)
	plt.title('P-Rx Curve (merged data2 + data3)', fontsize=14)
	plt.grid(True, linestyle='--', alpha=0.6)
	plt.legend()
	plt.tight_layout()
	plt.savefig(BASE_DIR / 'P-Rx_curve.png', dpi=300)

	# ---------- 合并 data2 + data3 统一计算 FF ----------
	u_all = pd.concat([pd.Series(u2), pd.Series(u3)], ignore_index=True).to_numpy()
	i_all = pd.concat([pd.Series(i2), pd.Series(i3)], ignore_index=True).to_numpy()
	p_all_mw = pd.concat([pd.Series(p2_mw), pd.Series(p3_mw)], ignore_index=True).to_numpy()

	p_max_mw, voc_v, isc_ma, ff = compute_fill_factor(u_all, i_all, p_all_mw)

	print(f'Pmax = {p_max_mw:.4f} mW')
	print(f'Voc = {voc_v:.4f} V')
	print(f'Isc = {isc_ma:.4f} mA')
	print(f'Fill Factor (FF) = {ff:.4f}')
	print(f'Linear Fit: ln(I) = {k:.6f} * U {b_sign} {b_abs:.6f}')
	print(f'R^2 = {r2:.6f}')

	with open(RESULT_FILE, 'w', encoding='utf-8') as f:
		f.write('ln(I)-U linear regression\n')
		f.write(f'k={k:.6f}\n')
		f.write(f'b={b:.6f}\n')
		f.write(f'equation: ln(I)={k:.6f}*U{b_sign}{b_abs:.6f}\n')
		f.write(f'R2={r2:.6f}\n')
		f.write('\n')
		f.write('Fill factor result\n')
		f.write(f'Pmax(mW)={p_max_mw:.6f}\n')
		f.write(f'Voc(V)={voc_v:.6f}\n')
		f.write(f'Isc(mA)={isc_ma:.6f}\n')
		f.write(f'FF={ff:.6f}\n')

	plt.show()


if __name__ == '__main__':
	main()