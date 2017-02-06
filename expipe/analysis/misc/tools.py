import neo
import numpy as np
import matplotlib.pyplot as plt
import quantities as pq
import pandas as pd
import os


def concatenate_spiketrains(sptrs):
    '''sptrs must be in a sorted order!!'''
    assert not isinstance(sptrs, neo.SpikeTrain)
    if len(sptrs) == 1:
        return sptrs[0]
    elif len(sptrs) == 0:
        raise ValueError('Recieved an empty list')
    from neo import SpikeTrain
    ts = sptrs[0].times.magnitude
    wf = sptrs[0].waveforms.magnitude
    t_stop = sptrs[0].t_stop
    t_start = sptrs[0].t_start
    sampling_rate = sptrs[0].sampling_rate
    left_sweep = sptrs[0].left_sweep
    for sptr in sptrs[1:]:
        assert all(ts < sptr.times.magnitude.max())
        ts = np.hstack([ts, sptr.times.magnitude])
        wf = np.vstack([wf, sptr.waveforms.magnitude])
        assert t_stop == sptr.t_stop and t_start == sptr.t_start
        assert sampling_rate == sptr.sampling_rate
        assert left_sweep == sptr.left_sweep
    return SpikeTrain(times=ts*sptr.times.units, waveforms=wf*sptr.waveforms.units,
                      t_stop=t_stop, t_start=t_start, left_sweep=sptr.left_sweep,
                      sampling_rate=sptr.sampling_rate)


def moving_average(vec, N):
    return np.convolve(vec, np.ones((N,)) / N, mode='full')[(N-1):]


def nested_dict2pandas_df(dictionary, depth=3, fcn=lambda inp: pd.Series(inp)):
    if depth == 3:
        reform = {(outerKey, midKey, innerKey): fcn(values)
                  for outerKey, midDict in dictionary.iteritems()
                  for midKey, innerDict in midDict.iteritems()
                  for innerKey, values in innerDict.iteritems()}
    elif depth == 2:
        reform = {(outerKey, innerKey): fcn(values)
                  for outerKey, innerDict in dictionary.iteritems()
                  for innerKey, values in innerDict.iteritems()}
    else:
        raise NotImplementedError
    return pd.DataFrame(reform)


def is_quantities(data, dtype='scalar'):
    """
    test if data is quantities

    Parameters
    ----------
    data : list
        data to test
    dtype : str
        in {"scalar", "vector"}
    """
    if not isinstance(data, list):
        data = [data]
    for d in data:
        if dtype == 'scalar':
            try:
                assert isinstance(d.units, pq.Quantity)
                assert d.shape in ((), (1, ))
            except:
                raise ValueError('data must be a scalar quantities value')
        if dtype == 'vector':
            try:
                assert isinstance(d.units, pq.Quantity)
                assert len(d.shape) == 1
            except:
                raise ValueError('data must be a 1d quantities.Quantity array')


def detect_peaks(image):
    """
    Takes an image and detect the peaks usingthe local maximum filter.
    Returns a boolean mask of the peaks (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)

    Obtained from http://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array
    """
    from scipy.ndimage.filters import maximum_filter
    from scipy.ndimage.morphology import (generate_binary_structure,
                                          binary_erosion)
    # define an 8-connected neighborhood
    neighborhood = generate_binary_structure(2, 2)

    # apply the local maximum filter; all pixel of maximal value
    # in their neighborhood are set to 1
    local_max = maximum_filter(image, footprint=neighborhood) == image
    # local_max is a mask that contains the peaks we are
    # looking for, but also the background.
    # In order to isolate the peaks we must remove the background from the mask

    # we create the mask of the background
    background = (image == 0)

    # a little technicality: we must erode the background in order to
    # successfully subtract it form local_max, otherwise a line will
    # appear along the background border (artifact of the local maximum filter)
    eroded_background = binary_erosion(background, structure=neighborhood,
                                       border_value=1)

    # we obtain the final mask, containing only peaks,
    # by removing the background from the local_max mask
    detected_peaks = local_max - eroded_background

    return detected_peaks


def normalize(x, mode='minmax'):
    '''
    Normalizes x ignoring nan with given mode

    Parameters
    ----------
    x : np.ndarray
    mode : str
        'minmax' or 'zscore'

    Returns
    -------
    minmax : x in [0,1]
    zscore : mean(x) = 0, std(x) in [0,1]
    '''
    x = np.array(x)
    if mode == 'minmax':
        xp = (x - np.nanmin(x))
        x = xp / np.nanmax(xp)
    elif mode == 'zscore':
        x = (x - np.nanmean(x)) / np.nanstd(x)
    return x


def find_max_peak(sig):
    from scipy import signal
    sig = np.reshape(sig, len(sig))
    pksind = signal.argrelmax(sig)
    if len(pksind[0]) == 0:
        return np.nan, np.nan
    pk = sig[pksind].max()
    ind = np.where(sig == pk)[0]
    return pk, ind


def find_first_peak(sig):
    from scipy import signal
    assert len(sig.shape) == 1
    sig = np.array(sig)
    times = np.linspace(0, 1, len(sig))
    pksind = signal.argrelmax(sig)
    if len(pksind[0]) == 0:
        return [], []
    tpk = times[pksind].min()
    ind = np.where(times == tpk)[0]
    pk = sig[ind]
    return pk, ind


def masked_corrcoef2d(a, v):
    import numpy.ma as ma
    a_ = np.reshape(a, (1, a.size))
    v_ = np.reshape(v, (1, v.size))
    corr = ma.corrcoef(a_, v_)
    return corr


def corrcoef2d(a, v):
    a_ = np.reshape(a, (1, a.size))
    v_ = np.reshape(v, (1, v.size))
    corr = np.corrcoef(a_, v_)
    return corr


def fftcorrelate2d(a, v, mode='full', normalize=False):
    from scipy.signal import fftconvolve
    if normalize:
        a_ = np.reshape(a, (1, a.size))
        v_ = np.reshape(v, (1, v.size))
        a = (a - np.mean(a_)) / (np.std(a_) * len(a_))
        v = (v - np.mean(v_)) / np.std(v_)
    corr = fftconvolve(a, np.fliplr(np.flipud(v)), mode=mode)
    return corr
