"""
Python library for reading OpenEphys files.
Depends on: sys
            os
            glob
            datetime
            numpy
            quantities

Authors: Alessio Buccino @CINPLA,
         Svenn-Arne Dragly @CINPLA,
         Milad H. Mobarhan @CINPLA,
         Mikkel E. Lepperod @CINPLA
"""

from __future__ import division
from __future__ import print_function
from __future__ import with_statement

import sys
import quantities as pq
import os
from os.path import join
import glob
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime

# constants for pre-allocating matrices:
MAX_NUMBER_OF_EVENTS = int(1e6)

data_end_string = "\r\ndata_end\r\n"
data_end_length = len(data_end_string)

assert(data_end_length == 12)


def scale_analog_signal(value, gain, adc_fullscale_mv, bytes_per_sample):
    """
    Takes value as raw sample data and converts it to millivolts quantity.
    The mapping in the case of bytes_per_sample = 1 is
        [-128, 127] -> [-1.0, (127.0/128.0)] * adc_fullscale_mv / gain (mV)
    The correctness of this mapping has been verified by contacting Axona.
    """
    if type(value) is np.ndarray and value.base is not None:
        raise ValueError("Value passed to scale_analog_signal cannot be a numpy view because we need to convert the entire array to a quantity.")
    max_value = 2**(8 * bytes_per_sample - 1)  # 128 when bytes_per_sample = 1
    result = (value / max_value) * (adc_fullscale_mv / gain)
    result = result
    return result


class Channel:
    def __init__(self, index, name, gain):
        self.index = index
        self.name = name
        self.gain = gain


class ChannelGroup:
    def __init__(self, channel_group_id, filename, channels, adc_fullscale, attrs):
        self.attrs = attrs
        self.filename = filename
        self.channel_group_id = channel_group_id
        self.channels = channels
        self._adc_fullscale = adc_fullscale

    @property
    def analog_signals(self):
        return self.analog_signals


class AnalogSignal:
    def __init__(self, channel_id, signal, sample_rate, attrs):
        self.channel_id = channel_id
        self.signal = signal
        self.sample_rate = sample_rate
        self.attrs = attrs

    def __str__(self):
        return "<Axona analog signal: channel: {}, shape: {}, sample_rate: {}>".format(
            self.channel_id, self.signal.shape, self.sample_rate
        )


class TrackingData:
    def __init__(self, times, positions, attrs):
        self.attrs = attrs
        self.times = times
        self.positions = positions

    def __str__(self):
        return "<Axona tracking data: times shape: {}, positions shape: {}>".format(
            self.times.shape, self.positions.shape
        )



class File:
    """
    Class for reading experimental data from an OpenEphys dataset.
    """
    def __init__(self, foldername):
        self._absolute_foldername = foldername
        self._path, relative_foldername = os.path.split(foldername)

        filenames = [f for f in os.listdir(self._absolute_foldername)]
        if not any(sett == 'settings.xml' for sett in filenames):
            raise ValueError("'setting.xml' should be in the folder")

        # Read and parse 'settings.xml'
        tree = ET.parse(join(self._absolute_foldername, 'settings.xml'))
        self._root = tree.getroot()
        self.nchan = 0
        rhythm = False
        rhythmID = -1
        rhythmRates = np.array([1., 1.25, 1.5, 2, 2.5, 3, 3.33, 4., 5., 6.25, 8., 10., 12.5, 15., 20., 25., 30.])
        osc = False
        oscID = -1
        self.tracking_timesamples_rate = 1000 * 1000. * pq.Hz

        # Count number of recorded channels
        if self._root.tag == 'SETTINGS':
            print ('Reading settings.xml...')
            for child in self._root:
                if child.tag == 'SIGNALCHAIN':
                    for granchild in child:
                        if granchild.tag == 'PROCESSOR' and granchild.attrib['name'] == 'Sources/Rhythm FPGA':
                            rhythm = True
                            rhythmID = granchild.attrib['NodeId']
                            for chan in granchild:
                                if chan.tag == 'CHANNEL':
                                    for selec in chan:
                                        if selec.tag == 'SELECTIONSTATE':
                                            if selec.attrib['record'] == '1':
                                                self.nchan += 1
                                if chan.tag == 'EDITOR':
                                    sampleIdx = int(chan.attrib['SampleRate'])-1
                                    self.sample_rate = rhythmRates[sampleIdx] * 1000. * pq.Hz
                            print('RhythmFPGA with ', self.nchan, ' channels. NodeId: ', rhythmID)
                        if granchild.tag == 'PROCESSOR' and granchild.attrib['name'] == 'Sources/OSC Port':
                            osc = True
                            oscID = granchild.attrib['NodeId']
                            print('OSC Port. NodeId: ', oscID)
                if child.tag == 'CONTROLPANEL':
                    # Check openephys format
                    if child.attrib['recordEngine'] == 'OPENEPHYS':
                        self._format = 'openephys'
                    elif child.attrib['recordEngine'] == 'RAWBINARY':
                        self._format = 'binary'
                    else:
                        self._format = 'INVALID'
                    print('Decoding data from ', self._format, ' format')


        # Check and decode files
        if self._format == 'binary':
            print(rhythm)
            if rhythm is True:
                if any('.dat' in f for f in filenames):
                    datfile = [f for f in filenames if '.dat' in f][0]
                    print('.dat: ', datfile)
                    with open(join(self._absolute_foldername, datfile), "rb") as fh:
                        self._nsamples = self._read_analog_signals(fh, self.nchan)
                        if any('.eventsmessages' in f for f in filenames):
                            messagefile = [f for f in filenames if '.eventsmessages' in f][0]
                            self._create_analog_timestamps(messagefile, self._nsamples)
                else:
                    raise ValueError("'.dat' should be in the folder")
            else:
                print('No rhythm FPGA data')
            if osc is True and any('.eventsbinary' in f for f in filenames):
                posfile = [f for f in filenames if '.eventsbinary' in f][0]
                print('.eventsbinary: ', posfile)
                with open(join(self._absolute_foldername, posfile), "r", encoding='utf-8', errors='ignore') as fh:
                    self._read_tracking(fh)
            else:
                raise ValueError("'.eventsbinary' should be in the folder")


        # with open(self._absolute_filename, "r") as f:
        #     text = f.read()
        #
        # attrs = parse_attrs(text)
        #
        # self._adc_fullscale = float(attrs["ADC_fullscale_mv"]) * 1000.0 * pq.uV
        # if all(key in attrs for key in ['trial_date', 'trial_time']):
        #     self._start_datetime = datetime.strptime(attrs['trial_date'] +
        #                                              attrs['trial_time'],
        #                                              '%A, %d %b %Y%H:%M:%S')
        # else:
        #     self._start_datetime = None
        # self._duration = float(attrs["duration"]) * pq.s
        # self._tracked_spots_count = int(attrs["tracked_spots"])
        # self.attrs = attrs
        #
        # self._channel_groups = []
        # self._analog_signals = []
        # self._cuts = []
        # self._inp_data = None
        # self._tracking = None
        #
        # self._channel_groups_dirty = True
        # self._analog_signals_dirty = True
        # self._cuts_dirty = True
        # self._inp_data_dirty = True
        # self._tracking_dirty = True

    @property
    def settings(self):
        return self._root

    @property
    def session(self):
        return self._base_filename

    @property
    def related_files(self):
        file_path = os.path.join(self._path, self._base_filename)
        cut_files = glob.glob(os.path.join(file_path + "_[0-9]*.cut"))

        return glob.glob(os.path.join(file_path + ".*")) + cut_files

    def channel_group(self, channel_id):
        if self._channel_groups_dirty:
            self._read_channel_groups()

        return self._channel_id_to_channel_group[channel_id]

    @property
    def channel_groups(self):
        if self._channel_groups_dirty:
            self._read_channel_groups()

        return self._channel_groups

    @property
    def analog_signals(self):
        if self._analog_signals_dirty:
            self._read_analog_signals()

        return self._analog_signals

    @property
    def tracking(self):
        if self._tracking_dirty:
            self._read_tracking()

        return self._tracking

    @property
    def inp_data(self):
        if self._inp_data_dirty:
            self._read_inp_data()

        return self._inp_data

    @property
    def cuts(self):
        if self._cuts_dirty:
            self._read_cuts()

        return self._cuts



    def _read_tracking(self, fh):
        # tracking_data = {}

        print ('Reading positions...')

        header = self._readHeader(fh)

        if float(header['version']) < 0.4:
            raise Exception('Loader is only compatible with .events files with version 0.4 or higher')

        # tracking_data['header'] = header

        index = -1

        ids = np.zeros(MAX_NUMBER_OF_EVENTS)
        timestamps = np.zeros(MAX_NUMBER_OF_EVENTS)
        x = np.zeros(MAX_NUMBER_OF_EVENTS)
        y = np.zeros(MAX_NUMBER_OF_EVENTS)
        h = np.zeros(MAX_NUMBER_OF_EVENTS)
        w = np.zeros(MAX_NUMBER_OF_EVENTS)

        nsamples = (os.fstat(fh.fileno()).st_size -fh.tell()) / 25
        print('Estimated position samples: ', nsamples)
        nread = 0

        while fh.tell() < os.fstat(fh.fileno()).st_size:

            index += 1

            idcurr = np.fromfile(fh, '<u1', 1)
            tcurr = np.fromfile(fh, np.dtype('<i8'), 1)
            xcurr = np.fromfile(fh, np.dtype('<f4'), 1)
            ycurr = np.fromfile(fh, np.dtype('<f4'), 1)
            wcurr = np.fromfile(fh, np.dtype('<f4'), 1)
            hcurr = np.fromfile(fh, np.dtype('<f4'), 1)

            # if not np.isnan(xcurr) and not np.isnan(ycurr) and not np.isnan(wcurr) and not np.isnan(hcurr):
            #     if len(xcurr) == 1 and len(ycurr) == 1 and len(wcurr) == 1 and len(hcurr) == 1:
            ids[index] = idcurr
            x[index] = xcurr
            y[index] = ycurr
            w[index] = wcurr
            h[index] = hcurr
            timestamps[index] = tcurr

            nread += 1

        print('Read position samples: ', nread)

        ids = ids[:index]
        x = x[:index]
        y = y[:index]
        w = w[:index]
        h = h[:index]
        # times are in uS
        times = timestamps[:index] / 1000.

        # Sort out different Sources
        if len(np.unique(ids)) == 1:
            print("Single tracking source")
            # TODO
        else:
            print("Multiple tracking sources")
            sources = np.unique(ids)
            coord_s, w_s, h_s, ts_s = [], [], [], []
            sample_rate_s, width_s, height_s = [], [], []
            for ss in sources:
                x_ = np.squeeze(x[np.where(ids==ss)])
                y_ = np.squeeze(y[np.where(ids==ss)])
                w_ = np.squeeze(w[np.where(ids==ss)])
                h_ = np.squeeze(h[np.where(ids==ss)])
                ts_ = np.squeeze(times[np.where(ids==ss)])
                print('Ts len: ', len(ts_))

                # adjust times with linear interpolation
                idx_non_zero = np.where(ts_ != 0)
                linear_coeff = np.polyfit(np.arange(len(ts_))[idx_non_zero], ts_[idx_non_zero], 1)
                times_fit = linear_coeff[0]*(np.arange(len(ts_))) + linear_coeff[1]
                difft = np.diff(times_fit)
                avg_period = np.mean(difft)
                sample_rate_ = np.round(1./float(avg_period)) * pq.Hz

                coord_ = np.array([x_, y_])
                coord_s.append(coord_)
                ts_s.append(times_fit)

                sample_rate_s.append(sample_rate_)
                width_s.append(np.mean(w_))
                height_s.append(np.mean(h_))

            attrs = {}
            attrs['sample_rate'] = np.array(sample_rate_s)

            # xsize = w
            # ysize = h
            # length_scale = [xsize, ysize, xsize, ysize]
            # attrs['length_scale'] = length_scale
            attrs['length_scale'] = np.array([width_s, height_s])
            coord_s = coord_s
            ts_s = ts_s

            # coords = np.array([x_s, y_s]) * pq.m

        # # dacq doc: positions with value 1023 are missing
        # for i in range(2 * self._tracked_spots_count):
        #     coords[:, i] /= length_scale[i]
        #     coords[np.where(data["coords"][:, i] == 1023)] = np.nan * pq.m

        tracking_data = TrackingData(
            times=ts_s,
            positions=coord_s,
            attrs=attrs
        )

        self._tracking = tracking_data
        self._tracking_dirty = False


        # pos_filename = os.path.join(self._path, self._base_filename + ".pos")
        # if not os.path.exists(pos_filename):
        #     raise IOError("'.pos' file not found:" + pos_filename)
        #
        # with open(pos_filename, "rb") as f:
        #     attrs = parse_header_and_leave_cursor(f)
        #
        #     sample_rate_split = attrs["sample_rate"].split(" ")
        #     assert(sample_rate_split[1] == "hz")
        #     sample_rate = float(sample_rate_split[0]) * pq.Hz  # sample_rate 50.0 hz
        #
        #     eeg_samples_per_position = float(attrs["EEG_samples_per_position"])
        #     pos_samples_count = int(attrs["num_pos_samples"])
        #     bytes_per_timestamp = int(attrs["bytes_per_timestamp"])
        #     bytes_per_coord = int(attrs["bytes_per_coord"])
        #
        #     timestamp_dtype = ">i" + str(bytes_per_timestamp)
        #     coord_dtype = ">i" + str(bytes_per_coord)
        #
        #     bytes_per_pixel_count = 4
        #     pixel_count_dtype = ">i" + str(bytes_per_pixel_count)
        #
        #     bytes_per_pos = (bytes_per_timestamp + 2 * self._tracked_spots_count * bytes_per_coord + 8)  # pos_format is as follows for this file t,x1,y1,x2,y2,numpix1,numpix2.
        #
        #     # read data:
        #     dtype = np.dtype([("t", (timestamp_dtype, 1)),
        #                       ("coords", (coord_dtype, 1), 2 * self._tracked_spots_count),
        #                       ("pixel_count", (pixel_count_dtype, 1), 2)])
        #
        #     data = np.fromfile(f, dtype=dtype, count=pos_samples_count)
        #
        #     try:
        #         assert_end_of_data(f)
        #     except AssertionError:
        #         print("WARNING: found remaining data while parsing pos file")
        #
        #     time_scale = float(attrs["timebase"].split(" ")[0]) * pq.Hz
        #     times = data["t"].astype(float) / time_scale
        #
        #     window_min_x = float(attrs["window_min_x"])
        #     window_max_x = float(attrs["window_max_x"])
        #     window_min_y = float(attrs["window_min_y"])
        #     window_max_y = float(attrs["window_max_y"])
        #     xsize = window_max_x - window_min_x
        #     ysize = window_max_y - window_min_y
        #     length_scale = [xsize, ysize, xsize, ysize]
        #     coords = data["coords"].astype(float) * pq.m
        #
        #     # dacq doc: positions with value 1023 are missing
        #     for i in range(2 * self._tracked_spots_count):
        #         coords[:, i] /= length_scale[i]
        #         coords[np.where(data["coords"][:, i] == 1023)] = np.nan * pq.m
        #
        #     tracking_data = TrackingData(
        #         times=times,
        #         positions=coords,
        #         attrs=attrs
        #     )
        #


    def _read_analog_signals(self, filehandle, numchan):

        numchan=int(numchan)

        nsamples = os.fstat(filehandle.fileno()).st_size / (numchan*2)
        print('Estimated samples: ', int(nsamples))
        sam = []

        print('Reading all samples')
        while filehandle.tell() < os.fstat(filehandle.fileno()).st_size:
            sam = np.fromfile(filehandle, np.dtype('i2'))*0.195

        nread = len(sam)/numchan
        print('Read samples: ', int(nread))

        print('Rearranging...')
        samples = np.reshape(sam, (int(len(sam)/numchan), numchan))
        samples = np.transpose(samples)

        print('Done!')

        self._analog_signals = samples
        self._analog_signals_dirty = False

        return nread

    def _readHeader(self, fh):
        """Read header information from the first 1024 bytes of an OpenEphys file.

        Args:
            f: An open file handle to an OpenEphys file

        Returns: dict with the following keys.
            - bitVolts : float, scaling factor, microvolts per bit
            - blockLength : int, e.g. 1024, length of each record (see
                loadContinuous)
            - bufferSize : int, e.g. 1024
            - channel : the channel, eg "'CH1'"
            - channelType : eg "'Continuous'"
            - date_created : eg "'15-Jun-2016 21212'" (What are these numbers?)
            - description : description of the file format
            - format : "'Open Ephys Data Format'"
            - header_bytes : int, e.g. 1024
            - sampleRate : float, e.g. 30000.
            - version: eg '0.4'
            Note that every value is a string, even numeric data like bitVolts.
            Some strings have extra, redundant single apostrophes.
        """
        header = {}

        # Read the data as a string
        # Remove newlines and redundant "header." prefixes
        # The result should be a series of "key = value" strings, separated
        # by semicolons.
        header_string = fh.read(1024).replace('\n','').replace('header.','')

        # Parse each key = value string separately
        for pair in header_string.split(';'):
            if '=' in pair:
                # print pair
                key, value = pair.split(' = ')
                key = key.strip()
                value = value.strip()

                # Convert some values to numeric
                if key in ['bitVolts', 'sampleRate']:
                    header[key] = float(value)
                elif key in ['blockLength', 'bufferSize', 'header_bytes']:
                    header[key] = int(value)
                else:
                    # Keep as string
                    header[key] = value

        return header

    def _create_analog_timestamps(self, messagefile, nsamples):
        with open(join(self._absolute_foldername, messagefile)) as fm:
            lines = fm.readlines()
            if any('start time:' in l for l in lines):
                start = [l for l in lines if 'start time:' in l][0]
                s = start.split()
                start_time = float(int(s[0]))/self.sample_rate

                self._timestamps = np.arange(nsamples)/self.sample_rate + start_time
            else:
                raise Error('eventsmessages file should be in the same folder')



    # def _read_cuts(self):
    #     self._cuts = []
    #     cut_basename = os.path.join(self._path, self._base_filename)
    #     cut_files = glob.glob(cut_basename + "_[0-9]*.cut")
    #
    #     if not len(cut_files) > 0:
    #         raise IOError("'.cut' file(s) not found")
    #
    #     for cut_filename in sorted(cut_files):
    #         split_basename = os.path.basename(cut_filename).split(self._base_filename+"_")[-1]
    #         suffix = split_basename.split('.')[0]
    #         channel_group_id = int(suffix) - 1  # -1 to match channel_group_id
    #         lines = ""
    #         with open(cut_filename, "r") as f:
    #             for line in f:
    #                 if line.lstrip().startswith('Exact_cut_for'):
    #                     break
    #             lines = f.read()
    #             lines = lines.replace("\n", "").strip()
    #             indices = []
    #             indices += list(map(int, lines.split("  ")))
    #
    #             cut = CutData(
    #                 channel_group_id=channel_group_id,
    #                 indices=np.asarray(indices, dtype=np.int)
    #             )
    #             self._cuts.append(cut)
    #
    #     self._cuts_dirty = False


        # # TODO read for specific channel
        # # TODO check that .egf file exists
        #
        # self._analog_signals = []
        # eeg_basename = os.path.join(self._path, self._base_filename)
        # eeg_files = glob.glob(eeg_basename + ".eeg")
        # eeg_files += glob.glob(eeg_basename + ".eeg[0-9]*")
        # eeg_files += glob.glob(eeg_basename + ".egf")
        # eeg_files += glob.glob(eeg_basename + ".egf[0-9]*")
        # for eeg_filename in sorted(eeg_files):
        #     extension = os.path.splitext(eeg_filename)[-1][1:]
        #     file_type = extension[:3]
        #     suffix = extension[3:]
        #     if suffix == "":
        #         suffix = "1"
        #     suffix = int(suffix)
        #     with open(eeg_filename, "rb") as f:
        #         attrs = parse_header_and_leave_cursor(f)
        #         attrs["raw_filename"] = eeg_filename
        #
        #         if file_type == "eeg":
        #             sample_count = int(attrs["num_EEG_samples"])
        #         elif file_type == "egf":
        #             sample_count = int(attrs["num_EGF_samples"])
        #         else:
        #             raise IOError("Unknown file type. Should be .eeg or .efg.")
        #
        #         sample_rate_split = attrs["sample_rate"].split(" ")
        #         bytes_per_sample = attrs["bytes_per_sample"]
        #         assert(sample_rate_split[1].lower() == "hz")
        #         sample_rate = float(sample_rate_split[0]) * pq.Hz  # sample_rate 250.0 hz
        #
        #         sample_dtype = (('<i' + str(bytes_per_sample), 1), attrs["num_chans"])
        #         data = np.fromfile(f, dtype=sample_dtype, count=sample_count)
        #         assert_end_of_data(f)
        #
        #         eeg_final_channel_id = self.attrs["EEG_ch_" + str(suffix)]
        #         eeg_mode = self.attrs["mode_ch_" + str(eeg_final_channel_id)]
        #         ref_id = self.attrs["b_in_ch_" + str(eeg_final_channel_id)]
        #         eeg_original_channel_id = self.attrs["ref_" + str(ref_id)]
        #
        #         attrs["channel_id"] = eeg_original_channel_id
        #
        #         gain = self.attrs["gain_ch_{}".format(eeg_final_channel_id)]
        #
        #         signal = scale_analog_signal(data,
        #                                      gain,
        #                                      self._adc_fullscale,
        #                                      bytes_per_sample)
        #
        #         # TODO read start time
        #
        #         analog_signal = AnalogSignal(
        #             channel_id=eeg_original_channel_id,
        #             signal=signal,
        #             sample_rate=sample_rate,
        #             attrs=attrs
        #         )
        #
        #         self._analog_signals.append(analog_signal)
        #
        # self._analog_signals_dirty = False


    # def _read_channel_groups(self):
    #     # TODO this file reading can be removed, perhaps?
    #     channel_group_filenames = glob.glob(os.path.join(self._path, self._base_filename) + ".[0-9]*")
    #
    #     self._channel_id_to_channel_group = {}
    #     self._channel_group_id_to_channel_group = {}
    #     self._channel_count = 0
    #     self._channel_groups = []
    #     for channel_group_filename in channel_group_filenames:
    #         # increment before, because channel_groups start at 1
    #         basename, extension = os.path.splitext(channel_group_filename)
    #         channel_group_id = int(extension[1:]) - 1
    #         with open(channel_group_filename, "rb") as f:
    #             channel_group_attrs = parse_header_and_leave_cursor(f)
    #             num_chans = channel_group_attrs["num_chans"]
    #             channels = []
    #             for i in range(num_chans):
    #                 channel_id = self._channel_count + i
    #                 channel = Channel(
    #                     channel_id,
    #                     name="channel_{}_channel_group_{}_internal_{}".format(channel_id, channel_group_id, i),
    #                     gain=self._channel_gain(channel_group_id, i)
    #                 )
    #                 channels.append(channel)
    #
    #             channel_group = ChannelGroup(
    #                 channel_group_id,
    #                 filename=channel_group_filename,
    #                 channels=channels,
    #                 adc_fullscale=self._adc_fullscale,
    #                 attrs=channel_group_attrs
    #             )
    #
    #             self._channel_groups.append(channel_group)
    #             self._channel_group_id_to_channel_group[channel_group_id] = channel_group
    #
    #             for i in range(num_chans):
    #                 channel_id = self._channel_count + i
    #                 self._channel_id_to_channel_group[channel_id] = channel_group
    #
    #             # increment after, because channels start at 0
    #             self._channel_count += num_chans
    #
    #     # TODO add channels only for files that exist
    #     self._channel_ids = np.arange(self._channel_count)
    #     self._channel_groups_dirty = False
    #
    # def _channel_gain(self, channel_group_index, channel_index):
    #     # TODO split into two functions, one for mapping and one for gain lookup
    #     global_channel_index = channel_group_index * 4 + channel_index
    #     param_name = "gain_ch_{}".format(global_channel_index)
    #     return float(self.attrs[param_name])
    #
    # def _read_inp_data(self):
    #     """
    #     Reads axona .inp files.
    #     Event type can be 'I', 'O', or 'K' representing input,
    #     output, and keypress, respectively.
    #     The value of all event types is assumed to have dtype='>i',
    #     even though this is not true for keypress.
    #     """
    #     inp_filename = os.path.join(self._path, self._base_filename + ".inp")
    #     if not os.path.exists(inp_filename):
    #         raise IOError("'.inp' file not found:" + inp_filename)
    #
    #     with open(inp_filename, "rb") as f:
    #         attrs = parse_header_and_leave_cursor(f)
    #
    #         sample_rate_split = attrs["timebase"].split(" ")
    #         assert(sample_rate_split[1] == "hz")
    #         sample_rate = float(sample_rate_split[0]) * pq.Hz  # sample_rate 50.0 hz
    #
    #         duration = float(attrs["duration"]) * pq.s
    #         num_inp_samples = int(attrs["num_inp_samples"])
    #         bytes_per_timestamp = int(attrs["bytes_per_timestamp"])
    #         bytes_per_type = int(attrs["bytes_per_type"])
    #         bytes_per_value = int(attrs["bytes_per_value"])
    #
    #         timestamp_dtype = ">i" + str(bytes_per_timestamp)
    #         type_dtype = "S"
    #         value_dtype = 'i1'
    #
    #         # read data:
    #         dtype = np.dtype([("t", (timestamp_dtype, 1)),
    #                           ("event_types", (type_dtype, bytes_per_type)),
    #                           ("values", (value_dtype, bytes_per_value))])
    #
    #         # num_inp_samples cannot be used because it
    #         # does not include outputs ('O').
    #         # We need to find the length of the data manually
    #         # by seeking to the end of the file and subtracting
    #         # the position at data_start.
    #         current_position = f.tell()
    #         f.seek(-data_end_length, os.SEEK_END)
    #         end_position = f.tell()
    #         data_byte_count = end_position - current_position
    #         data_count = int(data_byte_count / dtype.itemsize)
    #         assert_end_of_data(f)
    #
    #         # seek back to data start and read the newly calculated
    #         # number of samples
    #         f.seek(current_position, os.SEEK_SET)
    #
    #         data = np.fromfile(f, dtype=dtype, count=data_count)
    #
    #         assert_end_of_data(f)
    #         times = data["t"].astype(float) / sample_rate
    #
    #         inp_data = InpData(
    #             duration=duration,
    #             times=times,
    #             event_types=data["event_types"].astype(str),
    #             values=data["values"],
    #         )
    #
    #     self._inp_data = inp_data
    #     self._inp_data_dirty = False

    # def parse_attrs(text):
    #     attrs = {}
    #
    #     for line in text.split("\n"):
    #         line = line.strip()
    #
    #         if len(line) == 0:
    #             continue
    #
    #         line_splitted = line.split(" ", 1)
    #
    #         name = line_splitted[0]
    #         attrs[name] = None
    #
    #         if len(line_splitted) > 1:
    #             try:
    #                 attrs[name] = int(line_splitted[1])
    #             except:
    #                 try:
    #                     attrs[name] = float(line_splitted[1])
    #                 except:
    #                     attrs[name] = line_splitted[1]
    #     return attrs
    #
    #
    # def parse_header_and_leave_cursor(file_handle):
    #     header = ""
    #     while True:
    #         search_string = "data_start"
    #         byte = file_handle.read(1)
    #         header += str(byte, 'latin-1')
    #
    #         if not byte:
    #             raise IOError("Hit end of file before '" + search_string + "' found.")
    #
    #         if header[-len(search_string):] == search_string:
    #             break
    #
    #     attrs = parse_attrs(header)
    #
    #     return attrs
    #
    #
    # def assert_end_of_data(file_handle):
    #     remaining_data = str(file_handle.read(), 'latin1')
    #     assert(remaining_data.strip() == "data_end")
