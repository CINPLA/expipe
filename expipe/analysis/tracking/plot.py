import neo
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import quantities as pq
from .fields import gridness, spatial_rate_map
from .head import *
from ..misc.plot import simpleaxis
import math


def plot_path(x, y, t, sptr=None, box_size=1*pq.m, color='grey', alpha=0.5,
              spike_color='r', rate_markersize=False, markersize=1.,
              animate=False, ax=None, title=''):
    """
    Plot path visited

    Parameters
    ----------
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    t : quantities.Quantity array in s
        1d vector of time at x, y positions
    sptr : neo.SpikeTrain
    box_size : quantities scalar
        size of spatial 2d square
    color : path color
    alpha : opacity of path
    spike_color : spike marker color
    rate_markersize : bool
        scale marker size to firing rate
    markersize : float
        size of spike marker
    animate : bool
    ax : matplotlib axes

    Returns
    -------
    out : ax
    """
    box_size = float(box_size.rescale('m').magnitude)
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, xlim=[0, box_size], ylim=[0, box_size],
                             aspect=1)
    if sptr is not None:
        spikes_in_bin, _ = np.histogram(sptr, t)
        is_spikes_in_bin = np.array(spikes_in_bin, dtype=bool)

        if rate_markersize:
            markersizes = spikes_in_bin[is_spikes_in_bin]*markersize
        else:
            markersizes = markersize*np.ones(is_spikes_in_bin.size)
    if animate:
        import time
        plt.show()
        for idx, x, y, active, msize in zip(range(len(x)), x, y):
            ax.plot(x, y, c=color, alpha=alpha)
            if sptr is not None:
                if is_spikes_in_bin[idx]:
                    ax.scatter(x, y, facecolor=spike_color, edgecolor=spike_color,
                               s=markersizes[idx])
            time.sleep(0.1)  # plt.pause(0.0001)
            plt.draw()
    else:
        ax.plot(x, y, c=color, alpha=alpha)
        if sptr is not None:
            ax.scatter(x[0:-1][is_spikes_in_bin], y[0:-1][is_spikes_in_bin],
                       facecolor=spike_color, edgecolor=spike_color,
                       s=markersizes)
    ax.set_title(title)
    ax.grid(False)
    return ax


def plot_head_direction_rate(sptr, ang_bins, rate_in_ang, projection='polar',
                             normalization=False, ax=None, color='k'):
    """


    Parameters
    ----------
    sptr : neo.SpikeTrain
    ang_bins : angular binsize
    rate_in_ang :
    projection : 'polar' or None
    normalization :
    group_name
    ax : matplotlib axes
    mask_unvisited : True: mask bins which has not been visited

    Returns
    -------
    out : ax
    """
    import math
    assert ang_bins.units == pq.degrees, 'ang_bins must be in degrees'
    if normalization:
        rate_in_ang = normalize(rate_in_ang, mode='minmax')
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection=projection)
    binsize = ang_bins[1]-ang_bins[0]
    if projection is None:
        ax.set_xticks(range(0, 360+60, 60))
        ax.set_xlim(0, 360)
    elif projection == 'polar':
        ang_bins = [math.radians(deg) for deg in ang_bins] * pq.radians
        binsize = math.radians(binsize) * pq.radians
        ax.set_xticks([0, np.pi])
    ax.bar(ang_bins, rate_in_ang, width=binsize, color=color)
    return ax


def plot_ratemap(x, y, t, sptr, binsize=0.05*pq.m, box_size=1*pq.m,
                 vmin=0, ax=None, mask_unvisited=True, convolve=True):
    """


    Parameters
    ----------
    x : 1d vector of x positions
    y : 1d vector of y positions
    t : 1d vector of time at x, y positions
    sptr : one neo.SpikeTrain
    binsize : size of spatial 2d square bins
    vmin : color min
    ax : matplotlib axes
    mask_unvisited : True: mask bins which has not been visited

    Returns
    -------
    out : axes
    """
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, xlim=[0, 1], ylim=[0, 1], aspect=1)

    rate_map = spatial_rate_map(x, y, t, sptr, binsize=binsize,
                                 mask_unvisited=mask_unvisited, box_size=box_size,
                                 convolve=convolve)
    ax.imshow(rate_map, interpolation='none', origin='lower',
              extent=(0, 1, 0, 1), vmin=vmin)
    ax.set_title('%.2f Hz' % np.nanmax(rate_map))
    ax.grid(False)
    return ax
