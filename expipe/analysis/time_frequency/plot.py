import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import quantities as pq
from ..misc.tools import is_quantities
from scipy import signal
from .timefreq import TimeFreq


def plot_psd(trials, color='b', ax=None, nperseg=1024, lw=2, label='LFP',
             xlim=None, mark_max=False, legend=False, fcn=lambda inp:inp,
             title=None, xlabel='Frequency [Hz]', ylabel='PSD', ylim=None,
             mean_power=False, max_power=False, srch=None):
    '''assumes all trials to be of same length'''
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    if xlim is None:
        xlim = [0, trials[0].sampling_rate.rescale('Hz').magnitude/2]
    if srch is None:
        src = xlim
    pxxs = []
    assert not (mean_power and max_power)
    for ana in trials:
        fs = ana.sampling_rate.rescale('Hz').magnitude
        sig = np.reshape(fcn(ana.magnitude), len(ana.magnitude))
        freqs, Pxx = signal.welch(sig, fs=fs, nperseg=nperseg)
        pxxs.append(Pxx)
    pxxs = np.reshape(np.array(pxxs), (len(trials), len(Pxx)))
    if mean_power:
        pxx = pxxs.mean(axis=0)
        ax.plot(freqs, pxx, lw=lw, label=label, c=color)
    elif max_power:
        pxx = pxxs[np.argmax([np.max(pxx[(freqs > srch[0]) & (freqs < srch[1])])
                              for pxx in pxxs]), :]
        ax.plot(freqs, pxx, lw=lw, label=label, c=color)
    else:
        for idx, pxx in enumerate(pxxs):
            ax.plot(freqs, pxx, lw=lw, label='group. %s' % idx)

    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if title is not None:
        ax.set_title(title)
    ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
    if mark_max:
        pk, ind = find_max_peak(pxxs[(freqs > xlim[0]) & (freqs < xlim[1])])
        tmp = freqs[(freqs > xlim[0]) & (freqs < xlim[1])]
        addticks(ax, tmp[ind], tmp[ind].round(1))
    if legend:
        ax.legend(loc=legend)
    return ax


def plot_spike_psd(sptrs, lw=2, ax=None, NFFT=512,
                   sampling_frequency=1000.*pq.Hz, legend=False, color='b',
                   label='Spikes', mark_max=False, xlim=None,
                   rate_based=False, title=None, xlabel='Frequency [Hz]',
                   ylabel='PSD', ylim=None):
    if rate_based:
        import elephant as el
        kernel = el.kernels.GaussianKernel(2*pq.ms)
    pxxs = []
    for sptr in sptrs:
        if not rate_based:
            spt = sptr.times.rescale('s').magnitude
            bins = np.arange(sptr.t_start.rescale('s').magnitude,
                             sptr.t_stop.rescale('s').magnitude,
                             1/sampling_frequency.rescale('Hz').magnitude) #time bins for spikes
            #firing rate histogram
            hist = np.histogram(spt, bins=bins)[0].astype(float)
        else:
            hist = el.statistics.instantaneous_rate(sptr, 1/sampling_frequency,
                                                    kernel=kernel)
            hist = hist.magnitude
            hist = np.reshape(hist, hist.size)
        hist -= hist.mean()
        Pxx, freqs = plt.mlab.psd(hist, NFFT=NFFT,
                                  Fs=sampling_frequency.rescale('Hz').magnitude,
                                  noverlap=NFFT*3/4)
        pxxs.append(Pxx)
    pxxs = np.reshape(np.array(pxxs), (len(sptrs), len(Pxx))).mean(axis=0)
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    ax.plot(freqs, pxxs, lw=lw, label=label, c=color)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if ylabel is not None:
        ax.set_xlabel(xlabel)
    if title is not None:
        ax.set_title(title)
    if xlim is None:
        xlim = [0, 200]
    ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
    if mark_max:
        pk, ind = find_max_peak(pxxs[(freqs > xlim[0]) & (freqs < xlim[1])])
        tmp = freqs[(freqs > xlim[0]) & (freqs < xlim[1])]
        addticks(ax, tmp[ind], tmp[ind].round(1))
    if legend:
        ax.legend(loc=legend)
    return ax


def plot_tfr(ana, tlim=None, f0=5, flim=None, nperseg=1024,
             epo=None, epo_style='vlines', plot_ana=False):
    '''
    Plots time frequency representations of analog signal with PSD estimation


    Parameters
    ----------
    epo : neo.EpochArray
        stimulus times plotted in tfr plot
    epo_style : 'hlines' plot epochs as horizontal lines,
               'vlines' - sames with vertical lines
    plot_ana : bool
        plot analog signal at bottom of figure
    nperseg : int
        length of each welch window segment
    f0 : float
        see OpenElectrophy doc
    flim : list or tuple of size 2
        e.g. [start frequency, stop frequency]
    tlim : list or tuple of size 2
        e.g. [start time, stop time]
    '''
    assert epo_style in ['vlines', 'hlines'], 'epo_style not implemented'
    if tlim is not None:
        import neo
        ana = neo.AnalogSignal(ana.magnitude[(ana.times >= tlim[0]) &
                                             (ana.times <= tlim[1])],
                               sampling_rate=ana.sampling_rate,
                               units=ana.units,
                               t_start=tlim[0])
    else:
        tlim = [ana.t_start, ana.t_stop] * ana.t_start.units
    is_quantities([tlim], 'vector')
    freqs, Pxx = signal.welch(np.reshape(ana.magnitude, len(ana)), fs=ana.sampling_rate,
                              nperseg=nperseg)
    if flim is not None:
        Pxx = Pxx[(freqs >= flim[0]) & (freqs <= flim[1])]
        freqs = freqs[(freqs >= flim[0]) & (freqs <= flim[1])]

    tfr = TimeFreq(ana,
                   f_start=freqs[0],
                   f_stop=freqs[-1],
                   deltafreq=freqs[1]-freqs[0],
                   f0=f0,
                   sampling_rate=ana.sampling_rate,
                   use_joblib=True,
                   optimize_fft=True
                   )
    # compute the map

    if plot_ana:
        fig = plt.figure()
        gs = gridspec.GridSpec(2, 2)
        ax1 = fig.add_subplot(gs[0, 0])  # PSD
        ax2 = fig.add_subplot(gs[0, 1], sharey=ax1)  # TFR
        plt.setp(ax2.get_yticklabels(), visible=False)
        ax2.grid(False)
        ax3 = fig.add_subplot(gs[1, :], sharex=ax2)  # AnalogSignal
        ax3.plot(ana.times, ana.magnitude)
        ax3.set_xlabel('time [%s]' % ana.times.dimensionality)
        ax3.set_ylabel('signal [%s]' % ana.dimensionality)
        if tlim is not None:
            ax3.set_xlim(tlim)
        epo_line_axes = [ax2, ax3]
    else:
        fig = plt.figure()
        ax1 = fig.add_subplot(121)  # PSD
        ax2 = fig.add_subplot(122, sharey=ax1)  # TFR
        ax2.grid(False)
        epo_line_axes = [ax2]

    ax1.semilogx(Pxx, freqs, 'k', rasterized=True)
    ax1.set_xlabel(r'PSD [%s$^2$/Hz]' % ana.dimensionality)
    ax1.set_ylabel('frequency [Hz]')
    ax1.set_ylim(flim)
    tfr.plot(ax2, freq_axis='left', colorbar=False)
    ax2.set_xlabel('time [%s]' % ana.times.dimensionality)
    if tlim is None:
        tlim = [0, ana.t_stop.magnitude]
    ax2.set_xlim(tlim)
    ax2.set_ylim(flim)

    if epo is not None:
        for ax in epo_line_axes:
            ylim = ax.get_ylim()
            if epo_style == 'hlines':
                for i, t, d in zip(range(epo.times.size),
                                   epo.times, epo.durations):
                    ypos = flim[1]*0.8
                    ax.plot([t, t+d], [ypos, ypos], lw=15, color='r')
                import matplotlib.lines as mlines
                line = mlines.Line2D([], [], color='r', label='epoch')
                ax.legend(handles=[line],
                          bbox_to_anchor=(0., 1.02, 1., .102), loc=4,
                          ncol=2, borderaxespad=0.)
            elif epo_style == 'vlines':
                ax.vlines(epo.times, ylim[0], ylim[-1], color='g',
                          label='on')
                ax.vlines(epo.times+epo.durations, ylim[0], ylim[-1],
                          color='r', label='off')
                ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=4,
                          ncol=2, borderaxespad=0.)
    fig.tight_layout()
    fig.subplots_adjust(top=0.9)
    return fig

def plot_dsyn_syn(S, f, time, low=[4, 12], high=[30, 80]):
    from expipe.time_frequency import separate_syn_dsyn
    dsync_idxs, sync_idxs, L, H = separate_syn_dsyn(S, f, low=low, high=high,
                                                    return_all=True)
    rat = np.log(L)/np.log(H)
    rat_syn_mean = np.nanmean(rat[sync_idxs])
    rat_syn_std = np.nanstd(rat[sync_idxs])
    rat_dsyn_mean = np.nanmean(rat[dsync_idxs])
    rat_dsyn_std = np.nanstd(rat[dsync_idxs])
    plt.figure()
    plt.plot(time[dsync_idxs], rat[dsync_idxs], linestyle='none',
             marker='.', color='r')
    plt.plot(time[sync_idxs], rat[sync_idxs], linestyle='none',
             marker='.', color='b')

    plt.plot(time, rat_dsyn_mean*np.ones(len(rat)) + rat_dsyn_std, '--r')
    plt.plot(time, rat_dsyn_mean*np.ones(len(rat)), 'r')
    plt.plot(time, rat_syn_mean*np.ones(len(rat)) - rat_syn_std, '--b')
    plt.plot(time, rat_syn_mean*np.ones(len(rat)), 'b')
    plt.plot(time, np.mean(rat)*np.ones(len(rat)), 'k')
    plt.xlabel('Time (s)');
    plt.ylabel('log(LH power ratio)')

    d_idcs = np.where(rat < (rat_dsyn_mean + rat_dsyn_std))[0]
    s_idcs = np.where(rat > (rat_syn_mean - rat_syn_std))[0]
    plt.figure()
    plt.loglog(L[d_idcs], H[d_idcs], linestyle='none', marker='.', color='r')
    plt.loglog(L[s_idcs], H[s_idcs], linestyle='none', marker='.', color='b')
    plt.xlabel('%s power' % low)
    plt.ylabel('%s power' % high)
