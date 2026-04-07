import csv
import math
import sys
from pathlib import Path


# 已知常量（SI 单位）
M_KG = 25.0 / 1000.0
R_M = 25.00 / 1000.0
G = 9.83
THETA_RAD = 9.0 * math.pi
OMEGA0 = 0.0
DISK_R_M = 120.00 / 1000.0
DISK_R_U_M = 0.02 / 1000.0
MASS_U_KG = 1.0 / 1000.0

OUTPUT_FILE = "results.csv"


def read_beta_columns(csv_path: Path) -> tuple[list[float], list[float]]:
	beta: list[float] = []
	beta_prime: list[float] = []

	if not csv_path.exists():
		raise FileNotFoundError(f"输入文件不存在: {csv_path}")

	with csv_path.open("r", encoding="utf-8", newline="") as f:
		reader = csv.reader(f)
		for row_index, row in enumerate(reader, start=1):
			if len(row) < 2:
				raise ValueError(f"第 {row_index} 行列数不足 2: {row}")
			try:
				beta_value = float(row[0].strip())
				beta_prime_value = float(row[1].strip())
			except ValueError as exc:
				raise ValueError(f"第 {row_index} 行存在非数值数据: {row}") from exc

			beta.append(beta_value)
			beta_prime.append(beta_prime_value)

	if len(beta) < 2:
		raise ValueError("数据行数不足 2，无法计算 A 类不确定度")

	return beta, beta_prime


def mean(values: list[float]) -> float:
	return sum(values) / len(values)


def u_a_of_mean(values: list[float]) -> float:
	n = len(values)
	x_bar = mean(values)
	ss = sum((x - x_bar) ** 2 for x in values)
	return math.sqrt(ss / (n * (n - 1)))


def calc_i0_and_uncertainty(
	beta_mean: float,
	beta_u_a: float,
	beta_prime_mean: float,
	beta_prime_u_a: float,
) -> tuple[float, float]:
	delta = beta_mean - beta_prime_mean
	if abs(delta) < 1e-12:
		raise ZeroDivisionError("beta 平均值与 beta_ 平均值差值过小，无法计算 I0")

	i0 = M_KG * G * R_M / delta

	# I0 = K / (beta - beta_), K = m g r
	# dI0/dbeta = -K/(beta-beta_)^2, dI0/dbeta_ = +K/(beta-beta_)^2
	coeff = (M_KG * G * R_M) / (delta ** 2)
	u_i0 = math.sqrt((coeff * beta_u_a) ** 2 + (coeff * beta_prime_u_a) ** 2)
	return i0, u_i0


def get_mass_from_input_or_argv(argv_index: int, prompt: str) -> float:
	if len(sys.argv) > argv_index:
		mass_grams = float(sys.argv[argv_index])
	else:
		mass_grams = float(input(prompt).strip())
	return mass_grams / 1000.0


def get_m2_kg() -> float:
	return get_mass_from_input_or_argv(1, "请输入 m2（单位 g，默认不确定度 1g）: ")


def get_disk_mass_kg() -> float:
	return get_mass_from_input_or_argv(2, "请输入铝盘质量（单位 g，默认不确定度 1g）: ")


def calc_theoretical_i_and_uncertainty(
	m2_kg: float,
	m2_u_kg: float,
	r_inner_m: float,
	r_inner_u_m: float,
	r_outer_m: float,
	r_outer_u_m: float,
) -> tuple[float, float]:
	theory_i = m2_kg * (r_inner_m ** 2 + r_outer_m ** 2) / 2.0
	d_i_dm = (r_inner_m ** 2 + r_outer_m ** 2) / 2.0
	d_i_drin = m2_kg * r_inner_m
	d_i_drout = m2_kg * r_outer_m
	theory_u = math.sqrt(
		(d_i_dm * m2_u_kg) ** 2
		+ (d_i_drin * r_inner_u_m) ** 2
		+ (d_i_drout * r_outer_u_m) ** 2
	)
	return theory_i, theory_u


def calc_disk_theoretical_i_and_uncertainty(
	disk_mass_kg: float,
	disk_mass_u_kg: float,
	disk_r_m: float,
	disk_r_u_m: float,
) -> tuple[float, float]:
	# 均匀圆盘: I = 1/2 * M * R^2
	i_theory = 0.5 * disk_mass_kg * (disk_r_m ** 2)
	d_i_dm = 0.5 * (disk_r_m ** 2)
	d_i_dr = disk_mass_kg * disk_r_m
	u_i_theory = math.sqrt((d_i_dm * disk_mass_u_kg) ** 2 + (d_i_dr * disk_r_u_m) ** 2)
	return i_theory, u_i_theory


def read_two_rows(csv_path: Path) -> tuple[list[float], list[float]]:
	if not csv_path.exists():
		raise FileNotFoundError(f"输入文件不存在: {csv_path}")

	rows: list[list[float]] = []
	with csv_path.open("r", encoding="utf-8", newline="") as f:
		reader = csv.reader(f)
		for row_index, row in enumerate(reader, start=1):
			if not row:
				continue
			try:
				rows.append([float(cell.strip()) for cell in row])
			except ValueError as exc:
				raise ValueError(f"第 {row_index} 行存在非数值数据: {row}") from exc

	if len(rows) != 2:
		raise ValueError(f"data3 需要恰好 2 行数据，当前为 {len(rows)} 行")
	if len(rows[0]) != len(rows[1]):
		raise ValueError("data3 两行列数不一致")
	if len(rows[0]) < 2:
		raise ValueError("data3 列数不足 2")

	return rows[0], rows[1]


def calc_inv_t2(values: list[float]) -> list[float]:
	inv: list[float] = []
	for index, t_value in enumerate(values, start=1):
		if abs(t_value) < 1e-12:
			raise ZeroDivisionError(f"第 {index} 个时间值为 0，无法计算 1/t^2")
		inv.append(1.0 / (t_value ** 2))
	return inv


def linear_fit(x_values: list[float], y_values: list[float]) -> tuple[float, float]:
	if len(x_values) != len(y_values):
		raise ValueError("拟合数据长度不一致")
	if len(x_values) < 2:
		raise ValueError("拟合点数不足 2")

	x_bar = mean(x_values)
	y_bar = mean(y_values)
	s_xx = sum((x - x_bar) ** 2 for x in x_values)
	if abs(s_xx) < 1e-18:
		raise ZeroDivisionError("x 数据离散度过小，无法线性拟合")
	s_xy = sum((x - x_bar) * (y - y_bar) for x, y in zip(x_values, y_values))
	slope = s_xy / s_xx
	intercept = y_bar - slope * x_bar
	return slope, intercept


def format_decimal(value: float) -> str:
	formatted = f"{value:.15f}".rstrip("0").rstrip(".")
	if formatted == "-0":
		formatted = "0"
	return formatted


def format_value_list(values: list[float]) -> str:
	return "; ".join(format_decimal(v) for v in values)


def fit_equation_text(slope: float, intercept: float) -> str:
	return f"m = {format_decimal(slope)}*(1/t^2) + {format_decimal(intercept)}"


def process_data3(csv_path: Path, disk_mass_kg: float) -> list[tuple[str, str, float | str] | None]:
	t_with_disk, t_without_disk = read_two_rows(csv_path)
	point_count = len(t_with_disk)
	masses_kg = [(15.0 + 5.0 * i) / 1000.0 for i in range(point_count)]

	inv_t2_with = calc_inv_t2(t_with_disk)
	inv_t2_without = calc_inv_t2(t_without_disk)

	k_with, b_with = linear_fit(inv_t2_with, masses_kg)
	k_without, b_without = linear_fit(inv_t2_without, masses_kg)

	# 用户确认公式: k = 2*I*theta/(g*r) => I = k*g*r/(2*theta)
	i_with = k_with * G * R_M / (2.0 * THETA_RAD)
	i_without = k_without * G * R_M / (2.0 * THETA_RAD)
	i_disk_exp = i_with - i_without

	i_disk_theory, u_i_disk_theory = calc_disk_theoretical_i_and_uncertainty(
		disk_mass_kg=disk_mass_kg,
		disk_mass_u_kg=MASS_U_KG,
		disk_r_m=DISK_R_M,
		disk_r_u_m=DISK_R_U_M,
	)

	return [
		("data3", "inv_t2_with_disk", format_value_list(inv_t2_with)),
		("data3", "fit_with_disk", fit_equation_text(k_with, b_with)),
		("data3", "I_with_disk", i_with),
		("data3", "inv_t2_without_disk", format_value_list(inv_t2_without)),
		("data3", "fit_without_disk", fit_equation_text(k_without, b_without)),
		("data3", "I_without_disk", i_without),
		None,
		("", "I_disk_exp", i_disk_exp),
		("", "I_disk_theory", i_disk_theory),
		("", "uI_disk_theory", u_i_disk_theory),
		("", "theta_rad", THETA_RAD),
		("", "omega0", OMEGA0),
	]


def write_results(output_path: Path, rows: list[tuple[str, str, float | str] | None]) -> None:
	with output_path.open("w", encoding="utf-8", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["dataset", "item", "value"])
		for row in rows:
			if row is None:
				writer.writerow([])
				continue
			dataset, key, value = row
			formatted = value if isinstance(value, str) else format_decimal(value)
			writer.writerow([dataset, key, formatted])


def process_dataset(dataset_name: str, csv_path: Path) -> list[tuple[str, str, float]]:
	beta, beta_prime = read_beta_columns(csv_path)

	beta_mean = mean(beta)
	beta_u_a = u_a_of_mean(beta)
	beta_prime_mean = mean(beta_prime)
	beta_prime_u_a = u_a_of_mean(beta_prime)

	i0, u_i0 = calc_i0_and_uncertainty(
		beta_mean=beta_mean,
		beta_u_a=beta_u_a,
		beta_prime_mean=beta_prime_mean,
		beta_prime_u_a=beta_prime_u_a,
	)

	return [
		(dataset_name, "beta_mean", beta_mean),
		(dataset_name, "uA_beta", beta_u_a),
		(dataset_name, "beta_prime_mean", beta_prime_mean),
		(dataset_name, "uA_beta_prime", beta_prime_u_a),
		(dataset_name, "I", i0),
		(dataset_name, "uI", u_i0),
	]


def get_result_value(rows: list[tuple[str, str, float]], dataset_name: str, item_name: str) -> float:
	for dataset, item, value in rows:
		if dataset == dataset_name and item == item_name:
			return value
	raise KeyError(f"未找到结果项: {dataset_name}/{item_name}")


def main() -> None:
	base = Path(__file__).resolve().parent
	output_path = base / OUTPUT_FILE
	m2_kg = get_m2_kg()
	disk_mass_kg = get_disk_mass_kg()
	m2_u_kg = 1.0 / 1000.0
	r_inner_m = 105.00 / 1000.0
	r_inner_u_m = 0.02 / 1000.0
	r_outer_m = 120.00 / 1000.0
	r_outer_u_m = 0.02 / 1000.0

	results = []
	data1_results = process_dataset("data1", base / "data1_without_anything.csv")
	data2_results = process_dataset("data2", base / "data2_with_ring.csv")
	results.extend(data1_results)
	results.append(None)
	results.extend(data2_results)

	data1_i0 = get_result_value(data1_results, "data1", "I")
	data1_u_i = get_result_value(data1_results, "data1", "uI")
	data2_i = get_result_value(data2_results, "data2", "I")
	data2_u_i = get_result_value(data2_results, "data2", "uI")

	i_x = data2_i - data1_i0
	u_i_x = math.sqrt(data1_u_i ** 2 + data2_u_i ** 2)
	theory_i, theory_u = calc_theoretical_i_and_uncertainty(
		m2_kg=m2_kg,
		m2_u_kg=m2_u_kg,
		r_inner_m=r_inner_m,
		r_inner_u_m=r_inner_u_m,
		r_outer_m=r_outer_m,
		r_outer_u_m=r_outer_u_m,
	)

	results.append(None)
	results.extend([
		("", "Ix", i_x),
		("", "uIx", u_i_x),
		("", "I_theory", theory_i),
		("", "uI_theory", theory_u),
	])

	results.append(None)
	results.extend(process_data3(base / "data3.csv", disk_mass_kg))
	write_results(output_path, results)

	print(f"结果已写入: {output_path}")


if __name__ == "__main__":
	main()
