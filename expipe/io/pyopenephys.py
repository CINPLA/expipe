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

#TODO: add extensive funciton descrption and verbose option for prints

from __future__ import division
from __future__ import print_function
from __future__ import with_statement

import sys
import quantities as pq
import os
import os.path as op
import glob
import numpy as np
import xml.etree.ElementTree as ET
from xmljson import yahoo as yh
from datetime import datetime
from six import exec_

# TODO related files
# TODO append .continuous files directly to file and memory map in the end
# TODO ChannelGroup class - needs probe file
# TODO Channel class


def _read_python(path):
    path = op.realpath(op.expanduser(path))
    assert op.exists(path)
    with open(path, 'r') as f:
        contents = f.read()
    metadata = {}
    exec_(contents, {}, metadata)
    metadata = {k.lower(): v for (k, v) in metadata.items()}
    return metadata


class Channel:
    def __init__(self, index, name, gain, channel_id):
        self.index = index
        self.id = channel_id
        self.name = name
        self.gain = gain


class ChannelGroup:
    def __init__(self, channel_group_id, filename, channels, attrs):
        self.attrs = attrs
        self.filename = filename
        self.channel_group_id = channel_group_id
        self.channels = channels

    def __str__(self):
        return "<OpenEphys channel_group {}: channel_count: {}>".format(
            self.channel_group_id, len(self.channels)
        )


class AnalogSignal:
    def __init__(self, channel_id, signal, sample_rate):
        self.signal = signal
        self.channel_id = channel_id
        self.sample_rate = sample_rate

    @property
    def times(self):
        nsamples = self.signal.shape[1]
        return np.arange(nsamples) / self.sample_rate

    def __str__(self):
        return "<OpenEphys analog signal:shape: {}, sample_rate: {}>".format(
            self.signal.shape, self.sample_rate
        )


class TrackingData:
    def __init__(self, times, positions, attrs):
        self.attrs = attrs
        self.times = times
        self.positions = positions

    def __str__(self):
        return "<OpenEphys tracking data: times shape: {}, positions shape: {}>".format(
            self.times.shape, self.positions.shape
        )


class File:
    """
    Class for reading experimental data from an OpenEphys dataset.
    """
    def __init__(self, foldername, probefile):
        # TODO assert probefile is a probefile
        self._absolute_foldername = foldername
        self._path, relative_foldername = os.path.split(foldername)
        self._analog_signals_dirty = True
        self._channel_groups_dirty = True
        self._tracking_dirty = True
        filenames = [f for f in os.listdir(self._absolute_foldername)]
        if not any(sett == 'settings.xml' for sett in filenames):
            raise ValueError("'setting.xml' should be in the folder")

        self.rhythm = False
        self.rhythmID = []
        rhythmRates = np.array([1., 1.25, 1.5, 2, 2.5, 3, 3.33, 4., 5., 6.25,
                                8., 10., 12.5, 15., 20., 25., 30.])
        self.osc = False
        self.oscID = []
        self.oscPort = []
        self.oscAddress = []
        self.tracking_timesamples_rate = 1000 * 1000. * pq.Hz

        # TODO: support for multiple exp in same folder
        print('Reading settings.xml...')
        with open(op.join(self._absolute_foldername, 'settings.xml')) as f:
            xmldata = f.read()
            self.settings = yh.data(ET.fromstring(xmldata))['SETTINGS']
        self._start_datetime = datetime.strptime(self.settings['INFO']['DATE'],
                                                 '%d %b %Y %H:%M:%S')
        self._channel_info = {}
        self.nchan = 0
        FPGA_count = 0
        for sigchain in self.settings['SIGNALCHAIN']:
            for processor in sigchain['PROCESSOR']:
                if processor['name'] == 'Sources/Rhythm FPGA':
                    assert FPGA_count == 0
                    FPGA_count += 1
                    # TODO can there be multiple FPGAs ?
                    self._channel_info['channels'] = []
                    self._channel_info['gain'] = []
                    self.rhythm = True
                    self.rhythmID = processor['NodeId']
                    gain = {ch['number']: ch['gain']
                            for chs in processor['CHANNEL_INFO'].values()
                            for ch in chs}
                    for chan in processor['CHANNEL']:
                        if chan['SELECTIONSTATE']['record'] == '1':
                            self.nchan += 1
                            chnum = chan['number']
                            self._channel_info['channels'].append(int(chnum))
                            self._channel_info['gain'].append(float(gain[chnum]))
                        sampleIdx = int(processor['EDITOR']['SampleRate'])-1
                        self.sample_rate = rhythmRates[sampleIdx] * 1000. * pq.Hz
                    print('RhythmFPGA with ', self.nchan, ' channels. NodeId: ', self.rhythmID)
                if processor['name'] == 'Sources/OSC Port':
                    self.osc = True
                    self.oscID.append(processor['NodeId'])
                    self.oscPort.append(processor['EDITOR']['OSCNODE']['port'])
                    self.oscAddress.append(processor['EDITOR']['OSCNODE']['address'])
                    print('OSC Port. NodeId: ', self.oscID)
        # Check openephys format
        if self.settings['CONTROLPANEL']['recordEngine'] == 'OPENEPHYS':
            self._format = 'openephys'
        elif self.settings['CONTROLPANEL']['recordEngine'] == 'RAWBINARY':
            self._format = 'binary'
        else:
            self._format = None
        print('Decoding data from ', self._format, ' format')

        self._duration = (self.analog_signals[0].signal.shape[1] /
                          self.analog_signals[0].sample_rate)

        sort_idx = np.argsort(self._channel_info['channels'])
        self._channel_info['channels'] = np.array(self._channel_info['channels'])[sort_idx]
        self._channel_info['gain'] = np.array(self._channel_info['gain'])[sort_idx]
        self._channel_group_info = _read_python(probefile)['channel_groups']
        for group in self._channel_group_info.values():
            group['filemap'] = []
            group['gain'] = []
            for chan in group['channels']:
                idx = self._channel_info['channels'].tolist().index(chan)
                group['filemap'].append(idx)
                group['gain'].append(self._channel_info['gain'][idx])

    @property
    def session(self):
        return op.split(self._absolute_foldername)[-1]

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

    def _read_channel_groups(self):
        self._channel_id_to_channel_group = {}
        self._channel_group_id_to_channel_group = {}
        self._channel_count = 0
        self._channel_groups = []
        for channel_group_id, channel_group_content in self._channel_group_info.items():
            num_chans = len(channel_group_content['channels'])
            self._channel_count += num_chans
            channels = []
            for idx, channel_id in enumerate(channel_group_content['filemap']):
                channel = Channel(
                    index=idx,
                    channel_id=channel_id,
                    name="channel_{}_channel_group_{}".format(channel_id,
                                                              channel_group_id),
                    gain=channel_group_content['gain'][idx]
                )
                channels.append(channel)

            channel_group = ChannelGroup(
                channel_group_id=channel_group_id,
                filename=None,#TODO,
                channels=channels,
                attrs=None #TODO
            )
            ana = self.analog_signals[0]
            analog_signals = []
            for channel in channels:
                analog_signals.append(AnalogSignal(signal=ana.signal[channel.id],
                                                   channel_id=channel.id,
                                                   sample_rate=ana.sample_rate))

            channel_group.analog_signals = analog_signals

            self._channel_groups.append(channel_group)
            self._channel_group_id_to_channel_group[channel_group_id] = channel_group

            for channel_id in channel_group_content['channels']:
                self._channel_id_to_channel_group[channel_id] = channel_group

        # TODO channel mapping to file
        self._channel_ids = np.arange(self._channel_count)
        self._channel_groups_dirty = False

    def _read_tracking(self):
        filenames = [f for f in os.listdir(self._absolute_foldername)]
        if self.osc is True and any('.eventsbinary' in f for f in filenames):
            posfile = [f for f in filenames if '.eventsbinary' in f][0]
            print('.eventsbinary: ', posfile)
            if sys.version_info > (3, 0):
                with open(op.join(self._absolute_foldername, posfile), "r", encoding='utf-8', errors='ignore') as fh:
                    self._read_tracking_events(fh)
            else:
                with open(op.join(self._absolute_foldername, posfile), "r") as fh:
                    self._read_tracking_events(fh)
        else:
            raise ValueError("'.eventsbinary' should be in the folder")

    def _read_tracking_events(self, fh):
        print('Reading positions...')

        #TODO consider NOT writing header from openephys
        header = readHeader(fh)

        if float(header['version']) < 0.4:
            raise Exception('Loader is only compatible with .events files with version 0.4 or higher')

        index = -1

        ids = np.array([])
        timestamps = np.array([])
        x = np.array([])
        y = np.array([])
        h = np.array([])
        w = np.array([])

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

            ids = np.append(ids, idcurr)
            timestamps = np.append(timestamps, tcurr)
            x = np.append(x, xcurr)
            y = np.append(y, ycurr)
            w = np.append(w, wcurr)
            h = np.append(h, hcurr)

            nread += 1

        print('Read position samples: ', nread)

        ts = timestamps / 1000.

        # Sort out different Sources
        if len(np.unique(ids)) == 1:
            print("Single tracking source")

            # adjust times with linear interpolation
            idx_non_zero = np.where(ts != 0)
            linear_coeff = np.polyfit(np.arange(len(ts))[idx_non_zero], ts[idx_non_zero], 1)
            times_fit = linear_coeff[0]*(np.arange(len(ts))) + linear_coeff[1]
            difft = np.diff(times_fit)
            avg_period = np.mean(difft)
            sample_rate_s = np.round(1./float(avg_period)) * pq.Hz

            # Camera (0,0) is top left corner -> adjust y
            coord_s = np.array([x, 1-y])
            ts_s = times_fit

            width_s = np.mean(w)
            height_s = np.mean(h)

            attrs = dict()
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
                ts_ = np.squeeze(ts[np.where(ids==ss)])

                # adjust times with linear interpolation
                idx_non_zero = np.where(ts_ != 0)
                linear_coeff = np.polyfit(np.arange(len(ts_))[idx_non_zero], ts_[idx_non_zero], 1)
                times_fit = linear_coeff[0]*(np.arange(len(ts_))) + linear_coeff[1]
                difft = np.diff(times_fit)
                avg_period = np.mean(difft)
                sample_rate_ = np.round(1./float(avg_period)) * pq.Hz

                # Camera (0,0) is top left corner -> adjust y
                coord_ = np.array([x_, 1-y_])
                coord_s.append(coord_)
                ts_s.append(times_fit)

                sample_rate_s.append(sample_rate_)
                width_s.append(np.mean(w_))
                height_s.append(np.mean(h_))

            attrs = dict()
            attrs['sample_rate'] = np.array(sample_rate_s)
            attrs['length_scale'] = np.array([width_s, height_s])
            attrs['nodeId'] = self.oscID
            attrs['port'] = self.oscPort
            attrs['address'] = self.oscAddress

        tracking_data = TrackingData(
            times=ts_s,
            positions=coord_s.T,
            attrs=attrs
        )

        self._tracking = tracking_data
        self._tracking_dirty = False

    def _read_analog_signals(self):
        # Check and decode files
        filenames = [f for f in os.listdir(self._absolute_foldername)]
        anas = np.array([])
        timestamps = np.array([])
        if self._format == 'binary':
            if self.rhythm is True:
                if any('.dat' in f for f in filenames):
                    datfile = [f for f in filenames if '.dat' in f][0]
                    print('.dat: ', datfile)
                    with open(op.join(self._absolute_foldername, datfile), "rb") as fh:
                        anas, nsamples = read_analog_binary_signals(fh, self.nchan)
                else:
                    raise ValueError("'.dat' should be in the folder")
            else:
                print('No rhythm FPGA data')
        elif self._format == 'openephys':
            # Find continuous CH data
            contFiles = [f for f in os.listdir(self._absolute_foldername) if 'continuous' in f and 'CH' in f]
            contFiles = sorted(contFiles)
            if len(contFiles) != 0:
                print('Reading all channels')
                for f in contFiles:
                    fullpath = op.join(self._absolute_foldername, f)
                    sig = read_analog_continuous_signal(fullpath)
                    if anas.shape[0] < 1:
                        anas = sig['data'][None, :]
                    else:
                        if sig['data'].size == anas[-1].size:
                            anas = np.append(anas, sig['data'][None, :], axis=0)
                        else:
                            raise Exception('Channels must have the same number of samples')

                anas = np.array(anas)
                print('Done!')

        self._analog_signals = [AnalogSignal(
            channel_id=range(anas.shape[0]),
            signal=anas,
            sample_rate=self.sample_rate
        )]
        self._analog_signals_dirty = False

    def _create_analog_timestamps(self, messagefile, nsamples):
        with open(op.join(self._absolute_foldername, messagefile)) as fm:
            lines = fm.readlines()
            if any('start time:' in l for l in lines):
                start = [l for l in lines if 'start time:' in l][0]
                s = start.split()
                start_time = float(int(s[0]))/self.sample_rate

                self._timestamps = np.arange(nsamples)/self.sample_rate + start_time
            else:
                raise Exception('eventsmessages file should be in the same folder')


def read_analog_binary_signals(filehandle, numchan):

    numchan=int(numchan)

    nsamples = os.fstat(filehandle.fileno()).st_size / (numchan*2)
    print('Estimated samples: ', int(nsamples))

    samples = np.memmap(filehandle, np.dtype('i2'), mode='r',
                        shape=(nsamples, numchan))
    samples = np.transpose(samples)

    return samples, nsamples


def read_analog_continuous_signal(filepath, dtype=float, verbose=False,
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
        header = readHeader(f)
        record_length_bytes = 2 * header['blockLength'] + 22
        fileLength = os.fstat(f.fileno()).st_size
        n_records = get_number_of_records(filepath)

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
                raise IOError('Found corrupted record in block')

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


'''from OpenEphys.py'''
def readHeader(fh):
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


def get_number_of_records(filepath):
    # Open the file
    with file(filepath, 'rb') as f:
        # Read header info
        header = readHeader(f)

        # Get file length
        fileLength = os.fstat(f.fileno()).st_size

        # Determine the number of records
        record_length_bytes = 2 * header['blockLength'] + 22
        n_records = int((fileLength - 1024) / record_length_bytes)
        # if (n_records * record_length_bytes + 1024) != fileLength:
        #     print("file does not divide evenly into full records")
        #     # raise IOError("file does not divide evenly into full records")

    return n_records
