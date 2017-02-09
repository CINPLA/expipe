import numpy as np
import matplotlib.pyplot as plt
import quantities as pq
from ..misc.plot import simpleaxis


def plot_spike_histogram(trials, color='b', ax=None, binsize=None, bins=100,
                         output='counts', edgecolor='k', alpha=1., ylabel=True,
                         dim='s'):
    """
    Raster plot of trials

    Parameters
    ----------
    trials : list of neo.SpikeTrains
    color : color of histogram
    ax : matplotlib axes
    output : accepts 'counts' or 'rate',
    binsize : binsize of spike rate histogram, default None, if not None then
              bins are overridden
    bins : number of bins, defaults to 100 if binsize is None
    ylabel : bool
    Returns
    -------
    out : axes
    """
    assert isinstance(ylabel, bool)
    from elephant.statistics import time_histogram
    t_start = trials[0].t_start.rescale(dim)
    t_stop = trials[0].t_stop.rescale(dim)
    if binsize is None:
        binsize = (abs(t_start)+abs(t_stop))/float(bins)
    else:
        binsize = binsize.rescale(dim)
    time_hist = time_histogram(trials, binsize, t_start=t_start,
                               t_stop=t_stop, output=output, binary=False)
    bs = np.arange(t_start.magnitude, t_stop.magnitude, binsize.magnitude)
    if output == 'counts' and ylabel:
        ax.set_ylabel('count')
    elif output == 'rate':
        time_hist = time_hist.rescale('Hz')
        if ylabel:
            ax.set_ylabel('rate [%s]' % time_hist.dimensionality)
    elif output == 'mean' and ylabel:
        ax.set_ylabel('mean count')
    ax.bar(bs[0:len(time_hist)], time_hist.magnitude, width=bs[1]-bs[0],
           edgecolor=edgecolor, facecolor=color, alpha=alpha)
    return ax


def plot_isi_hist(sptr, alpha=1, ax=None, binsize=2*pq.ms,
                  time_limit=100*pq.ms, color='b'):
    """
    Bar plot of interspike interval (ISI) histogram

    Parameters
    ----------
    sptr : neo.SpikeTrain
    color : color of histogram
    ax : matplotlib axes
    alpha : opacity
    binsize : binsize of spike rate histogram, default 30 ms
    time_limit : end time of histogram x limit

    Returns
    -------
    out : axes
    """
    if ax is None:
        fig, ax = plt.subplots()
    spk_isi = np.diff(sptr)*sptr.units
    binsize.units = 's'
    time_limit.units = 's'
    ax.hist(spk_isi, bins=np.arange(0., time_limit.magnitude,
            binsize.magnitude), normed=True, alpha=alpha, color=color)
    ax.set_xlabel('$Interspike\, interval\, \Delta t \,[ms]$')
    binsize.units = 'ms'
    ax.set_ylabel('$Proportion\, of\, intervals\, (%.f ms\, bins)$' % binsize)
    return ax


def plot_autocorr(sptr, title='', color='k', edgecolor='k', ax=None, **kwargs):
    par = {'corr_bin_width': 0.01*pq.s,
           'corr_limit': 1.*pq.s}
    if kwargs:
        par.update(kwargs)
    from .correlogram import correlogram
    if ax is None:
        fig, ax = plt.subplots()
    bin_width = par['corr_bin_width'].rescale('s').magnitude
    limit = par['corr_limit'].rescale('s').magnitude
    count, bins = correlogram(t1=sptr.times.magnitude, t2=None,
                              bin_width=bin_width, limit=limit,  auto=True)
    ax.bar(bins[:-1] + bin_width / 2., count, width=bin_width, color=color,
            edgecolor=edgecolor)
    ax.set_xlim([-limit, limit])
    ax.set_title(title)


def hist_spike_rate(sptr, ax, sigma):
    '''
    deprecated
    calculates spike rate histogram and plots to given axis
    '''
    nbins = sptr.max() / sigma
    ns, bs = np.histogram(sptr, nbins)
    ax.bar(bs[0:-1], ns/sigma, width=bs[1]-bs[0])
    ax.set_ylabel('spikes/s')
