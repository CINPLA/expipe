import numpy as np
import quantities as pq


def average_rate(trails):
    '''
    calculates the mean firing rate for every orientation

    Parameters
    ----------
    trails : neo.SpikeTrains
        list of spike trains

    Returns
    -------
    avg_rate : array
        average rates
    orients : array
        sorted stimulus orientations
    '''
    from elephant.statistics import mean_firing_rate
    import collections as collect
    spike_count_rate = collect.defaultdict(list)

    for trail in trails:
        orient = float(list(trail.annotations.values())[0])
        rate = mean_firing_rate(trail, trail.t_start, trail.t_stop)
        spike_count_rate[orient].append(rate)

    avg_rate = np.zeros(len(spike_count_rate))
    orients = np.zeros(len(spike_count_rate))

    for i, orient in enumerate(spike_count_rate):
        avg_rate[i] = np.mean(spike_count_rate[orient])
        orients[i] = orient

    sorted_indices = np.argsort(orients)
    orients = orients[sorted_indices] * pq.deg
    avg_rate = avg_rate[sorted_indices] * 1./pq.s
    
    return avg_rate, orients


def wrap_angle(angle, wrap_range=360.):
    '''
    wraps angle in to the interval [0, wrap_range]
    ----------
    angle : numpy.array/float
        input array/float
    wrap_range : float
        wrap range (eg. 360 or 2pi)

    Returns
    -------
    out : numpy.array/float
        angle in interval [0, wrap_range]

    '''
    return angle - wrap_range * np.floor(angle/float(wrap_range))


def compute_selectivity_index(av_rates, orients, selectivity_type):
    '''
    calculates selectivity index (orientation or direction)
    Parameters
    ----------
    av_rates : numpy.array
        array of mean firing rates
    orients : numpy.array
        array of orientations
    selectivity_type : str
        selectivity type osi/dsi

    Returns
    -------
    out : float
        preferred orientation
    out : float
        selectivity index
    '''
    preferred = np.where(av_rates == av_rates.max())
    null_angle = wrap_angle(orients[preferred] + 180*pq.deg, wrap_range=360.)

    null = np.where(orients == null_angle)
    if len(null[0]) == 0:
        raise Exception("orientation not found: "+str(null_angle))

    if(selectivity_type == "dsi"):
        index = 1. - av_rates[null] / av_rates[preferred]
        return orients[preferred], index

    elif(selectivity_type == "osi"):
        orth_angle_p = wrap_angle(orients[preferred] + 90*pq.deg, wrap_range=360.)
        orth_angle_n = wrap_angle(orients[preferred] - 90*pq.deg, wrap_range=360.)
        orth_p = np.where(orients == orth_angle_p)
        orth_n = np.where(orients == orth_angle_n)

        if len(orth_p[0]) == 0:
            raise Exception("orientation not found: " BaseException+str(orth_angle_p))
        if len(orth_n[0]) == 0:
            raise Exception("orientation not found: " + str(orth_angle_n))

        index = 1. - (av_rates[orth_p] + av_rates[orth_n]) / (av_rates[preferred]+av_rates[null])
        return orients[preferred], index

    else:
        raise ValueError("unknown selectivity type: ", str(selectivity_type), " options: osi, dsi")
        

def make_stim_off_epoch_array(epo, include_boundary=True):
    '''
    Makes EpochArray of stimulus off periods

    Parameters
    ----------
    epo : neo.EpochArray
        EpochArray array of stimulus periods

    include_boundary : bool
        include initial point


    Returns
    -------
    out : neo.EpochArray
        EpochArray array with stimulus off periods

    '''
    from neo.core import EpochArray
    times = epo.times[:-1] + epo.durations[:-1]
    durations = epo.times[1:] - times

    if(include_boundary):
        times = np.append([0], times)*pq.s
        durations = np.append(epo.times[0], durations)*pq.s

    return EpochArray(times=times, durations=durations, labels=[np.NAN]*len(times))
