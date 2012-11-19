import string, sys
import pysam
import numpy as np
import pdb

sam = pysam.PySAM()


#WORK_DIR = 'c:/admills/sam_python'
WORK_DIR = 'c:/users/admills/sam_python'

DERATE = 0.83 # DC-to-AC derate factor for PVWatts

def simulate_pv(tech, dc_cap, lat, weather_file):
	cxt = sam.create_context('dummy')
	get_inputs[tech](cxt, dc_cap)

	sam.set_s(cxt, 'sim.hourly_file', WORK_DIR + '/hourly.dat')
	sam.set_s(cxt, 'trnsys.workdir', WORK_DIR)
	sam.set_s(cxt, 'ptflux.workdir', WORK_DIR)
	sam.set_s(cxt, 'trnsys.installdir', 'C:/SAM/2011.12.2/exelib/trnsys')
	sam.set_d(cxt, 'trnsys.timestep', 1.0)
	sam.set_s(cxt, 'ptflux.exedir', 'C:/SAM/2011.12.2/exelib/tools')

	sam.set_s(cxt, 'climate.location', weather_file)
	sam.set_d(cxt, 'climate.latitude', float(lat))

	cxt = simulate_context( cxt, 'pvwatts' )
	cxt = simulate_context( cxt, 'fin.ipp' )
	#print 'Lcoe(real)=',sam.get_d(usf, 'sv.lcoe_real')
	#print 'Lcoe(nom)=',sam.get_d(usf, 'sv.lcoe_nom')
	print 'E_net=',sam.get_d(cxt, 'system.annual.e_net')
	hourly_power = extract_hourly_ac_power(WORK_DIR + '/hourly.dat')

	sam.free_context(cxt)
	return 	hourly_power 

def utility_fixed_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc
	"""

	cxt = define_capacity_param(cxt, dc_cap)
	sam.set_i(cxt, 'pvwatts.array_type', 0)
	sam.set_d(cxt, 'pvwatts.tilt', 30)
	sam.set_i(cxt, 'pvwatts.tilt_eq_lat', 0)
	sam.set_d(cxt, 'pvwatts.azimuth', 180)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)

def utility_sat_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc
	"""
	cxt = define_capacity_param(cxt, dc_cap)
	sam.set_i(cxt, 'pvwatts.array_type', 1)
	sam.set_d(cxt, 'pvwatts.tilt', 0)
	sam.set_i(cxt, 'pvwatts.tilt_eq_lat', 0)
	sam.set_d(cxt, 'pvwatts.azimuth', 180)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)

def residential_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc
	"""
	cxt = define_capacity_param(cxt, dc_cap)
	sam.set_i(cxt, 'pvwatts.array_type', 0)
	sam.set_d(cxt, 'pvwatts.tilt', 30)
	sam.set_i(cxt, 'pvwatts.tilt_eq_lat', 0)
	sam.set_d(cxt, 'pvwatts.azimuth', 180)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)


def commercial_inputs(cxt, dc_cap):
	"""
	Input dc_capacity in MWdc
	"""
	cxt = define_capacity_param(cxt, dc_cap)
	sam.set_i(cxt, 'pvwatts.array_type', 0)
	sam.set_d(cxt, 'pvwatts.tilt', 0)
	sam.set_i(cxt, 'pvwatts.tilt_eq_lat', 0)
	sam.set_d(cxt, 'pvwatts.azimuth', 180)
	
	cxt = define_site_param(cxt)
	cxt = define_generic_param(cxt)


get_inputs = { "utility_scale_fixed": utility_fixed_inputs,
	      "utility_scale_sat": utility_sat_inputs,
	      "residential": residential_inputs,
	      "commercial": commercial_inputs}

def define_site_param( cxt):
	sam.set_s(cxt, 'climate.location', 'C:/SAM/2011.12.2/exelib/climate_files/AZ Phoenix.tm2')
	sam.set_d(cxt, 'climate.latitude', 33.4333)
	
	return cxt

def define_capacity_param(cxt, dc_cap):

	dc_cap = float(dc_cap) * 1000. #kWdc
	sam.set_d(cxt, 'pvwatts.dcrate', dc_cap)

	return cxt

def define_generic_param(cxt):
	sam.set_d(cxt, 'pvwatts.derate', DERATE)
	sam.set_i(cxt, 'pvwatts.array_type', 0)
	sam.set_d(cxt, 'pvwatts.tilt', 0)
	sam.set_i(cxt, 'pvwatts.tilt_eq_lat', 0)
	sam.set_d(cxt, 'pvwatts.azimuth', 180)
	sam.set_i(cxt, 'pv.shading.mxh.enabled', 0)

	# Inputs for SAMSIM model "pvwatts"
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
	
	# Inputs for SAMSIM model "fin.ipp"
	sam.set_d(cxt, 'system.recapitalization_cost', 0)
	sam.set_d(cxt, 'system.recapitalization_escalation', 0)
	da = [1]
	sam.set_da(cxt, 'system.degradation', da, 1)
	da = [100]
	sam.set_da(cxt, 'system.availability', da, 1)
	sam.set_d(cxt, 'system.nameplate_capacity', 20000)
	sam.set_d(cxt, 'system.direct_cost', 8e+007)
	sam.set_d(cxt, 'system.installed_cost', 8.16e+007)
	sam.set_d(cxt, 'system.construction_financing_cost', 0)
	sam.set_d(cxt, 'system.installed_cost_per_capacity', 4080)
	sam.set_d(cxt, 'system.direct_sales_tax', 0)
	sam.set_d(cxt, 'system.summary.land_area', 0)
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
	sam.set_i(cxt, 'fin.utilityipp.mode', 0)
	sam.set_d(cxt, 'fin.utilityipp.debt_fraction', 56)
	sam.set_d(cxt, 'fin.utilityipp.loan_amount', 4.5696e+007)
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
	sam.set_s(cxt, 'system.tod.sched.weekday', '111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111')
	sam.set_s(cxt, 'system.tod.sched.weekend', '111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111')
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
	# Drop header rows (one)
	junk = reader.next()

	# extract ac_power data from hourly output file in column [9]
	hourly = []
	for row in reader:
		row = row.split(',') 
		hourly += [float(row[9])]
	# return the time-series of hourly generation data in MW
	return np.array(hourly)/1000.
