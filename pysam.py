#!/usr/bin/env python

import string, sys
from ctypes import *


class PySAM:
	def __init__(self):
		self.ssp = CDLL("C:\\SAM\\2011.12.2\\samsim.dll")
		
	INTEGER=1
	INTEGER_ARRAY=2
	DOUBLE=3
	DOUBLE_ARRAY=4
	STRING=5
	
	MODTYPE_SYSPERF=1
	MODTYPE_FINANCIAL=2
	
	OK=0
	ERR_INPUTS=-1
	ERR_OUTPUTS=-2
	ERR_WORKDIR=-3
	ERR_TRDFILE=-4
	ERR_ERR_TRDFILECR=-5
	ERR_ERR_PVWATTS=-6
	ERR_NOCONVERGE=-7
	ERR_OPTIMIZATION=-8
	ERR_NOTFOUND=-9
	ERR_BADTYPE=-10
	ERR_NOMODEL=-11
	ERR_TRNSYS=-12
	ERR_WEATHERFILE=-13
	ERR=-99
	
	
	def get_ver(self):
		major = c_long()
		minor = c_long()
		micro = c_long()		
		self.ssp.samsim_get_ver(byref(major), byref(minor), byref(micro))
		return [major.value, minor.value, micro.value]
	
	def get_model_count(self):
		return self.ssp.samsim_get_model_count()
		
	def get_model_name(self,idx):
		self.ssp.samsim_get_model_name.restype = c_char_p
		return self.ssp.samsim_get_model_name(c_int(idx))
	
	def create_context(self,name):
		return self.ssp.samsim_create_context(c_char_p(name))
	
	def free_context(self,cxt):
		return self.ssp.samsim_free_context(c_int(cxt))
	
	def switch_context(self,cxt,name):
		return self.ssp.samsim_switch_context(c_int(cxt),c_char_p(name))
		
	def get_model_type(self,cxt):
		return self.ssp.samsim_get_model_type(c_int(cxt))
	
	def get_input_count(self,cxt):
		return self.ssp.samsim_get_input_count(c_int(cxt))
	
	def get_output_count(self,cxt):
		return self.ssp.samsim_get_output_count(c_int(cxt))
	
	def get_input_name(self,cxt,idx):
		type = c_int()
		self.ssp.samsim_get_input.restype = c_char_p
		return self.ssp.samsim_get_input(c_int(cxt), c_int(idx), byref(type))
	
	def get_input_type(self,cxt,idx):
		type = c_int()
		self.ssp.samsim_get_input(c_int(cxt),c_int(idx),byref(type))
		return type.value
	
	def get_input_desc(self,cxt,idx):
		self.ssp.samsim_get_input_desc.restype = c_char_p
		return self.ssp.samsim_get_input_desc(c_int(cxt), c_int(idx))
	
	def get_output_name(self,cxt,idx):
		type = c_int()
		self.ssp.samsim_get_output.restype = c_char_p
		return self.ssp.samsim_get_output(c_int(cxt), c_int(idx), byref(type))
	
	def get_output_type(self,cxt,idx):
		type = c_int()
		self.ssp.samsim_get_output(c_int(cxt),c_int(idx),byref(type))
		return type.value
		
	def get_output_desc(self,cxt,idx):
		self.ssp.samsim_get_output_desc.restype = c_char_p
		return self.ssp.samsim_get_output_desc(c_int(cxt), c_int(idx))
		
	def set_i(self,cxt,name,value):
		return self.ssp.samsim_set_i( c_int(cxt), c_char_p(name), c_int(value))
	
	def set_ia(self,cxt,name,data,count):
		arr = (c_int*count)()
		for i in range(count):
			arr[i] = c_int(data[i])
		return self.ssp.samsim_set_ia( c_int(cxt), c_char_p(name), pointer(arr), c_int(count))
	
	def set_d(self,cxt,name,value):
		return self.ssp.samsim_set_d( c_int(cxt), c_char_p(name), c_double(value))
	
	def set_da(self,cxt,name,data,count):
		arr = (c_double*count)()
		for i in range(count):
			arr[i] = c_double(data[i])
		return self.ssp.samsim_set_da( c_int(cxt), c_char_p(name),pointer(arr), c_int(count))
	
	def set_s(self,cxt,name,value):
		return self.ssp.samsim_set_s( c_int(cxt), c_char_p(name), c_char_p(value))
		
	def get_i(self,cxt,name):
		val = c_int()
		self.ssp.samsim_get_i( c_int(cxt), c_char_p(name), byref(val) )
		return val.value
	
	def get_ia(self,cxt,name):
		count = self.ssp.samsim_get_ia_copy(c_int(cxt), c_char_p(name), None, c_int(0))
		arr = (c_int*count)()
		self.ssp.samsim_get_ia_copy(c_int(cxt), c_char_p(name), pointer(arr), c_int(count))
		return arr
	
	def get_d(self,cxt,name):
		val = c_double()
		self.ssp.samsim_get_d( c_int(cxt), c_char_p(name), byref(val) )
		return val.value
	
	def get_da(self,cxt,name):
		count = self.ssp.samsim_get_da_copy(c_int(cxt), c_char_p(name), None, c_int(0))
		arr = (c_double*count)()
		self.ssp.samsim_get_da_copy(c_int(cxt), c_char_p(name), pointer(arr), c_int(count))
		return arr
	
	def get_s(self,cxt,name):
		self.ssp.samsim_get_s.restype = c_char_p
		return self.ssp.samsim_get_s( c_int(cxt), c_char_p(name) )
	
	def precheck(self,cxt):
		return self.ssp.samsim_precheck( c_int(cxt) )
	
	def run(self,cxt):
		return self.ssp.samsim_run( c_int(cxt) )
	
	def message_count(self,cxt):
		return self.ssp.samsim_message_count( c_int(cxt) )
	
	def get_message(self,cxt,idx):
		self.ssp.samsim_get_message.restype = c_char_p
		return self.ssp.samsim_get_message( c_int(cxt), c_int(idx) )
		
	def symtab_read(self,cxt,file):
		return self.ssp.samsim_symtab_read( c_int(cxt), c_char_p(file), c_int(1))
		
	def load_library(self,cxt,file,prefix):
		return self.ssp.samsim_load_library( c_int(cxt), c_char_p(file), c_char_p(prefix) )
	
	def query_entries(self,cxt,type):
		return self.ssp.samsim_query_entries( c_int(cxt), c_char_p(type) )
	
	def get_entry(self,cxt,idx):
		self.ssp.samsim_get_entry.restype = c_char_p
		return self.ssp.samsim_get_entry( c_int(cxt), c_int(idx) )
	
	def apply_entry(self,cxt,name):
		return self.ssp.samsim_apply_entry( c_int(cxt), c_char_p(name) )
