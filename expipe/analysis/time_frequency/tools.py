import numpy as np
import quantities as pq
from ..misc import is_quantities
import matplotlib.pyplot as plt


def separate_syn_dsyn(S, f, low=[4, 12], high=[30, 80],
                      return_all=False):
    L = np.trapz(S[(low[0] <= f) & (f <= low[1]), :], axis=0)
    H = np.trapz(S[(high[0] <= f) & (f <= high[1]), :], axis=0)
    ##  Fuzzy c-means clustering
    import skfuzzy as fuzz
    data = np.vstack([np.log(L), np.log(H)])
    center, u = fuzz.cmeans(data, c=2, m=2., error=0.005, maxiter=1000,
                            init=None)[:2]
    cluster_membership = np.argmax(u, axis=0)
    index1 = np.where(cluster_membership == 0)
    index2 = np.where(cluster_membership == 1)
    if center[0, 1] > center[1, 1]:
        dsync_idxs = index1
        sync_idxs = index2
    else:
        dsync_idxs = index2
        sync_idxs = index1
    ## Power ratio
    ratio = np.log(L)/np.log(H)
    ratio_syn_mean = np.nanmean(ratio[sync_idxs])
    ratio_syn_std = np.nanstd(ratio[sync_idxs])
    ratio_dsyn_mean = np.nanmean(ratio[dsync_idxs])
    ratio_dsyn_std = np.nanstd(ratio[dsync_idxs])
    d_idcs = np.where(ratio < ratio_dsyn_mean + ratio_dsyn_std)[0]
    s_idcs = np.where(ratio > ratio_syn_mean - ratio_syn_std)[0]
    if return_all:
        return dsync_idxs, sync_idxs, L, H
    else:
        return d_idcs, s_idcs


def make_syn_dsyn_events(ana, epo, tlim=None, flim=[0, 100], deltafreq=1.,
                        f0=6, low=[4, 12], high=[30, 80], t_start=-.5*pq.s,
                        t_stop=.5*pq.s, plot=False, return_idcs=False):
    from .timefreq import TimeFreq
    from expipe.stimulus import make_trials
    from expipe.time_frequency import plot_dsyn_syn
    from neo.core import EventArray
    if tlim is not None:
        ana = ana[(ana.times >= tlim[0]) & (ana.times <= tlim[1])]
        ana.t_start = tlim[0]
    else:
        tlim = [ana.t_start, ana.t_stop] * ana.t_start.units
    is_quantities([tlim], 'vector')
    assert deltafreq <= 1., 'deltafreq is not recomended to be higher than 1'
    # compute the map
    tfr = TimeFreq(ana,
                   f_start=flim[0],
                   f_stop=flim[1],
                   deltafreq=deltafreq,
                   f0=f0,
                   sampling_rate=ana.sampling_rate
                   )
    S = abs(tfr.map).transpose()
    f = np.arange(tfr.f_start, tfr.f_stop, tfr.deltafreq)
    idcs_trials = make_trials(epo=epo, t_start=t_start, t_stop=t_stop,
                              ana=ana)
    idcs = np.reshape(idcs_trials, idcs_trials.size)
    d_idcs, s_idcs = separate_syn_dsyn(S[:, idcs], f, low=low, high=high)
    fin_d = idcs[d_idcs]
    fin_s = idcs[s_idcs]
    dsyn = []
    d_ev = []
    syn = []
    s_ev = []
    for trial, time in zip(idcs_trials, epo.times):
        if set(trial).issubset(fin_d):
            dsyn.extend(trial)
            d_ev.append(time.magnitude)
        elif set(trial).issubset(fin_s):
            syn.extend(trial)
            s_ev.append(time.magnitude)
    d_ev = EventArray(times=np.array(d_ev)*time.units, name='desynchronized',
                      description='stimulus on during desynchronized state')
    s_ev = EventArray(times=np.array(s_ev)*time.units, name='synchronized',
                      description='stimulus on during synchronized state')
    if plot:
        plot_dsyn_syn(S[:, idcs], f, ana.times[idcs], low=low, high=high)
        colors = ('r', 'k')
        fig, ax = plt.subplots()
        extent = (tfr.ana.t_start, tfr.ana.t_stop, tfr.f_start-tfr.deltafreq/2.,
                  tfr.f_stop-tfr.deltafreq/2.)
        im = ax.imshow(S,
                        interpolation='nearest',
                        extent=extent,
                        origin ='lower' ,
                        aspect = 'auto')
        for idx, color in zip([fin_d, fin_s], colors):
            clust = ana.times[idx]
            ax.plot(clust, np.ones(clust.shape)*20, '.', color=color)
        for idx, color in zip([dsyn, syn], colors):
            clust = ana.times[idx]
            ax.plot(clust, np.ones(clust.shape)*15, '.', color=color)
        for st, du in zip(epo.times, epo.durations):
            ax.axvspan(st, st+du, color='c', alpha=.3)
        ax.set_xlim([tfr.ana.t_start, tfr.ana.t_stop])
        ax.set_ylim([tfr.f_start, tfr.f_stop])
    if return_idcs:
        return dsyn, syn
    else:
        return d_ev, s_ev
