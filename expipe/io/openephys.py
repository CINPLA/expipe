import pyopenephys
import exdir
import shutil
import glob
import os
import quantities as pq
import numpy as np

from expipe.io.core import Filerecord
from expipe.io.core import user
from expipe import settings
import os.path as op

# TODO inform database about openephys data being included
# TODO SpikeTrain class - needs klusta stuff


def _prepare_exdir_file(exdir_file):
    general = exdir_file.require_group("general")
    subject = general.require_group("subject")
    processing = exdir_file.require_group("processing")
    epochs = exdir_file.require_group("epochs")

    return general, subject, processing, epochs


def convert(openephys_directory, exdir_path, probefile):
    openephys_file = pyopenephys.File(openephys_directory, probefile)
    exdir_file = exdir.File(exdir_path)
    dtime = openephys_file._start_datetime.strftime('%Y-%m-%dT%H:%M:%S')
    exdir_file.attrs['session_start_time'] = dtime
    exdir_file.attrs['session_duration'] = openephys_file._duration
    acquisition = exdir_file.require_group("acquisition")
    general = exdir_file.require_group("general")
    processing = exdir_file.require_group("processing")
    subject = general.require_group("subject")

    target_folder = op.join(acquisition.directory, openephys_file.session)
    acquisition.attrs["openephys_session"] = openephys_file.session

    shutil.copytree(openephys_file._absolute_foldername, target_folder)
    shutil.copy(probefile, op.join(target_folder, 'openephys_channelmap.prb'))

    print("Copied", openephys_file.session, "to", target_folder)


def load_openephys_file(exdir_file):
    acquisition = exdir_file["acquisition"]
    openephys_session = acquisition.attrs["openephys_session"]
    openephys_directory = op.join(acquisition.directory, openephys_session)
    probefile = op.join(openephys_directory, 'openephys_channelmap.prb')
    return pyopenephys.File(openephys_directory, probefile)


def _prepare_channel_groups(exdir_path):
    exdir_file = exdir.File(exdir_path)
    general, subject, processing, epochs = _prepare_exdir_file(exdir_file)
    openephys_file = load_openephys_file(exdir_file=exdir_file)
    exdir_channel_groups = []
    elphys = processing.require_group('electrophysiology')
    for openephys_channel_group in openephys_file.channel_groups:
        exdir_channel_group = elphys.require_group(
            "channel_group_{}".format(openephys_channel_group.channel_group_id))
        exdir_channel_groups.append(exdir_channel_group)
        channel_identities = np.array([ch.index for ch in openephys_channel_group.channels])
        exdir_channel_group.attrs['start_time'] = 0 * pq.s
        exdir_channel_group.attrs['stop_time'] = openephys_file._duration
        exdir_channel_group.attrs["electrode_identities"] = channel_identities
        exdir_channel_group.attrs["electrode_idx"] = channel_identities - channel_identities[0]
        exdir_channel_group.attrs['electrode_group_id'] = openephys_channel_group.channel_group_id
        # TODO else: test if attrs are the same
    return exdir_channel_groups, openephys_file


def generate_lfp(exdir_path):
    import scipy.signal as ss
    import copy
    exdir_channel_groups, openephys_file = _prepare_channel_groups(exdir_path)
    for channel_group, openephys_channel_group in zip(exdir_channel_groups,
                                                      openephys_file.channel_groups):
        lfp = channel_group.require_group("LFP")
        for channel in openephys_channel_group.channels:
                lfp_timeseries = lfp.require_group(
                    "LFP_timeseries_{}".format(channel.index)
                )
                analog_signal = openephys_channel_group.analog_signals[channel.index]
                # decimate
                target_rate = 1000 * pq.Hz
                signal = np.array(analog_signal.signal, dtype=float)
                signal *= channel.gain
                sample_rate = copy.copy(analog_signal.sample_rate)
                qs = [10, int((analog_signal.sample_rate / target_rate) / 10)]
                for q in qs:
                    signal = ss.decimate(signal, q=q, zero_phase=True)
                    sample_rate /= q
                t_stop = len(signal) / sample_rate
                assert round(t_stop, 2) == round(openephys_file._duration, 2), '{}, {}'.format(t_stop, openephys_file._duration)

                lfp_timeseries.attrs["num_samples"] = len(signal)
                lfp_timeseries.attrs["start_time"] = 0 * pq.s
                lfp_timeseries.attrs["stop_time"] = t_stop
                lfp_timeseries.attrs["sample_rate"] = sample_rate
                lfp_timeseries.attrs["electrode_identity"] = analog_signal.channel_id
                lfp_timeseries.attrs["electrode_idx"] = analog_signal.channel_id - openephys_channel_group.channel_group_id * 4
                lfp_timeseries.attrs['electrode_group_id'] = openephys_channel_group.channel_group_id
                data = lfp_timeseries.require_dataset("data", data=signal)
                data.attrs["num_samples"] = len(signal)
                # NOTE: In exdirio (python-neo) sample rate is required on dset #TODO
                data.attrs["sample_rate"] = sample_rate


def generate_spike_trains(exdir_path):
    import neo
    exdir_file = exdir.File(exdir_path)
    acquisition = exdir_file["acquisition"]
    openephys_session = acquisition.attrs["openephys_session"]
    openephys_directory = op.join(acquisition.directory, openephys_session)
    kwikfile = op.join(openephys_directory, openephys_session + '_klusta.kwik')
    kwikio = neo.io.KwikIO(filename=kwikfile)
    blk = kwikio.read_block()
    exdirio = neo.io.ExdirIO(exdir_path)
    exdirio.write_block(blk)
    

def generate_tracking(exdir_path):
    exdir_file = exdir.File(exdir_path)
    general, subject, processing, epochs = _prepare_exdir_file(exdir_file)
    openephys_file = load_openephys_file(exdir_file=exdir_file)
    tracking = processing.require_group('tracking')
    # NOTE openephys supports only one camera, but other setups might support several
    camera = tracking.require_group("camera_0")
    position = camera.require_group("Position")
    position.attrs['start_time'] = 0 * pq.s
    position.attrs['stop_time'] = openephys_file._duration
    tracking_data = openephys_file.tracking
    times, coords = tracking_data.times, tracking_data.positions
    print(times.shape, coords.shape)
    tracked_spots = int(coords.shape[1] / 2)  # 2 coordinates per spot
    for n in range(tracked_spots):
        led = position.require_group("led_" + str(n))
        data = coords[:, n * 2: n * 2 + 2]
        dset = led.require_dataset('data', data)
        dset.attrs['num_samples'] = len(data)
        dset = led.require_dataset("timestamps", times)
        dset.attrs['num_samples'] = len(times)
        led.attrs['start_time'] = 0 * pq.s
        led.attrs['stop_time'] = openephys_file._duration


class OpenEphysFilerecord(Filerecord):
    def __init__(self, action, filerecord_id=None):
        super().__init__(action, filerecord_id)

    def import_file(self, openephys_directory):
        convert(openephys_directory=openephys_directory,
                exdir_path=op.join(settings["data_path"], self.local_path))

    def generate_tracking(self):
        generate_tracking(self.local_path)

    def generate_lfp(self):
        generate_analog_signals(self.local_path)

    def generate_spike_trains(self):
        generate_spike_trains(self.local_path)

    def generate_inp(self):
        generate_inp(self.local_path)

if __name__ == '__main__':
    openephys_directory = '/home/mikkel/apps/expipe-project/openephystest/1753_2017-03-07_18-40-14_ephys-trackred'
    exdir_path = '/home/mikkel/apps/expipe-project/openephystest.exdir'
    probefile = '/home/mikkel/Dropbox/scripting/python/expipe/openephys_channelmap.prb'
    # convert(openephys_directory=openephys_directory,
    #         exdir_path=exdir_path,
    #         probefile=probefile)
    # generate_tracking(exdir_path)
    # generate_lfp(exdir_path)
    generate_spike_trains(exdir_path)
    # generate_inp(exdir_path)
