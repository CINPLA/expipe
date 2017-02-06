import numpy as np
import matplotlib.pyplot as plt
import quantities as pq


def plot_waveforms(sptr, color='r', fig=None, title='waveforms', lw=2):
    """
    Visualize waveforms on respective channels

    Parameters
    ----------
    sptr : neo.SpikeTrain
    color : color of waveforms
    title : figure title
    fig : matplotlib figure

    Returns
    -------
    out : fig
    """
    nrc = sptr.waveforms.shape[1]
    if fig is None:
        fig = plt.figure()
    axs = []
    ax = None
    for c in range(nrc):
        ax = fig.add_subplot(1, nrc, c+1, sharex=ax, sharey=ax)
        axs.append(ax)
    for c in range(nrc):
        wf = sptr.waveforms[:, c, :]
        m = np.mean(wf, axis=0)
        stime = np.arange(m.size, dtype=np.float32)/sptr.sampling_rate
        stime.units = 'ms'
        sd = np.std(wf, axis=0)
        axs[c].plot(stime, m, color=color, lw=lw)
        axs[c].fill_between(stime, m-sd, m+sd, alpha=.1, color=color)
        if sptr.left_sweep is not None:
            sptr.left_sweep.units = 'ms'
            axs[c].axvspan(sptr.left_sweep, sptr.left_sweep, color='k',
                           ls='--')
        axs[c].set_xlabel(stime.dimensionality)
        axs[c].set_xlim([stime.min(), stime.max()])
        if c > 0:
            plt.setp(axs[c].get_yticklabels(), visible=False)
    axs[0].set_ylabel(r'amplitude $\pm$ std [%s]' % m.dimensionality)
    fig.suptitle(title)
    return fig


def plot_largest_waveform(sptr, color='r', ax=None, title='waveforms', lw=2,
                          ylabel=True, xlabel=True):
    """
    Visualize waveforms on respective channels

    Parameters
    ----------
    sptr : neo.SpikeTrain
    color : color of waveforms
    title : figure title
    fig : matplotlib figure

    Returns
    -------
    out : fig
    """
    nrc = sptr.waveforms.shape[1]
    if ax is None:
        fig, ax = plt.subplots(111)
    maxs = []
    for c in range(nrc):
        maxs.append(np.mean(sptr.waveforms[:, c, :], axis=0).max())
    c = np.argmax(maxs)
    wf = sptr.waveforms[:, c, :]
    m = np.mean(wf, axis=0)
    stime = np.arange(m.size, dtype=np.float32)/sptr.sampling_rate
    stime.units = 'ms'
    sd = np.std(wf, axis=0)
    ax.plot(stime, m, color=color, lw=lw)
    ax.fill_between(stime, m-sd, m+sd, alpha=.1, color=color)
    if sptr.left_sweep is not None:
        sptr.left_sweep.units = 'ms'
        ax.axvspan(sptr.left_sweep.rescale('ms'), sptr.left_sweep.rescale('ms'),
                   color='k', ls='--')
    if xlabel:
        ax.set_xlabel(stime.dimensionality)
    ax.set_xlim([stime.min(), stime.max()])
    if ylabel:
        ax.set_ylabel(r'amplitude $\pm$ std [%s]' % m.dimensionality)


def plot_amp_clusters(sptrs, colors=None, fig=None, title=None):
    """
    Visualize clustering on amplitude at detection point

    Parameters
    ----------
    sptrs : list of neo.SpikeTrains with same number of recording channels
    color : color of spikes
    title : figure title
    fig : matplotlib figure

    Returns
    -------
    out : fig
    """
    nrc = sptrs[0].waveforms.shape[1]
    if fig is None:
        fig = plt.figure()
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(nrc-1, nrc-1)
    axs = []
    for x in range(nrc-1):
        for y in range(nrc-1):
            if y <= x:
                ax = fig.add_subplot(gs[x, y])
                axs.append(ax)
                ax.set_xticks([])
                ax.set_yticks([])
                if x == nrc-2:
                    ax.set_xlabel('channel %i' % (range(nrc)[y-1]))
                if y == 0:
                    ax.set_ylabel('channel %i' % (x))
    if colors is None:
        from matplotlib.pyplot import cm
        colors = cm.rainbow(np.linspace(0, 1, len(sptrs)))
    for idx, sptr in enumerate(sptrs):
        cnt = 0
        wf = sptr.waveforms
        if sptr.left_sweep is None:
            sptr.left_sweep = 0.2 * pq.ms
        mask = int(sptr.sampling_rate*sptr.left_sweep.rescale('s'))
        color = colors[idx]
        for x in range(nrc-1):
            for y in range(nrc-1):
                if y <= x:
                    axs[cnt].plot(wf[:, y-1, mask], wf[:, x, mask], ls='None',
                                  marker='.', color=color)
                    cnt += 1
    if title is not None:
        fig.suptitle(title)
    return fig
