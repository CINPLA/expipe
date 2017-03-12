"""
Python library for reading INTAN files.
Depends on: os
            numpy
            quantities

Authors: Alessio Buccino @CINPLA,
         Svenn-Arne Dragly @CINPLA,
         Milad H. Mobarhan @CINPLA,
         Mikkel E. Lepperod @CINPLA
"""

import os
import numpy as np
import quantities as pq
import time
import re


class AnalogSignals:
    def __init__(self, signals, times, sample_rate):
        self.signals = signals
        self.times = times
        self.sample_rate = sample_rate

    def __str__(self):
        return "<Intan analog signals:shape: {}, sample_rate: {}>".format(
            self.signals.shape, self.sample_rate
        )

class DigitalSignals:
    def __init__(self, dig_in, dig_out, sample_rate):
        self.dig_in = dig_in
        self.dig_out = dig_out
        self.sample_rate = sample_rate

    def __str__(self):
        return "<Intan digital signals:shape: {}, sample_rate: {}>".format(
            self.dig_in.shape, self.sample_rate
        )

class Stimulation:
    def __init__(self, stim_data, amp_settle, charge_recovery, compliance_limit, stim_param):
        self.stim_data = stim_data
        self.amp_settle = amp_settle
        self.charge_recovery = charge_recovery
        self.compliance_limit = compliance_limit
        self.stim_param = stim_param

    def __str__(self):
        return "<Intan stimulation signals:shape: {}, param: {}>".format(
            self.stim_param.shape, self.stim_param
        )

class File:
    """
    Class for reading experimental data from an OpenEphys dataset.
    """
    def __init__(self, filename):
        self._absolute_filename = os.path.abspath(filename)

        data = load(filename)

        self._analog_signals = AnalogSignals(
            signals=data['amplifier_data'],
            times=data['t'],
            sample_rate=data['frequency_parameters']['amplifier_sample_rate']
        )

        self._digital_signals = DigitalSignals(
            dig_in=data['board_dig_in_data'],
            dig_out=data['board_dig_out_data'],
            sample_rate=data['frequency_parameters']['board_dig_in_sample_rate']
        )

        self._stimulation = Stimulation(
            stim_data=data['stim_data'],
            amp_settle=data['amp_settle_data'],
            charge_recovery=data['charge_recovery_data'],
            compliance_limit=data['compliance_limit_data'],
            stim_param=data['stim_parameters']
        )


    @property
    def session(self):
        return self._absolute_filename


    @property
    def analog_signals(self):
        return self._analog_signals

    @property
    def digital_signals(self):
        return self._digital_signals

    @property
    def stimulation(self):
        return self._stimulation


def load(filepath, savedat=False):
    # redirects to code for individual file types
    if 'rhs' in filepath:
        data = loadRHS(filepath, savedat)
    elif 'rhd' in filepath:
        print('to be implemented soon')
        data = []
    else:
        raise Exception("Not a recognized file type. Please input a .continuous, .spikes, or .events file")

    return data


def loadRHS(filepath, savedat=False):
    data = {}

    t1 = time.time()

    print('loading intan data')

    f = open(filepath, 'rb')
    filesize = os.fstat(f.fileno()).st_size - f.tell()

    # Check 'magic number' at beginning of file to make sure this is an Intan
    # Technologies RHS2000 data file.
    magic_number = np.fromfile(f, np.dtype('u4'), 1)
    if magic_number != int('d69127ac', 16):
        raise IOError('Unrecognized file type.')

    # Read version number.
    data_file_main_version_number = np.fromfile(f, 'i2', 1)[0]
    data_file_secondary_version_number = np.fromfile(f, 'i2', 1)[0]

    print('Reading Intan Technologies RHS2000 Data File, Version ', data_file_main_version_number, \
        data_file_secondary_version_number)

    num_samples_per_data_block = 128

    # Read information of sampling rate and amplifier frequency settings.
    sample_rate = np.fromfile(f, 'f4', 1)[0]
    dsp_enabled = np.fromfile(f, 'i2', 1)[0]
    actual_dsp_cutoff_frequency = np.fromfile(f, 'f4', 1)[0]
    actual_lower_bandwidth = np.fromfile(f, 'f4', 1)[0]
    actual_lower_settle_bandwidth = np.fromfile(f, 'f4', 1)[0]
    actual_upper_bandwidth = np.fromfile(f, 'f4', 1)[0]

    desired_dsp_cutoff_frequency = np.fromfile(f, 'f4', 1)[0]
    desired_lower_bandwidth = np.fromfile(f, 'f4', 1)[0]
    desired_lower_settle_bandwidth = np.fromfile(f, 'f4', 1)[0]
    desired_upper_bandwidth = np.fromfile(f, 'f4', 1)[0]

    # This tells us if a software 50/60 Hz notch filter was enabled during the data acquistion
    notch_filter_mode = np.fromfile(f, 'i2', 1)[0]
    notch_filter_frequency = 0
    if notch_filter_mode == 1:
        notch_filter_frequency = 50
    elif notch_filter_mode == 2:
        notch_filter_frequency = 60

    desired_impedance_test_frequency = np.fromfile(f, 'f4', 1)[0]
    actual_impedance_test_frequency = np.fromfile(f, 'f4', 1)[0]

    amp_settle_mode = np.fromfile(f, 'i2', 1)[0]
    charge_recovery_mode = np.fromfile(f, 'i2', 1)[0]

    stim_step_size = np.fromfile(f, 'f4', 1)[0]
    charge_recovery_current_limit = np.fromfile(f, 'f4', 1)[0]
    charge_recovery_target_voltage = np.fromfile(f, 'f4', 1)[0]

    # Place notes in data structure
    notes = {'note1': fread_QString(f),
             'note2': fread_QString(f),
             'note3': fread_QString(f)}

    # See if dc amplifier was saved
    dc_amp_data_saved = np.fromfile(f, 'i2', 1)[0]

    # Load eval board mode
    eval_board_mode = np.fromfile(f, 'i2', 1)[0]

    reference_channel = fread_QString(f)

    # Place frequency-related information in data structure.
    frequency_parameters = {
    'amplifier_sample_rate': sample_rate * pq.Hz,
    'board_adc_sample_rate': sample_rate,
    'board_dig_in_sample_rate': sample_rate,
    'desired_dsp_cutoff_frequency': desired_dsp_cutoff_frequency,
    'actual_dsp_cutoff_frequency': actual_dsp_cutoff_frequency,
    'dsp_enabled': dsp_enabled,
    'desired_lower_bandwidth': desired_lower_bandwidth,
    'desired_lower_settle_bandwidth': desired_lower_settle_bandwidth,
    'actual_lower_bandwidth': actual_lower_bandwidth,
    'actual_lower_settle_bandwidth': actual_lower_settle_bandwidth,
    'desired_upper_bandwidth': desired_upper_bandwidth,
    'actual_upper_bandwidth': actual_upper_bandwidth,
    'notch_filter_frequency': notch_filter_frequency,
    'desired_impedance_test_frequency': desired_impedance_test_frequency,
    'actual_impedance_test_frequency': actual_impedance_test_frequency}

    stim_parameters = {
    'stim_step_size': stim_step_size,
    'charge_recovery_current_limit': charge_recovery_current_limit,
    'charge_recovery_target_voltage': charge_recovery_target_voltage,
    'amp_settle_mode': amp_settle_mode,
    'charge_recovery_mode': charge_recovery_mode}

    # Define data structure for spike trigger settings.
    spike_trigger_struct = {
    'voltage_trigger_mode': {},
    'voltage_threshold': {},
    'digital_trigger_channel': {},
    'digital_edge_polarity': {} }


    spike_triggers = []

    # Define data structure for data channels.
    channel_struct = {
    'native_channel_name': {},
    'custom_channel_name': {},
    'native_order': {},
    'custom_order': {},
    'board_stream': {},
    'chip_channel': {},
    'port_name': {},
    'port_prefix': {},
    'port_number': {},
    'electrode_impedance_magnitude': {},
    'electrode_impedance_phase': {} }

    # Create structure arrays for each type of data channel.
    amplifier_channels = []
    board_adc_channels = []
    board_dac_channels = []
    board_dig_in_channels = []
    board_dig_out_channels = []

    amplifier_index = 0
    board_adc_index = 0
    board_dac_index = 0
    board_dig_in_index = 0
    board_dig_out_index = 0

    # Read signal summary from data file header.

    number_of_signal_groups = np.fromfile(f, 'i2', 1)[0]
    print('Signal groups: ', number_of_signal_groups)

    for signal_group in range(number_of_signal_groups):
        signal_group_name = fread_QString(f)
        signal_group_prefix = fread_QString(f)
        signal_group_enabled = np.fromfile(f, 'i2', 1)[0]
        signal_group_num_channels = np.fromfile(f, 'i2', 1)[0]
        signal_group_num_amp_channels = np.fromfile(f, 'i2', 1)[0]

        if signal_group_num_channels > 0 and signal_group_enabled > 0:
            new_channel = {}
            new_trigger_channel = {}

            new_channel['port_name'] = signal_group_name
            new_channel['port_prefix'] = signal_group_prefix
            new_channel['port_number'] = signal_group
            for signal_channel in range(signal_group_num_channels):
                new_channel['native_channel_name'] = fread_QString(f)
                new_channel['custom_channel_name'] = fread_QString(f)
                new_channel['native_order'] = np.fromfile(f, 'i2', 1)[0]
                new_channel['custom_order'] = np.fromfile(f, 'i2', 1)[0]
                signal_type = np.fromfile(f, 'i2', 1)[0]
                channel_enabled = np.fromfile(f, 'i2', 1)[0]
                new_channel['chip_channel'] = np.fromfile(f, 'i2', 1)[0]
                np.fromfile(f, 'i2', 1)[0] # ignore command_stream
                new_channel['board_stream'] = np.fromfile(f, 'i2', 1)[0]
                new_trigger_channel['voltage_trigger_mode'] = np.fromfile(f, 'i2', 1)[0]
                new_trigger_channel['voltage_threshold'] = np.fromfile(f, 'i2', 1)[0]
                new_trigger_channel['digital_trigger_channel'] = np.fromfile(f, 'i2', 1)[0]
                new_trigger_channel['digital_edge_polarity'] = np.fromfile(f, 'i2', 1)[0]
                new_channel['electrode_impedance_magnitude'] = np.fromfile(f, 'f4', 1)[0]
                new_channel['electrode_impedance_phase'] = np.fromfile(f, 'f4', 1)[0]

                if channel_enabled:
                    if signal_type == 0:
                        ch = new_channel.copy()
                        amplifier_channels.append(ch)
                        spike_triggers.append(new_trigger_channel)
                        amplifier_index = amplifier_index + 1
                    elif signal_type == 1:
                        # aux inputs not used in RHS2000 system
                        pass
                    elif signal_type == 2:
                        # supply voltage not used in RHS2000 system
                        pass
                    elif signal_type == 3:
                        ch = new_channel.copy()
                        board_adc_channels.append(ch)
                        board_adc_index = board_adc_index + 1
                    elif signal_type == 4:
                        ch = new_channel.copy()
                        board_dac_channels.append(ch)
                        board_dac_index = board_dac_index + 1
                    elif signal_type == 5:
                        ch = new_channel.copy()
                        board_dig_in_channels.append(ch)
                        board_dig_in_index = board_dig_in_index + 1
                    elif signal_type == 6:
                        ch = new_channel.copy()
                        board_dig_out_channels.append(ch)
                        board_dig_out_index = board_dig_out_index + 1
                    else:
                        raise Exception('Unknown channel type')


    # Summarize contents of data file.
    num_amplifier_channels = amplifier_index
    num_board_adc_channels = board_adc_index
    num_board_dac_channels = board_dac_index
    num_board_dig_in_channels = board_dig_in_index
    num_board_dig_out_channels = board_dig_out_index

    print('Found ', num_amplifier_channels, ' amplifier channel' , plural(num_amplifier_channels))
    if dc_amp_data_saved != 0:
        print('Found ', num_amplifier_channels, 'DC amplifier channel' , plural(num_amplifier_channels))
    print('Found ', num_board_adc_channels, ' board ADC channel' , plural(num_board_adc_channels))
    print('Found ', num_board_dac_channels, ' board DAC channel' , plural(num_board_adc_channels))
    print('Found ', num_board_dig_in_channels, ' board digital input channel' , plural(num_board_dig_in_channels))
    print('Found ', num_board_dig_out_channels, ' board digital output channel' , plural(num_board_dig_out_channels))

    # Determine how many samples the data file contains.

    # Each data block contains num_samplesper_data_block amplifier samples
    bytes_per_block = num_samples_per_data_block * 4  # timestamp data
    if dc_amp_data_saved != 0:
        bytes_per_block += num_samples_per_data_block * (2 + 2 + 2) * num_amplifier_channels
    else:
        bytes_per_block += num_samples_per_data_block * (2 + 2) * num_amplifier_channels
    # Board analog inputs are sampled at same rate as amplifiers
    bytes_per_block += num_samples_per_data_block * 2 * num_board_adc_channels
    # Board analog outputs are sampled at same rate as amplifiers
    bytes_per_block += num_samples_per_data_block * 2 * num_board_dac_channels
    # Board digital inputs are sampled at same rate as amplifiers
    if num_board_dig_in_channels > 0:
        bytes_per_block += num_samples_per_data_block * 2
    # Board digital outputs are sampled at same rate as amplifiers
    if num_board_dig_out_channels > 0:
        bytes_per_block += num_samples_per_data_block * 2

    # How many data blocks remain in this file?
    data_present = 0
    bytes_remaining = filesize - f.tell()
    if bytes_remaining > 0:
        data_present = 1


    num_data_blocks = int(bytes_remaining / bytes_per_block)

    num_amplifier_samples = num_samples_per_data_block * num_data_blocks
    num_board_adc_samples = num_samples_per_data_block * num_data_blocks
    num_board_dac_samples = num_samples_per_data_block * num_data_blocks
    num_board_dig_in_samples = num_samples_per_data_block * num_data_blocks
    num_board_dig_out_samples = num_samples_per_data_block * num_data_blocks

    record_time = num_amplifier_samples / sample_rate

    if data_present:
        print('File contains ', record_time, ' seconds of data.  ' \
                                             'Amplifiers were sampled at ', sample_rate / 1000 , ' kS/s.')
    else:
        print('Header file contains no data.  Amplifiers were sampled at ', sample_rate / 1000 ,  'kS/s.')

    if data_present:

        # Pre-allocate memory for data.
        print('Allocating memory for data')

        t = np.zeros(num_amplifier_samples)

        amplifier_data = np.zeros((num_amplifier_channels, num_amplifier_samples))
        if dc_amp_data_saved != 0:
            dc_amplifier_data = np.zeros((num_amplifier_channels, num_amplifier_samples))

        stim_data = np.zeros((num_amplifier_channels, num_amplifier_samples))
        board_adc_data = np.zeros((num_board_adc_channels, num_board_adc_samples))
        board_dac_data = np.zeros((num_board_dac_channels, num_board_dac_samples))
        board_dig_in_data = np.zeros((num_board_dig_in_channels, num_board_dig_in_samples))
        board_dig_in_raw = np.zeros(num_board_dig_in_samples)
        board_dig_out_data = np.zeros((num_board_dig_out_channels, num_board_dig_out_samples))
        board_dig_out_raw = np.zeros(num_board_dig_out_samples)

        # Read sampled data from file.
        print('Reading data from file')

        amplifier_index = 0
        board_adc_index = 0
        board_dac_index = 0
        board_dig_in_index = 0
        board_dig_out_index = 0

        print_increment = 10
        percent_done = print_increment

        print('num_data_blocks: ', num_data_blocks)

        for i in range(num_data_blocks):
            t[amplifier_index:(amplifier_index + num_samples_per_data_block)] = \
                np.fromfile(f, 'i4', num_samples_per_data_block)
            if num_amplifier_channels > 0:
                amplifier_data[:, amplifier_index:(amplifier_index + num_samples_per_data_block)] = \
                    np.reshape(np.fromfile(f, 'u2', num_samples_per_data_block*num_amplifier_channels),
                                (num_amplifier_channels, num_samples_per_data_block))
                if dc_amp_data_saved != 0:
                    dc_amplifier_data[:, amplifier_index:(amplifier_index + num_samples_per_data_block)] = \
                        np.reshape(np.fromfile(f, 'u2', num_samples_per_data_block * num_amplifier_channels),
                                   (num_amplifier_channels, num_samples_per_data_block))
                stim_data[:, amplifier_index:(amplifier_index + num_samples_per_data_block)] = \
                    np.reshape(np.fromfile(f, 'u2', num_samples_per_data_block * num_amplifier_channels),
                               (num_amplifier_channels, num_samples_per_data_block))

            if num_board_adc_channels > 0:
                board_adc_data[:, board_adc_index:(board_adc_index + num_samples_per_data_block)] = \
                    np.reshape(np.fromfile(f, 'u2', num_samples_per_data_block*num_board_adc_channels),
                                (num_board_adc_channels, num_samples_per_data_block))
            if num_board_dac_channels > 0:
                board_dac_data[:, board_dac_index:(board_dac_index + num_samples_per_data_block)] = \
                    np.reshape(np.fromfile(f, 'u2', num_samples_per_data_block*num_board_dac_channels),
                                (num_board_dac_channels, num_samples_per_data_block))
            if num_board_dig_in_channels > 0:
                board_dig_in_raw[board_dig_in_index:(board_dig_in_index + num_samples_per_data_block)] = \
                np.fromfile(f, 'u2', num_samples_per_data_block)
            if num_board_dig_out_channels > 0:
                board_dig_out_raw[board_dig_out_index:(board_dig_out_index + num_samples_per_data_block)] = \
                np.fromfile(f, 'u2', num_samples_per_data_block)

            amplifier_index += num_samples_per_data_block
            board_adc_index += num_samples_per_data_block
            board_dac_index += num_samples_per_data_block
            board_dig_in_index += num_samples_per_data_block
            board_dig_out_index += num_samples_per_data_block

            fraction_done = 100 * float((i+1) / float(num_data_blocks))
            if fraction_done >= percent_done:
                print(percent_done, '% done')
                percent_done += print_increment

        # Make sure we have read exactly the right amount of data.
        bytes_remaining = filesize - f.tell()
        if bytes_remaining != 0:
            # raise Error('Error: End of file not reached.')
            pass

    # Close data file.
    f.close()

    t2 = time.time()
    print('Loading done. time: ', t2 - t1)

    if data_present:

        print('Parsing data')

        # # Extract digital input channels to separate variables.
        # '''FIX THIS'''
        # for i in range(num_board_dig_in_channels):
        #     # print(len(board_dig_in_channels)
        #     mask = (2 ** board_dig_in_channels[i]['native_order']) * np.ones(len(board_dig_in_raw))
        #     # board_dig_in_data[i,:] = (board_dig_in_raw & mask > 0)
        #
        # for i in range(num_board_dig_out_channels):
        #     mask = (2 ** board_dig_out_channels[i]['native_order']) * np.ones(len(board_dig_out_raw))
        #     # board_dig_in_data[i, :] = (board_dig_out_raw & mask > 0)


        #TODO optimize memory-wise: e.g. only save time and chan of compliance, ampsett, charge recovery as list
        # Scale voltage levels appropriately.
        amplifier_data -= 32768  # units = microvolts
        amplifier_data *= 0.195  # units = microvolts
        if dc_amp_data_saved != 0:
            dc_amplifier_data -= 512  # units = volts
            dc_amplifier_data *= -0.01923  # units = volts

        stim_polarity = np.zeros((num_amplifier_channels, num_amplifier_samples))

        compliance_limit_data_idx = np.where(stim_data >= 2 ** 15)
        stim_data[compliance_limit_data_idx] = 0
        charge_recovery_data_idx = np.where(stim_data >= 2 ** 14)
        stim_data[charge_recovery_data_idx] = 0
        amp_settle_data_idx = np.where(stim_data >= 2 ** 13)
        stim_data[amp_settle_data_idx] = 0

        stim_polarity_idx = np.where(stim_data >= 2 ** 8)
        stim_polarity[stim_polarity_idx] = 1
        stim_data[stim_polarity_idx] = 0
        stim_polarity = 1 - 2 * stim_polarity  # convert(0 = pos, 1 = neg) to + / -1
        stim_data *= stim_polarity
        stim_data = stim_parameters['stim_step_size'] * stim_data / float(1e-6)  # units = microamps

        board_adc_data =-32768  # units = volts
        board_adc_data *= 312.5e-6  # units = volts
        board_dac_data -= 32768  # units = volts
        board_dac_data *= 312.5e-6  # units = volts

        amp_settle_data = np.array((num_amplifier_channels, None))
        charge_recovery_data = np.array((num_amplifier_channels, None))
        compliance_limit_data = np.array((num_amplifier_channels, None))

        # Check for gaps in timestamps.
        num_gaps = len(np.where(np.diff(t) != 1)[0])
        if num_gaps == 0:
            print('No missing timestamps in data.')
        else:
            print('Warning: ', num_gaps, ' gaps in timestamp data found.  Time scale will not be uniform!')
        # Scale time steps (units = seconds).
        t /= float(sample_rate)

        for chan in range(num_amplifier_channels):
            if len(amp_settle_data_idx[0]) != 0:
                amp_settle_data[chan] = t[amp_settle_data_idx[1][np.where(amp_settle_data_idx[0]==chan)]]
            if len(charge_recovery_data_idx[0]) != 0:
                charge_recovery_data[chan] = t[charge_recovery_data_idx[1][np.where(charge_recovery_data_idx[0] == chan)]]
            if len(compliance_limit_data_idx[0]) != 0:
                compliance_limit_data[chan] = t[compliance_limit_data_idx[1][np.where(compliance_limit_data_idx[0] == chan)]]

        t3 = time.time()
        print('Parsing done. time: ', t3 - t2)

    # Create data dictionary
    print('Creating data structure...')
    data = dict()
    data['notes'] = notes
    data['frequency_parameters'] = frequency_parameters
    data['stim_parameters'] =  stim_parameters
    if data_file_main_version_number > 1:
        data['reference_channel'] = reference_channel

    if num_amplifier_channels > 0:
        data['amplifier_channels'] = amplifier_channels
        if data_present:
            data['amplifier_data'] = amplifier_data
            if dc_amp_data_saved != 0:
                data['dc_amplifier_data'] = dc_amplifier_data

            data['stim_data'] = stim_data
            data['amp_settle_data'] = amp_settle_data
            data['charge_recovery_data'] = charge_recovery_data
            data['compliance_limit_data'] = compliance_limit_data
            data['t'] = t

        data['spike_triggers'] = spike_triggers

    if num_board_adc_channels > 0:
        data['board_adc_channels'] = board_adc_channels
        if data_present:
            data['board_adc_data'] = board_adc_data
    else:
        data['board_adc_data'] = np.array([])

    if num_board_dac_channels > 0:
        data['board_dac_channels'] = board_dac_channels
        if data_present:
            data['board_dac_data'] = board_dac_data
    else:
        data['board_dac_data'] = np.array([])

    if num_board_dig_in_channels > 0:
        data['board_dig_in_channels'] = board_dig_in_channels
        if data_present:
            data['board_dig_in_data'] = board_dig_in_data
    else:
        data['board_dig_in_data'] = np.array([])


    if num_board_dig_out_channels > 0:
        data['board_dig_out_channels'] = board_dig_out_channels
        if data_present:
            data['board_dig_out_data'] = board_dig_out_data
    else:
        data['board_dig_out_data'] = np.array([])


    if data_present:
        print('Extracted data are now available in the python workspace.')
    else:
        print('Extracted waveform information is now available in the python workspace.')


    if savedat:
        print('Writing ' + filepath[:-4] + '.dat.')
        fdat = filepath[:-4] + '.dat'
        with open(fdat, 'wb') as f:
            np.transpose(amplifier_data).tofile(f)

    return data

def fread_QString(f):

    a = ''
    length = np.fromfile(f, 'u4', 1)[0]

    if hex(length) == '0xffffffff':
        print('return fread_QString')
        return

    # convert length from bytes to 16-bit Unicode words
    length = int(length / 2)

    for ii in range(length):
        newchar = np.fromfile(f, 'u2', 1)[0]
        a += newchar.tostring().decode('utf-16')
    return a

def plural(n):

    # s = plural(n)
    #
    # Utility function to optionally plurailze words based on the value
    # of n.

    if n == 1:
        s = ''
    else:
        s = 's'

    return s
