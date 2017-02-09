import neo
import numpy as np
import matplotlib.pyplot as plt
import quantities as pq
from .tools import *
from ..misc.plot import simpleaxis
from ..statistics.plot import (plot_spike_histogram)
from ..general.plot import (plot_raster)
from ..statistics.tools import (fano_factor_linregress)


def plot_psth(epo=None, t_start=None, t_stop=None, trials=None, unit=None,
              sptr=None, output='counts', binsize=None, bins=100, fig=None,
              color='b', title='plot_psth', stim_color='b', edgecolor='k',
              alpha=.2, label='stim on', legend_loc=1, legend_style='patch',
              axs=None, hist_ylabel=True, rast_ylabel='trials', dim='s',
              ylim=None):
    """
    Visualize clustering on amplitude at detection point

    Parameters
    ----------
    unit : one or several entire spiketrains
    sptr : neo.SpikeTrain
    trials : list of cut neo.SpikeTrains with same number of recording channels
    color : color of spikes
    title : figure title
    fig : matplotlib figure
    axs : matplotlib axes (must be 2)
    legend_loc : 'outside' or matplotlib standard loc
    legend_style : 'patch' or 'line'

    Returns
    -------
    out : fig
    """
    if fig is None and axs is None:
        fig, (ax, ax2) = plt.subplots(2, 1, sharex=True)
    elif fig is not None and axs is None:
        ax = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2, sharex=ax)
    else:
        assert len(axs) == 2
        ax, ax2 = axs
    if trials is None:
        assert unit is not None or sptr is not None
        assert epo is not None and t_start is not None and t_stop is not None
        trials = make_spiketrain_trials(epo=epo, t_start=t_start, t_stop=t_stop,
                                        unit=unit, sptr=sptr)
    plot_spike_histogram(trials, color=color, ax=ax, output=output,
                         binsize=binsize, bins=bins, edgecolor=edgecolor,
                         ylabel=hist_ylabel, dim=dim)
    if ylim is not None:
        ax.set_ylim(ylim)
    plot_raster(trials, color=color, ax=ax2, ylabel=rast_ylabel, dim=dim)
    if legend_style == 'patch':
        stim_stop = epo.durations.rescale(dim).magnitude.mean()
        import matplotlib.patches as mpatches
        line = mpatches.Patch([], [], color=stim_color, label=label, alpha=alpha)
    elif legend_style == 'line':
        stim_stop = 0
        import matplotlib.lines as mlines
        line = mlines.Line2D([], [], color=stim_color, label=label)
    ax.axvspan(0, stim_stop, color=stim_color, alpha=alpha)
    ax2.axvspan(0, stim_stop, color=stim_color, alpha=alpha)
    if legend_loc == 'outside':
        ax.legend(handles=[line], bbox_to_anchor=(0., 1.02, 1., .102), loc=4,
                  ncol=2, borderaxespad=0.)
    else:
        ax.legend(handles=[line], loc=legend_loc, ncol=2, borderaxespad=0.)
    if title is not None:
        ax.set_title(title)
    return fig


def plot_stimulus_overview(unit_trials, t_start, t_stop, binsize, title=None,
                           axs=None):
    '''plots an overview of many units where each unit has several trials,
    output is rate, raster and fano factor'''
    dim = 's'
    t_start = t_start.rescale(dim)
    t_stop = t_stop.rescale(dim)
    binsize = binsize.rescale(dim)
    bins, means, varis, fano, trials = fano_factor_linregress(unit_trials=unit_trials,
                                                              t_start=t_start,
                                                              t_stop=t_stop,
                                                              binsize=binsize)
    mean = np.mean(means, axis=0)
    if axs is None:
        f = plt.figure()
        ax = f.add_subplot(3, 1, 1)
        ax2 = f.add_subplot(3, 1, 2)
        ax3 = f.add_subplot(3, 1, 3)
    else:
        ax, ax2, ax3 = axs
    if title is not None:
        ax.set_title(title)
    ax.bar(bins[0:-1], mean/binsize, width=bins[1]-bins[0])
    ax.set_xlim(t_start, t_stop)
    ax.set_ylabel('mean rate')
    ax.axvspan(0,0,color='r')
    import matplotlib.lines as mlines
    line = mlines.Line2D([], [], color='r', label='stim on')
    ax.legend(handles=[line], bbox_to_anchor=(0., 1.02, 1., .102), loc=4,
                ncol=2, borderaxespad=0.)
    simpleaxis(ax, bottom=False, ticks=False)
    plot_raster(trials, ax=ax2)
    ax2.axvspan(0,0, color='r')
    simpleaxis(ax2, bottom=False, ticks=False)
    ax3.bar(bins[0:-1], fano, width=bins[1]-bins[0])
    ax3.set_xlim(t_start, t_stop)
    ax3.set_ylabel('Fano factor')
    ax3.set_xlabel('time [%s]' % bins.dimensionality)
    ax3.axvspan(0, 0, color='r')
    simpleaxis(ax3)
    plt.tight_layout()
