import string, sys
import pysam
import numpy as np
import os

sam = pysam.PySAM()

#### THIS NEEDS TO BE REPLACED WITH LOCATION OF YOUR VERSION OF SAM
SAM_DIR = 'C:/SAM/2011.12.2/'

#### THIS NEEDS TO BE REPLACED WITH THE LOCATION OF SAM OUTPUT FILES 
WORK_DIR = 'c:/users/admills/sam_python'

def simulate_pv(tech, dc_cap, lat, weather_file):
	cxt = sam.create_context('dummy')
	get_inputs[tech](cxt, dc_cap)

	sam.set_s(cxt, 'sim.hourly_file', WORK_DIR + '/hourly.dat')
	sam.set_s(cxt, 'trnsys.workdir', WORK_DIR)
	sam.set_s(cxt, 'ptflux.workdir', WORK_DIR)
	sam.set_s(cxt, 'trnsys.installdir', SAM_DIR + 'exelib/trnsys')
	sam.set_d(cxt, 'trnsys.timestep', 1.0)
	sam.set_s(cxt, 'ptflux.exedir', SAM_DIR + 'exelib/tools')

	sam.set_s(cxt, 'climate.location', weather_file)
	sam.set_d(cxt, 'climate.latitude', float(lat))

	cxt = simulate_context( cxt, 'trnsys.pv' )
	cxt = simulate_context( cxt, 'fin.ipp' )
	print 'E_net=',sam.get_d(cxt, 'system.annual.e_net')
	hourly_power = extract_hourly_ac_power(WORK_DIR + '/hourly.dat')

	sam.free_context(cxt)

	return 	hourly_power 

def utility_fixed_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc

	Try to keep divisible by 0.5 MW
	"""
	string_ratio = 50000/2500 
	inverter_cap = 460000 # Wac per inverter
	inverter_ratio = 46/50.
	sam.set_i(cxt, 'pv.array.modules_per_string', 200)

	cxt = define_ratio_param(cxt, dc_cap, string_ratio, inverter_cap, 
				 inverter_ratio)

	sam.set_i(cxt, 'pv.array.tracking_type', 0)
	sam.set_d(cxt, 'pv.array.azimuth', 0)
	sam.set_d(cxt, 'pv.array.tilt', 30)

	sam.set_d(cxt, 'pv.mod.spe.a', -3.47)
	sam.set_d(cxt, 'pv.mod.spe.b', -0.0594)
	sam.set_d(cxt, 'pv.mod.spe.dT', 3)
	sam.set_i(cxt, 'pv.mod.spe.module_structure', 4)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)

def utility_sat_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc

	Try to keep divisible by 0.5 MW
	"""

	string_ratio = 50000/2500 
	inverter_cap = 460000 # Wac per inverter
	inverter_ratio = 46/50.
	sam.set_i(cxt, 'pv.array.modules_per_string', 200)

	cxt = define_ratio_param(cxt, dc_cap, string_ratio, inverter_cap, 
				 inverter_ratio)

	sam.set_i(cxt, 'pv.array.tracking_type', 1)
	sam.set_d(cxt, 'pv.array.azimuth', 0)
	sam.set_d(cxt, 'pv.array.tilt', 0)

	sam.set_d(cxt, 'pv.mod.spe.a', -3.47)
	sam.set_d(cxt, 'pv.mod.spe.b', -0.0594)
	sam.set_d(cxt, 'pv.mod.spe.dT', 3)
	sam.set_i(cxt, 'pv.mod.spe.module_structure', 1)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)

def residential_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc

	Try to keep divisible by 0.004 MW
	"""

	string_ratio = 4/4 
	inverter_cap = 3650 # Wac per inverter
	inverter_ratio = 3650/4000.
	sam.set_i(cxt, 'pv.array.modules_per_string', 10)

	cxt = define_ratio_param(cxt, dc_cap, string_ratio, inverter_cap, 
				 inverter_ratio)

	sam.set_i(cxt, 'pv.array.tracking_type', 0)
	sam.set_d(cxt, 'pv.array.azimuth', 0)
	sam.set_d(cxt, 'pv.array.tilt', 30)

	sam.set_d(cxt, 'pv.mod.spe.a', -2.98)
	sam.set_d(cxt, 'pv.mod.spe.b', -0.0471)
	sam.set_d(cxt, 'pv.mod.spe.dT', 1)
	sam.set_i(cxt, 'pv.mod.spe.module_structure', 4)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)

def commercial_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc

	Try to keep divisible by 0.2 MW
	"""

	string_ratio = 200/200 
	inverter_cap = 184000 # Wac per inverter
	inverter_ratio = 184/200.
	sam.set_i(cxt, 'pv.array.modules_per_string', 10)

	cxt = define_ratio_param(cxt, dc_cap, string_ratio, inverter_cap, 
				 inverter_ratio)

	sam.set_i(cxt, 'pv.array.tracking_type', 0)
	sam.set_d(cxt, 'pv.array.azimuth', 0)
	sam.set_d(cxt, 'pv.array.tilt', 0)

	sam.set_d(cxt, 'pv.mod.spe.a', -2.98)
	sam.set_d(cxt, 'pv.mod.spe.b', -0.0471)
	sam.set_d(cxt, 'pv.mod.spe.dT', 1)
	sam.set_i(cxt, 'pv.mod.spe.module_structure', 4)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)

get_inputs = { "utility_scale_fixed": utility_fixed_inputs,
	      "utility_scale_sat": utility_sat_inputs,
	      "residential": residential_inputs,
	      "commercial": commercial_inputs}

def define_site_param( cxt):
	sam.set_s(cxt, 'climate.location', SAM_DIR+ 'exelib/climate_files/AZ Phoenix.tm2')
	sam.set_d(cxt, 'climate.latitude', 33.4333)
	
	return cxt

def define_ratio_param(cxt, dc_cap, string_ratio, inverter_cap, inverter_ratio):

	dc_cap = float(dc_cap) * 1000.
	num_string = int(dc_cap/string_ratio)
	inverter_count = int(inverter_ratio * dc_cap * 1000/inverter_cap)
	sam.set_d(cxt, 'system.nameplate_capacity', float(dc_cap)) # kWdc
	sam.set_d(cxt, 'pv.array.total_power', float(dc_cap)) # kWdc
	sam.set_d(cxt, 'pv.inv.spe.power_ac', float(inverter_cap)) # Wac per inverter
	sam.set_i(cxt, 'pv.array.strings_in_parallel', int(num_string))
	sam.set_i(cxt, 'pv.array.inverter_count', int(inverter_count))

	return cxt

def define_generic_param(cxt):
	# Inputs for SAMSIM model "trnsys.pv"

	sam.set_d(cxt, 'pv.mod.spe.temp_coeff', -0.5)
	sam.set_i(cxt, 'pv.mod.spe.reference', 4)

	sam.set_i(cxt, 'pv.array.tilt_eq_lat', 0)
	
	sam.set_i(cxt, 'pv.inv.model_type', 0)
	sam.set_d(cxt, 'pv.inv.spe.efficiency', 92)

	sam.set_d(cxt, 'pv.array.ground_reflectance', 0.2)
	sam.set_i(cxt, 'pv.array.radiation_type', 1)
	sam.set_i(cxt, 'pv.array.tilt_radiation_model_type', 2)
	sam.set_d(cxt, 'pv.array.pre_derate', 100)
	sam.set_d(cxt, 'pv.array.post_derate', 84)
	sam.set_d(cxt, 'pv.mod.cec.a_c', 0.67)
	sam.set_d(cxt, 'pv.mod.cec.a_ref', 0.473)
	sam.set_d(cxt, 'pv.mod.cec.adjust', 10.6)
	sam.set_d(cxt, 'pv.mod.cec.alpha_sc', 0.003)
	sam.set_d(cxt, 'pv.mod.cec.beta_oc', -0.04)
	sam.set_d(cxt, 'pv.mod.cec.gamma_r', -0.5)
	sam.set_d(cxt, 'pv.mod.cec.i_l_ref', 7.545)
	sam.set_d(cxt, 'pv.mod.cec.i_mp_ref', 6.6)
	sam.set_d(cxt, 'pv.mod.cec.i_o_ref', 1.943e-009)
	sam.set_d(cxt, 'pv.mod.cec.i_sc_ref', 7.5)
	sam.set_d(cxt, 'pv.mod.cec.n_s', 18)
	sam.set_d(cxt, 'pv.mod.cec.r_s', 0.094)
	sam.set_d(cxt, 'pv.mod.cec.r_sh_ref', 15.72)
	sam.set_d(cxt, 'pv.mod.cec.t_noct', 65)
	sam.set_d(cxt, 'pv.mod.cec.v_mp_ref', 8.4)
	sam.set_d(cxt, 'pv.mod.cec.v_oc_ref', 10.4)
	sam.set_i(cxt, 'pv.mod.cec.temp_corr_mode', 0)
	sam.set_i(cxt, 'pv.mod.cec.mounting_config', 0)
	sam.set_i(cxt, 'pv.mod.cec.heat_transfer', 0)
	sam.set_i(cxt, 'pv.mod.cec.mounting_orientation', 0)
	sam.set_d(cxt, 'pv.mod.cec.gap_spacing', 0.05)
	sam.set_d(cxt, 'pv.mod.cec.module_width', 1)
	sam.set_d(cxt, 'pv.mod.cec.module_length', 0.67)
	sam.set_d(cxt, 'pv.mod.cec.array_rows', 1)
	sam.set_d(cxt, 'pv.mod.cec.array_cols', 10)
	sam.set_d(cxt, 'pv.mod.cec.backside_temp', 20)
	sam.set_d(cxt, 'pv.mod.sandia.a', -3.47)
	sam.set_d(cxt, 'pv.mod.sandia.a0', 0.936)
	sam.set_d(cxt, 'pv.mod.sandia.a1', 0.053645)
	sam.set_d(cxt, 'pv.mod.sandia.a2', -0.0079402)
	sam.set_d(cxt, 'pv.mod.sandia.a3', 0.00052228)
	sam.set_d(cxt, 'pv.mod.sandia.a4', -1.3142e-005)
	sam.set_d(cxt, 'pv.mod.sandia.aimp', 0.00036)
	sam.set_d(cxt, 'pv.mod.sandia.aisc', 0.00092)
	sam.set_d(cxt, 'pv.mod.sandia.area', 2.427)
	sam.set_d(cxt, 'pv.mod.sandia.b', -0.0594)
	sam.set_d(cxt, 'pv.mod.sandia.b0', 1)
	sam.set_d(cxt, 'pv.mod.sandia.b1', -0.002438)
	sam.set_d(cxt, 'pv.mod.sandia.b2', 0.0003103)
	sam.set_d(cxt, 'pv.mod.sandia.b3', -1.246e-005)
	sam.set_d(cxt, 'pv.mod.sandia.b4', 2.112e-007)
	sam.set_d(cxt, 'pv.mod.sandia.b5', -1.359e-009)
	sam.set_d(cxt, 'pv.mod.sandia.bvmpo', -0.238)
	sam.set_d(cxt, 'pv.mod.sandia.bvoco', -0.227)
	sam.set_d(cxt, 'pv.mod.sandia.c0', 0.994)
	sam.set_d(cxt, 'pv.mod.sandia.c1', 0.006)
	sam.set_d(cxt, 'pv.mod.sandia.c2', 0.006258)
	sam.set_d(cxt, 'pv.mod.sandia.c3', -7.69008)
	sam.set_d(cxt, 'pv.mod.sandia.c4', 0.9843)
	sam.set_d(cxt, 'pv.mod.sandia.c5', 0.0157)
	sam.set_d(cxt, 'pv.mod.sandia.c6', 1.127)
	sam.set_d(cxt, 'pv.mod.sandia.c7', -0.127)
	sam.set_d(cxt, 'pv.mod.sandia.dtc', 3)
	sam.set_d(cxt, 'pv.mod.sandia.fd', 1)
	sam.set_d(cxt, 'pv.mod.sandia.impo', 5.3)
	sam.set_d(cxt, 'pv.mod.sandia.isco', 5.8)
	sam.set_d(cxt, 'pv.mod.sandia.ixo', 5.7)
	sam.set_d(cxt, 'pv.mod.sandia.ixxo', 3.8)
	sam.set_d(cxt, 'pv.mod.sandia.mbvmp', 0)
	sam.set_d(cxt, 'pv.mod.sandia.mbvoc', 0)
	sam.set_d(cxt, 'pv.mod.sandia.n', 1.288)
	sam.set_i(cxt, 'pv.mod.sandia.parallel_cells', 2)
	sam.set_i(cxt, 'pv.mod.sandia.series_cells', 108)
	sam.set_d(cxt, 'pv.mod.sandia.vmpo', 50)
	sam.set_d(cxt, 'pv.mod.sandia.voco', 62)
	sam.set_i(cxt, 'pv.mod.sandia.module_structure', 0)
	sam.set_d(cxt, 'pv.mod.sandia.ref_a', -3.47)
	sam.set_d(cxt, 'pv.mod.sandia.ref_b', -0.0594)
	sam.set_d(cxt, 'pv.mod.sandia.ref_dT', 3)
	sam.set_d(cxt, 'pv.mod.cpv.area', 200)
	sam.set_i(cxt, 'pv.mod.cpv.reference', 3)
	sam.set_d(cxt, 'pv.mod.cpv.rad0', 200)
	sam.set_d(cxt, 'pv.mod.cpv.rad1', 400)
	sam.set_d(cxt, 'pv.mod.cpv.rad2', 600)
	sam.set_d(cxt, 'pv.mod.cpv.rad3', 850)
	sam.set_d(cxt, 'pv.mod.cpv.rad4', 1000)
	sam.set_d(cxt, 'pv.mod.cpv.eff0', 20)
	sam.set_d(cxt, 'pv.mod.cpv.eff1', 20)
	sam.set_d(cxt, 'pv.mod.cpv.eff2', 20)
	sam.set_d(cxt, 'pv.mod.cpv.eff3', 20)
	sam.set_d(cxt, 'pv.mod.cpv.eff4', 20)
	sam.set_d(cxt, 'pv.mod.cpv.a', -3.2)
	sam.set_d(cxt, 'pv.mod.cpv.b', -0.09)
	sam.set_d(cxt, 'pv.mod.cpv.dT', 17)
	sam.set_d(cxt, 'pv.mod.cpv.temp_coeff', -0.15)
	sam.set_i(cxt, 'pv.mod.6par.type', 1)
	sam.set_d(cxt, 'pv.mod.6par.vmp', 30)
	sam.set_d(cxt, 'pv.mod.6par.imp', 6)
	sam.set_d(cxt, 'pv.mod.6par.voc', 37)
	sam.set_d(cxt, 'pv.mod.6par.isc', 7)
	sam.set_d(cxt, 'pv.mod.6par.bvoc', -0.11)
	sam.set_d(cxt, 'pv.mod.6par.aisc', 0.004)
	sam.set_d(cxt, 'pv.mod.6par.gpmp', -0.41)
	sam.set_i(cxt, 'pv.mod.6par.nser', 60)
	sam.set_d(cxt, 'pv.mod.6par.area', 1.3)
	sam.set_d(cxt, 'pv.mod.6par.tnoct', 46)
	sam.set_i(cxt, 'pv.mod.6par.standoff', 6)
	sam.set_i(cxt, 'pv.mod.6par.mounting', 0)
	sam.set_d(cxt, 'pv.inv.sandia.c0', -5.76809e-008)
	sam.set_d(cxt, 'pv.inv.sandia.c1', 7.19223e-005)
	sam.set_d(cxt, 'pv.inv.sandia.c2', 0.0020754)
	sam.set_d(cxt, 'pv.inv.sandia.c3', 5.95611e-005)
	sam.set_d(cxt, 'pv.inv.sandia.paco', 333000)
	sam.set_d(cxt, 'pv.inv.sandia.pdco', 343251)
	sam.set_d(cxt, 'pv.inv.sandia.pnt', 89.58)
	sam.set_d(cxt, 'pv.inv.sandia.pso', 1427.75)
	sam.set_d(cxt, 'pv.inv.sandia.vdco', 370.088)
	sam.set_d(cxt, 'pv.inv.sandia.vdcmax', 600)

	sam.set_d(cxt, 'sysudv.1', 0)
	sam.set_d(cxt, 'sysudv.2', 0)
	sam.set_d(cxt, 'sysudv.3', 0)
	sam.set_d(cxt, 'sysudv.4', 0)
	sam.set_d(cxt, 'sysudv.5', 0)
	sam.set_d(cxt, 'sysudv.6', 0)
	sam.set_d(cxt, 'sysudv.7', 0)
	sam.set_d(cxt, 'sysudv.8', 0)
	sam.set_d(cxt, 'sysudv.9', 0)
	sam.set_d(cxt, 'sysudv.10', 0)

	da = [100 for x in range(12)]
	sam.set_da(cxt, 'pv.array.monthly_soiling', da, 12)

	sam.set_d(cxt, 'pv.array.rot1', 360)
	sam.set_d(cxt, 'pv.array.rot2', -360)
	sam.set_d(cxt, 'pv.array.rot3', 360)
	sam.set_d(cxt, 'pv.array.rot4', -360)
	sam.set_d(cxt, 'pv.array.prederate.diodes', 100)
	sam.set_d(cxt, 'pv.array.prederate.nameplate', 100)
	sam.set_i(cxt, 'pv.mod.model_type', 0)
	sam.set_d(cxt, 'pv.mod.spe.area', 0.74074)
	sam.set_d(cxt, 'pv.mod.spe.rad0', 200)
	sam.set_d(cxt, 'pv.mod.spe.rad1', 400)
	sam.set_d(cxt, 'pv.mod.spe.rad2', 600)
	sam.set_d(cxt, 'pv.mod.spe.rad3', 800)
	sam.set_d(cxt, 'pv.mod.spe.rad4', 1000)
	sam.set_d(cxt, 'pv.mod.spe.eff0', 13.5)
	sam.set_d(cxt, 'pv.mod.spe.eff1', 13.5)
	sam.set_d(cxt, 'pv.mod.spe.eff2', 13.5)
	sam.set_d(cxt, 'pv.mod.spe.eff3', 13.5)
	sam.set_d(cxt, 'pv.mod.spe.eff4', 13.5)


	sam.set_i(cxt, 'pv.shading.mxh.enabled', 0)
	da = [12, 24] + [1 for x in range(288)]
	sam.set_da(cxt, 'pv.shading.mxh.factors', da, 290)
	sam.set_i(cxt, 'pv.shading.beam.hourly.enabled', 0)
	da = [1 for x in range(8760)]
	sam.set_da(cxt, 'pv.shading.beam.hourly.factors', da, 8760)
	sam.set_i(cxt, 'pv.shading.diffuse.enabled', 0)
	sam.set_d(cxt, 'pv.shading.diffuse.factor', 0)
	sam.set_i(cxt, 'pv.shading.azalt.enabled', 0)
	da = [11, 20, 0, -180, -160, -140, -120, -100, -80, -60, -40, -20, 0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 90, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 80, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 70, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 60, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 50, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 40, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 30, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 20, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
	sam.set_da(cxt, 'pv.shading.azalt.table', da, 222)
	sam.set_i(cxt, 'pv.shading.utility.enabled', 0)
	sam.set_d(cxt, 'pv.shading.utility.length', 0)
	sam.set_d(cxt, 'pv.shading.utility.width', 1)
	sam.set_i(cxt, 'pv.shading.utility.mod_orient', 0)
	sam.set_i(cxt, 'pv.shading.utility.str_orient', 1)
	sam.set_i(cxt, 'pv.shading.utility.ncellx', 4)
	sam.set_i(cxt, 'pv.shading.utility.ncelly', 0)
	sam.set_i(cxt, 'pv.shading.utility.ndiode', 2)
	sam.set_i(cxt, 'pv.shading.utility.nmodx', 1)
	sam.set_i(cxt, 'pv.shading.utility.nmody', 3)
	sam.set_i(cxt, 'pv.shading.utility.nrows', 5)
	sam.set_d(cxt, 'pv.shading.utility.rowspace', 5)
	sam.set_d(cxt, 'pv.shading.utility.slopens', 0)
	sam.set_d(cxt, 'pv.shading.utility.slopeew', 0)

	# Inputs for SAMSIM model "fin.ipp"

	sam.set_i(cxt, 'fin.analysis_period', 30)
	sam.set_d(cxt, 'fin.federal_tax', 35)
	sam.set_d(cxt, 'fin.inflation_rate', 2.5)
	sam.set_d(cxt, 'fin.insurance', 1)
	sam.set_d(cxt, 'fin.property_assessed_percent', 100)
	sam.set_d(cxt, 'fin.property_assessed_decline', 0)
	sam.set_d(cxt, 'fin.property_tax', 2)
	sam.set_d(cxt, 'fin.real_discount_rate', 7.5)
	sam.set_d(cxt, 'fin.sales_tax', 0)
	sam.set_d(cxt, 'fin.state_tax', 8)
	sam.set_d(cxt, 'fin.salvage_percent', 0)

	da = [1]
	sam.set_da(cxt, 'system.degradation', da, 1)
	da = [100]
	sam.set_da(cxt, 'system.availability', da, 1)
	sam.set_d(cxt, 'system.direct_cost', 1.66597e+009)
	sam.set_d(cxt, 'system.installed_cost', 1.69929e+009)
	sam.set_d(cxt, 'system.construction_financing_cost', 0)
	sam.set_d(cxt, 'system.installed_cost_per_capacity', 1.69929e+006)
	sam.set_d(cxt, 'system.direct_sales_tax', 0)
	sam.set_d(cxt, 'system.summary.land_area', 0)


	sam.set_d(cxt, 'system.recapitalization_cost', 0)
	sam.set_d(cxt, 'system.recapitalization_escalation', 0)

	da = [0]
	sam.set_da(cxt, 'oandm.fixed_annual', da, 1)
	sam.set_d(cxt, 'oandm.fixed_annual.escalation', 0)
	da = [0]
	sam.set_da(cxt, 'oandm.per_mwh_variable', da, 1)
	sam.set_d(cxt, 'oandm.per_mwh_variable.escalation', 0)
	da = [59.6]
	sam.set_da(cxt, 'oandm.per_kw_fixed', da, 1)
	sam.set_d(cxt, 'oandm.per_kw_fixed.escalation', 0)
	da = [0]
	sam.set_da(cxt, 'oandm.fuel_cost', da, 1)
	sam.set_d(cxt, 'oandm.fuel_cost.escalation', 0)
	sam.set_i(cxt, 'fin.utilityipp.mode', 0)
	sam.set_d(cxt, 'fin.utilityipp.debt_fraction', 56)
	sam.set_d(cxt, 'fin.utilityipp.loan_amount', 9.51603e+008)
	sam.set_d(cxt, 'fin.utilityipp.loan_rate', 6)
	sam.set_i(cxt, 'fin.utilityipp.loan_term', 20)
	sam.set_d(cxt, 'fin.utilityipp.min_dscr', 1.2)
	sam.set_d(cxt, 'fin.utilityipp.min_irr', 12)
	sam.set_d(cxt, 'fin.utilityipp.ppa_escalation', 0)
	sam.set_i(cxt, 'fin.utilityipp.require_min_dscr', 1)
	sam.set_i(cxt, 'fin.utilityipp.require_positive_cashflow', 1)
	sam.set_i(cxt, 'fin.utilityipp.optimize_lcoe_wrt_debt_fraction', 0)
	sam.set_i(cxt, 'fin.utilityipp.optimize_lcoe_wrt_ppa_escalation', 0)
	sam.set_d(cxt, 'fin.utilityipp.construction_financing_cost', 0)
	sam.set_d(cxt, 'fin.utilityipp.bid_price', 0.15)
	sam.set_d(cxt, 'fin.utilityipp.bid_price_esc', 0)
	sam.set_d(cxt, 'epd.disp1.todf', 1)
	sam.set_d(cxt, 'epd.disp2.todf', 1)
	sam.set_d(cxt, 'epd.disp3.todf', 1)
	sam.set_d(cxt, 'epd.disp4.todf', 1)
	sam.set_d(cxt, 'epd.disp5.todf', 1)
	sam.set_d(cxt, 'epd.disp6.todf', 1)
	sam.set_d(cxt, 'epd.disp7.todf', 1)
	sam.set_d(cxt, 'epd.disp8.todf', 1)
	sam.set_d(cxt, 'epd.disp9.todf', 1)
	sam.set_s(cxt, 'system.tod.sched.weekday', '1'*288)
	sam.set_s(cxt, 'system.tod.sched.weekend', '1'*288)
	sam.set_i(cxt, 'txc.itc.fed.amount.deprbasis.fed.enabled', 1)
	sam.set_i(cxt, 'txc.itc.fed.amount.deprbasis.state.enabled', 1)
	sam.set_d(cxt, 'txc.itc.fed.amount.value', 0)
	sam.set_i(cxt, 'txc.itc.fed.percentage.deprbasis.fed.enabled', 1)
	sam.set_i(cxt, 'txc.itc.fed.percentage.deprbasis.state.enabled', 1)
	sam.set_d(cxt, 'txc.itc.fed.percentage.maximum', 1e+099)
	sam.set_d(cxt, 'txc.itc.fed.percentage.value', 30)
	sam.set_i(cxt, 'txc.itc.state.amount.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'txc.itc.state.amount.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'txc.itc.state.amount.value', 0)
	sam.set_i(cxt, 'txc.itc.state.percentage.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'txc.itc.state.percentage.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'txc.itc.state.percentage.maximum', 1e+099)
	sam.set_d(cxt, 'txc.itc.state.percentage.value', 0)
	da = [0]
	sam.set_da(cxt, 'txc.ptc.fed.amountperkwh', da, 1)
	sam.set_d(cxt, 'txc.ptc.fed.escalation', 2)
	sam.set_d(cxt, 'txc.ptc.fed.term', 10)
	da = [0]
	sam.set_da(cxt, 'txc.ptc.state.amountperkwh', da, 1)
	sam.set_d(cxt, 'txc.ptc.state.escalation', 2)
	sam.set_d(cxt, 'txc.ptc.state.term', 10)
	sam.set_i(cxt, 'incen.cbi.fed.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.cbi.fed.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.cbi.fed.maximum', 1e+099)
	sam.set_i(cxt, 'incen.cbi.fed.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.cbi.fed.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.cbi.fed.value', 0)
	sam.set_i(cxt, 'incen.cbi.other.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.cbi.other.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.cbi.other.maximum', 1e+099)
	sam.set_i(cxt, 'incen.cbi.other.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.cbi.other.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.cbi.other.value', 0)
	sam.set_i(cxt, 'incen.cbi.state.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.cbi.state.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.cbi.state.maximum', 1e+099)
	sam.set_i(cxt, 'incen.cbi.state.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.cbi.state.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.cbi.state.value', 0)
	sam.set_i(cxt, 'incen.cbi.utility.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.cbi.utility.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.cbi.utility.maximum', 1e+099)
	sam.set_i(cxt, 'incen.cbi.utility.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.cbi.utility.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.cbi.utility.value', 0)
	sam.set_i(cxt, 'incen.ibi.fed.amount.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.fed.amount.deprbasis.state.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.fed.amount.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.fed.amount.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.fed.amount.value', 0)
	sam.set_i(cxt, 'incen.ibi.fed.percentage.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.fed.percentage.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.ibi.fed.percentage.maximum', 1e+099)
	sam.set_i(cxt, 'incen.ibi.fed.percentage.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.fed.percentage.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.fed.percentage.value', 0)
	sam.set_i(cxt, 'incen.ibi.other.amount.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.other.amount.deprbasis.state.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.other.amount.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.other.amount.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.other.amount.value', 0)
	sam.set_i(cxt, 'incen.ibi.other.percentage.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.other.percentage.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.ibi.other.percentage.maximum', 1e+099)
	sam.set_i(cxt, 'incen.ibi.other.percentage.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.other.percentage.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.other.percentage.value', 0)
	sam.set_i(cxt, 'incen.ibi.state.amount.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.state.amount.deprbasis.state.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.state.amount.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.state.amount.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.state.amount.value', 0)
	sam.set_i(cxt, 'incen.ibi.state.percentage.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.state.percentage.deprbasis.state.enabled', 0)
	sam.set_d(cxt, 'incen.ibi.state.percentage.maximum', 1e+099)
	sam.set_i(cxt, 'incen.ibi.state.percentage.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.state.percentage.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.state.percentage.value', 0)
	sam.set_i(cxt, 'incen.ibi.utility.amount.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.utility.amount.deprbasis.state.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.utility.amount.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.utility.amount.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.utility.amount.value', 0)
	sam.set_d(cxt, 'incen.ibi.utility.percentage.maximum', 1e+099)
	sam.set_i(cxt, 'incen.ibi.utility.percentage.deprbasis.fed.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.utility.percentage.deprbasis.state.enabled', 0)
	sam.set_i(cxt, 'incen.ibi.utility.percentage.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.ibi.utility.percentage.taxable.state.enabled', 1)
	sam.set_d(cxt, 'incen.ibi.utility.percentage.value', 0)
	da = [0]
	sam.set_da(cxt, 'incen.pbi.fed.amountperkwh', da, 1)
	sam.set_d(cxt, 'incen.pbi.fed.escalation', 2)
	sam.set_d(cxt, 'incen.pbi.fed.term', 10)
	da = [0]
	sam.set_da(cxt, 'incen.pbi.other.amountperkwh', da, 1)
	sam.set_d(cxt, 'incen.pbi.other.escalation', 0)
	sam.set_d(cxt, 'incen.pbi.other.term', 0)
	da = [0]
	sam.set_da(cxt, 'incen.pbi.state.amountperkwh', da, 1)
	sam.set_d(cxt, 'incen.pbi.state.escalation', 0)
	sam.set_d(cxt, 'incen.pbi.state.term', 0)
	da = [0]
	sam.set_da(cxt, 'incen.pbi.utility.amountperkwh', da, 1)
	sam.set_d(cxt, 'incen.pbi.utility.escalation', 0)
	sam.set_d(cxt, 'incen.pbi.utility.term', 0)
	sam.set_i(cxt, 'incen.pbi.fed.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.fed.taxable.state.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.state.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.state.taxable.state.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.utility.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.utility.taxable.state.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.other.taxable.fed.enabled', 1)
	sam.set_i(cxt, 'incen.pbi.other.taxable.state.enabled', 1)
	sam.set_i(cxt, 'depreciation.fed.type', 1)
	sam.set_i(cxt, 'depreciation.fed.years', 7)
	da = [0.0 ]
	sam.set_da(cxt, 'depreciation.fed.custom', da, 0)
	sam.set_i(cxt, 'depreciation.state.type', 0)
	sam.set_i(cxt, 'depreciation.state.years', 7)
	da = [0.0 ]
	sam.set_da(cxt, 'depreciation.state.custom', da, 0)

	return cxt

	

def simulate_context(cxt, model_name):
	cxt = sam.switch_context(cxt, model_name)
	if (sam.precheck(cxt) != sam.OK):
		print 'Precheck error:'
		nmsg = sam.message_count(cxt)
		for i in range(nmsg):
			print sam.get_message(cxt, i)
		return 0
	if (sam.run(cxt) != sam.OK):
		print 'Run error:'
		nmsg = sam.message_count(cxt)
		for i in range(nmsg):
			print sam.get_message(cxt, i)
		return 0
	return cxt

def extract_hourly_ac_power(file_name):

	# Open hourly data
	reader = open(file_name)
	# Drop header rows (two)
	junk = reader.next()
	junk = reader.next()

	# extract ac_power data from hourly output file in column [10]
	hourly = []
	for row in reader:
		row = row.split('\t') 
		hourly += [float(row[10])]

	#### Delete the file so that it doesn't get used if the next SAM call 
	#### fails
	os.remove(file_name)

	# return the time-series of hourly generation data in MW
	return np.array(hourly)/1000.
