import numpy as np
import matplotlib.pyplot as plt
import quantities as pq
from ..misc.plot import simpleaxis


def plot_raster(trials, color="#3498db", lw=1, ax=None, marker='.', marker_size=10,
                ylabel='Trials', id_start=0, ylim=None, dim='s'):
    """
    Raster plot of trials

    Parameters
    ----------
    trials : list of neo.SpikeTrains
    color : color of spikes
    lw : line width
    ax : matplotlib axes

    Returns
    -------
    out : axes
    """
    from matplotlib.ticker import MaxNLocator
    if ax is None:
        fig, ax = plt.subplots()
    trial_id = []
    spikes = []
    for n, trial in enumerate(trials):  # TODO what about empty trials?
        n += id_start
        spikes.extend(trial.times.rescale(dim).magnitude)
        trial_id.extend([n]*len(trial.times))
    if marker_size is None:
        heights = 6000./len(trials)
        if heights < 0.9:
            heights = 1.  # min size
    else:
        heights = marker_size
    ax.scatter(spikes, trial_id, marker=marker, s=heights, lw=lw, color=color,
               edgecolors='face')
    if ylim is None:
        ax.set_ylim(-0.5, len(trials)-0.5)
    elif ylim is True:
        ax.set_ylim(ylim)
    else:
        pass
    y_ax = ax.axes.get_yaxis()  # Get X axis
    y_ax.set_major_locator(MaxNLocator(integer=True))
    t_start = trials[0].t_start.rescale(dim)
    t_stop = trials[0].t_stop.rescale(dim)
    ax.set_xlim([t_start, t_stop])
    ax.set_xlabel("Times ["+dim+"]")
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    return ax
