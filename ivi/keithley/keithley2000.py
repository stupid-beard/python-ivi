"""

Python Interchangeable Virtual Instrument Library

Copyright (c) 2012-2014 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import time
import struct

from .. import ivi
from .. import dmm
from .. import scpi

MeasurementFunctionMapping = {
        'dc_volts': 'volt:dc',
        'ac_volts': 'volt:ac',
        'dc_current': 'curr:dc',
        'ac_current': 'curr:ac',
        'two_wire_resistance': 'res',
        'four_wire_resistance': 'fres',
        'frequency': 'freq',
        'period': 'per',
        'continuity': 'cont',
        'diode': 'diod'}

MeasurementRangeMapping = {
        'dc_volts': 'volt:dc:range',
        'ac_volts': 'volt:ac:range',
        'dc_current': 'curr:dc:range',
        'ac_current': 'curr:ac:range',
        'two_wire_resistance': 'res:range',
        'four_wire_resistance': 'fres:range'}

MeasurementAutoRangeMapping = {
        'dc_volts': 'volt:dc:range:auto',
        'ac_volts': 'volt:ac:range:auto',
        'dc_current': 'curr:dc:range:auto',
        'ac_current': 'curr:ac:range:auto',
        'two_wire_resistance': 'res:range:auto',
        'four_wire_resistance': 'fres:range:auto'}

MeasurementResolutionMapping = {
        'dc_volts': 'volt:dc:digits',
        'ac_volts': 'volt:ac:digits',
        'dc_current': 'curr:dc:digits',
        'ac_current': 'curr:ac:digits',
        'two_wire_resistance': 'res:digits',
        'four_wire_resistance': 'fres:digits'}

class keithley2000(scpi.dmm.Base, scpi.dmm.MultiPoint, scpi.dmm.SoftwareTrigger):
    "Keithley 2000 IVI DMM driver"
    
    def __init__(self, *args, **kwargs):
        self.__dict__.setdefault('_instrument_id', '2000')
        
        super(keithley2000, self).__init__(*args, **kwargs)
        
        self._memory_size = 5
        
        self._identity_description = "Keithley 2000 IVI DMM driver"
        self._identity_identifier = ""
        self._identity_revision = ""
        self._identity_vendor = ""
        self._identity_instrument_manufacturer = "Keithley Instruments Inc."
        self._identity_instrument_model = ""
        self._identity_instrument_firmware_revision = ""
        self._identity_specification_major_version = 4
        self._identity_specification_minor_version = 1
        self._identity_supported_instrument_models = ['2000', '2015']
        
        self._measurement_continuous = 'off'
        self._add_property('measurement.continuous',
                        self._get_measurement_continuous,
                        self._set_measurement_continuous)
        
        self._set_cache_valid(False, 'measurement_function')
    
    def _initialize(self, resource = None, id_query = False, reset = False, **keywargs):
        "Opens an I/O session to the instrument."
        
        super(keithley2000, self)._initialize(resource, id_query, reset, **keywargs)
        
        # interface clear
        if not self._driver_operation_simulate:
            self._clear()
        
        # check ID
        if id_query and not self._driver_operation_simulate:
            id = self.identity.instrument_model
            id_check = self._instrument_id
            id_short = id[:len(id_check)]
            if id_short != id_check:
                raise Exception("Instrument ID mismatch, expecting %s, got %s", id_check, id_short)
        
        # reset
        if reset:
            self.utility.reset()
    
    def _get_measurement_function(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            value = self._ask(":sense:function?").lower().strip('"')
            value = [k for k,v in MeasurementFunctionMapping.items() if v==value][0]
            self._measurement_function = value
            self._set_cache_valid()
        return self._measurement_function
    
    def _set_measurement_function(self, value):
        if value not in MeasurementFunctionMapping:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write(":sense:function '%s'" % MeasurementFunctionMapping[value])
        self._measurement_function = value
        self._set_cache_valid()
        self._set_cache_valid(False, 'range')
        self._set_cache_valid(False, 'auto_range')
        self._set_cache_valid(False, 'resolution')

    def _get_resolution(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            func = self._get_measurement_function()
            if func in MeasurementResolutionMapping:
                cmd = MeasurementResolutionMapping[func]
                value = float(self._ask("%s?" % (cmd)))
                self._resolution = value
                self._set_cache_valid()
        return self._resolution
    
    def _set_resolution(self, value):
        value = float(value)
        # round up to even power of 10
        value = math.pow(10, math.ceil(math.log10(value)))
        if not self._driver_operation_simulate:
            func = self._get_measurement_function()
            if func in MeasurementResolutionMapping:
                cmd = MeasurementResolutionMapping[func]
                self._write("%s %g" % (cmd, value))
        self._resolution = value
        self._set_cache_valid()
    
    def _get_measurement_continuous(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            value = self._ask(":init:cont?")
            
            self._measurement_continuous = value
            self._set_cache_valid()
        
        return self._measurement_continuous
    
    def _set_measurement_continuous(self, value):
        if value not in dmm.Auto2:
            return ivi.ValueNotSupportedException
        
        if not self._driver_operation_simulate:
            self._write(":init:cont %s" % value)
        
        self._measurement_continuous = value
        self._set_cache_valid()
