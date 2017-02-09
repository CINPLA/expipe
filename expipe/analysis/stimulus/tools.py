import numpy as np
import quantities as pq
from ..misc.tools import find_first_peak, is_quantities


def rate_latency(trials=None, epo=None, unit=None, t_start=None, t_stop=None,
                 kernel=None, search_stop=None, sampling_period=None):
    assert trials != unit
    import neo
    import elephant
    if trials is None:
        trials = make_spiketrain_trials(epo=epo, unit=unit, t_start=t_start,
                                        t_stop=t_stop)
    else:
        t_start = trials[0].t_start
        t_stop = trials[0].t_stop
        if search_stop is None:
            search_stop = t_stop
    trial = neo.SpikeTrain(times=np.array([st for trial in trials
                                           for st in trial.times.rescale('s')])*pq.s,
                           t_start=t_start, t_stop=t_stop)
    rate = elephant.statistics.instantaneous_rate(trial, sampling_period,
                                                  kernel=kernel, trim=True)/len(trials)
    rate_mag = rate.rescale('Hz').magnitude.reshape(len(rate))
    if not any(rate_mag):
        return np.nan, rate
    else:
        mask = (rate.times > 0*pq.ms) & (rate.times < 250*pq.ms)
        spont_mask = (rate.times > -250*pq.ms) & (rate.times < 0*pq.ms)
        # spk, ind = find_max_peak(rate_mag[mask])
        krit1 = rate_mag[mask].mean() + rate_mag[mask].std() > \
                rate_mag[spont_mask].mean() + rate_mag[spont_mask].std()
        spike_mask = (trial.times > 0*pq.ms) & (trial.times < search_stop)
        krit2 = len(trial.times[spike_mask])/search_stop.rescale('s') > 1.*pq.Hz
        if not krit1 and krit2:
            return np.nan, rate
        t0 = 0*pq.ms
        while t0 < search_stop:
            mask = (rate.times > t0) & (rate.times < search_stop)
            pk, ind = find_first_peak(rate_mag[mask])
            if len(pk) == 0:
                break
            krit3 = pk > rate_mag[mask].mean() + rate_mag[mask].std()
            krit4 = pk > 1.*pq.Hz
            krit5 = pk != 0
            lat_time = rate.times[mask][ind]
            assert len(lat_time) == 1
            if krit3 and krit4 and krit5:
                return lat_time, rate
            else:
                t0 = lat_time
        return np.nan, rate


def epoch_overview(epo, period, expected_num_epochs=None):
    '''
    Makes a new Epoch with start and stop time as first and last event in
    a burst of epochs, bursts are separated by > period + stim duration*2

    Parameters
    ----------
    epo : neo.Epoch

    Returns
    -------
    out : neo.Epoch
    '''
    is_quantities(period, dtype='scalar')
    if len(epo.times) == 1:
        return epo
    from neo import Epoch
    pause = np.diff(epo.times)
    pause = pause > period + np.median(epo.durations)*2
    start_ind = np.concatenate((np.array([1]), pause))
    stop_ind = np.concatenate((pause, np.array([1])))
    stop_times = epo.times[stop_ind == 1]
    start_times = epo.times[start_ind == 1]
    if expected_num_epochs is not None:
        assert len(start_times) == expected_num_epochs
    return Epoch(times=start_times,
                      durations=stop_times-start_times,
                      description=epo.description)


def print_epo(epo, N=20):
    '''
    Print the N first epochs

    Parameters
    ----------
    epo : neo.Epoch
    N : number of epochs to print

    Returns
    ------
    prints : print of epoch
    '''
    cnt = 0
    for i, t, d in zip(range(epo.times.size), epo.times, epo.durations):
        d.units = 'ms'
        p = epo.times[i+1]-t-d
        p.units = 'ms'
        print('%.2f %.2f %.2f %.2f' % (t, d, t+d, p))
        cnt += 1
        if cnt == N:
            break


def make_spiketrain_trials(epo, t_start, t_stop, unit=None, sptr=None):
    '''
    Makes trials based on an Epoch and given temporal bound

    Parameters
    ----------
    epo : neo.Epoch
    t_start : quantities.Quantity
        time before epochs
    t_stop : quantities.Quantity
        time after epochs
    unit : neo.Unit
    sptr : neo.SpikeTrain

    Returns
    -------
    out : list of neo.SpikeTrains
    '''
    from neo.core import SpikeTrain
    
    if t_start.ndim == 0:
        t_starts = t_start * np.ones(len(epo.times))
    else:
        t_starts = t_start
        assert len(epo.times) == len(t_starts), 'epo.times and t_starts have different size'

    if t_stop.ndim == 0:
        t_stops = t_stop * np.ones(len(epo.times))
    else:
        t_stops = epo.durations
        assert len(epo.times) == len(t_stops), 'epo.times and t_stops have different size'

    dim = 's'
    
    if sptr is None:
        assert unit is not None, 'unit and st cannot be both None'
        sptr = []
        for st in unit.spiketrains:
            sptr.append(st.rescale(dim).magnitude)
        sptr = np.array(st)*pq.s
    else:
        sptr = sptr.rescale(dim)
    trials = []
    for j, t in enumerate(epo.times.rescale(dim)):
        t_start = t_starts[j].rescale(dim)
        t_stop = t_stops[j].rescale(dim)
        spikes = []
        for spike in sptr[(t+t_start < sptr) & (sptr < t+t_stop)]:
            spikes.append(spike-t)
        trials.append(SpikeTrain(times=spikes*pq.s,
                                 t_start=t_start,
                                 t_stop=t_stop))
    return trials


def make_analog_trials(ana, epo, t_start, t_stop):
    '''
    Makes trials based on an Epoch and given temporal bound

    Parameters
    ----------
    epo : neo.Epoch
    t_start : quantities.Quantity
        time before epochs
    t_stop : quantities.Quantity
        time after epochs
    ana : neo.AnalogSignal

    Returns
    -------
    out : list of neo.AnalogSignal
    '''
    assert t_start != t_stop, 't_start cannot be equal to t_stop'
    from neo.core import AnalogSignal
    dim = 's'
    t_start = t_start.rescale(dim)
    t_stop = t_stop.rescale(dim)
    times = epo.times.rescale(dim)
    trials = []
    nsamp = int(abs(t_start - t_stop) * ana.sampling_rate)-1
    for j, t in enumerate(times):
        sig = ana.magnitude[(t+t_start <= ana.times) & (ana.times <= t+t_stop), :]
        trials.append(AnalogSignal(signal=sig[:nsamp, :]*ana.units,
                                   sampling_rate=ana.sampling_rate,
                                   t_start=t_start,
                                   t_stop=t_stop))
    return trials
