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
            print('Reading settings.xml...')
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
                        self._nsamples = self._read_analog_binary_signals(fh, self.nchan)
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
                if (sys.version_info > (3, 0)):
                    with open(join(self._absolute_foldername, posfile), "r", encoding='utf-8', errors='ignore') as fh:
                        self._read_tracking(fh)
                else:
                    with open(join(self._absolute_foldername, posfile), "r") as fh:
                        self._read_tracking(fh)


            else:
                raise ValueError("'.eventsbinary' should be in the folder")
        elif self._format == 'openephys':
            # Find continuous CH data
            contFiles = [f for f in os.listdir(self._absolute_foldername) if 'continuous' in f and 'CH' in f]
            contFiles = sorted(contFiles)

            anas = []

            if len(contFiles) != 0:
                for f in contFiles:
                    print('Loading: ', f)
                    fullpath = join(self._absolute_foldername, f)
                    sig = self._read_analog_continuous_signal(fullpath)
                    try:
                        anas.append(sig['data'])
                        ts = sig['timestamps']
                    except:
                        print('Error in concatenating a recorded channel...')
                        pass
                anas = np.array(anas)

                if any('messages' in f for f in filenames):
                    messagefile = [f for f in filenames if 'messages' in f][0]
                    self._nsamples = anas.shape[1]
                    self._create_analog_timestamps(messagefile, self._nsamples)

                self._analog_signals = anas
                self._analog_signals_dirty = False


        #TODO add openephys format


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


    def _read_tracking(self, fh):
        # tracking_data = {}

        print('Reading positions...')

        header = self._readHeader(fh)

        if float(header['version']) < 0.4:
            raise Exception('Loader is only compatible with .events files with version 0.4 or higher')

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
        # times are in ms
        ts_ = timestamps[:index] / 1000.

        #TODO clean nans

        # Sort out different Sources
        if len(np.unique(ids)) == 1:
            print("Single tracking source")
            sources = np.unique(ids)
            coord_s, w_s, h_s, ts_s = [], [], [], []
            sample_rate_s, width_s, height_s = [], [], []

            # adjust times with linear interpolation
            idx_non_zero = np.where(ts_ != 0)
            linear_coeff = np.polyfit(np.arange(len(ts_))[idx_non_zero], ts_[idx_non_zero], 1)
            times_fit = linear_coeff[0]*(np.arange(len(ts_))) + linear_coeff[1]
            difft = np.diff(times_fit)
            avg_period = np.mean(difft)
            sample_rate_s = np.round(1./float(avg_period)) * pq.Hz

            coord_s = np.array([x, y])
            ts_s = times_fit

            width_s = np.mean(w)
            height_s = np.mean(h)

            attrs = {}
            attrs['sample_rate'] = sample_rate_s
            attrs['length_scale'] = np.array([width_s, height_s])

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
            attrs['length_scale'] = np.array([width_s, height_s])
            # xsize = w
            # ysize = h
            # length_scale = [xsize, ysize, xsize, ysize]
            # attrs['length_scale'] = length_scale

        # TODO adjust ref system

        tracking_data = TrackingData(
            times=ts_s,
            positions=coord_s,
            attrs=attrs
        )

        self._tracking = tracking_data
        self._tracking_dirty = False


    def _read_analog_binary_signals(self, filehandle, numchan):

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

    def _read_analog_continuous_signal(self, filepath, dtype=float, verbose=False,
        start_record=None, stop_record=None, ignore_last_record=True):
        """Load continuous data from a single channel in the file `filepath`.

        This is intended to be mostly compatible with the previous version.
        The differences are:
        - Ability to specify start and stop records
        - Converts numeric data in the header from string to numeric data types
        - Does not rely on a predefined maximum data size
        - Does not necessarily drop the last record, which is usually incomplete
        - Uses the block length that is specified in the header, instead of
            hardcoding it.
        - Returns timestamps and recordNumbers as int instead of float
        - Tests the record metadata (N and record marker) for internal consistency

        The OpenEphys file format breaks the data stream into "records",
        typically of length 1024 samples. There is only one timestamp per record.

        Args:
            filepath : string, path to file to load
            dtype : float or np.int16
                If float, then the data will be multiplied by bitVolts to convert
                to microvolts. This increases the memory required by 4 times.
            verbose : whether to print debugging messages
            start_record, stop_record : indices that control how much data
                is read and returned. Pythonic indexing is used,
                so `stop_record` is not inclusive. If `start` is None, reading
                begins at the beginning; if `stop` is None, reading continues
                until the end.
            ignore_last_record : The last record in the file is almost always
                incomplete (padded with zeros). By default it is ignored, for
                compatibility with the old version of this function.

        Returns: dict, with following keys
            data : array of samples of data
            header : the header info, as returned by readHeader
            timestamps : the timestamps of each record of data that was read
            recordingNumber : the recording number of each record of data that
                was read. The length is the same as `timestamps`.
        """
        if dtype not in [float, np.int16]:
            raise ValueError("Invalid data type. Must be float or np.int16")

        if verbose:
            print("Loading continuous data from " + filepath)

        """Here is the OpenEphys file format:
        'each record contains one 64-bit timestamp, one 16-bit sample
        count (N), 1 uint16 recordingNumber, N 16-bit samples, and
        one 10-byte record marker (0 1 2 3 4 5 6 7 8 255)'
        Thus each record has size 2*N + 22 bytes.
        """
        # This is what the record marker should look like
        spec_record_marker = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 255])

        # Lists for data that's read
        timestamps = []
        recordingNumbers = []
        samples = []
        samples_read = 0
        records_read = 0

        # Open the file
        with file(filepath, 'rb') as f:
            # Read header info, file length, and number of records
            header = self._readHeader(f)
            record_length_bytes = 2 * header['blockLength'] + 22
            fileLength = os.fstat(f.fileno()).st_size
            n_records = self._get_number_of_records(filepath)

            # Use this to set start and stop records if not specified
            if start_record is None:
                start_record = 0
            if stop_record is None:
                stop_record = n_records

            # We'll stop reading after this many records are read
            n_records_to_read = stop_record - start_record

            # Seek to the start location, relative to the current position
            # right after the header.
            f.seek(record_length_bytes * start_record, 1)

            # Keep reading till the file is finished
            while f.tell() < fileLength and records_read < n_records_to_read:
                # Skip the last record if requested, which usually contains
                # incomplete data
                if ignore_last_record and f.tell() == (
                    fileLength - record_length_bytes):
                    break

                # Read the timestamp for this record
                # litte-endian 64-bit signed integer
                timestamps.append(np.fromfile(f, np.dtype('<i8'), 1))

                # Read the number of samples in this record
                # little-endian 16-bit unsigned integer
                N = np.fromfile(f, np.dtype('<u2'), 1).item()
                if N != header['blockLength']:
                    raise IOError('Found corrupted record in block ' +
                        str(recordNumber))

                # Read and store the recording numbers
                # big-endian 16-bit unsigned integer
                recordingNumbers.append(np.fromfile(f, np.dtype('>u2'), 1))

                # Read the data
                # big-endian 16-bit signed integer
                data = np.fromfile(f, np.dtype('>i2'), N)
                if len(data) != N:
                    raise IOError("could not load the right number of samples")

                # Optionally convert dtype
                if dtype == float:
                    data = data * header['bitVolts']

                # Store the data
                samples.append(data)

                # Extract and test the record marker
                record_marker = np.fromfile(f, np.dtype('<u1'), 10)
                if np.any(record_marker != spec_record_marker):
                    raise IOError("corrupted record marker at record %d" %
                        records_read)

                # Update the count
                samples_read += len(samples)
                records_read += 1

        # Concatenate results, or empty arrays if no data read (which happens
        # if start_sample is after the end of the data stream)
        res = {'header': header}
        if samples_read > 0:
            res['timestamps'] = np.concatenate(timestamps)
            res['data'] = np.concatenate(samples)
            res['recordingNumber'] = np.concatenate(recordingNumbers)
        else:
            res['timestamps'] = np.array([], dtype=np.int)
            res['data'] = np.array([], dtype=dtype)
            res['recordingNumber'] = np.array([], dtype=np.int)

        return res



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

    '''from OpenEphys.py'''
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

    def _get_number_of_records(self, filepath):
        # Open the file
        with file(filepath, 'rb') as f:
            # Read header info
            header = self._readHeader(f)

            # Get file length
            fileLength = os.fstat(f.fileno()).st_size

            # Determine the number of records
            record_length_bytes = 2 * header['blockLength'] + 22
            n_records = int((fileLength - 1024) / record_length_bytes)
            if (n_records * record_length_bytes + 1024) != fileLength:
                print("file does not divide evenly into full records")
                # raise IOError("file does not divide evenly into full records")

        return n_records
