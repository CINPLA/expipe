import numpy as np
import quantities as pq
import pandas as pd

def theta_mod_idx(sptr, **kwargs):
    '''Theta modulation index as defined in [1]_

    References:
    -----------
    .. [1] Cacucci, F., Lever, C., Wills, T. J., Burgess, N., & O'Keefe, J. (2004).
       Theta-modulated place-by-direction cells in the hippocampal formation in the rat.
       The Journal of Neuroscience, 24(38), 8265-8277.
    '''
    par = {'corr_bin_width': 0.01*pq.s,
           'corr_limit': 1.*pq.s}
    if kwargs:
        par.update(kwargs)
    from .correlogram import correlogram
    bin_width = par['corr_bin_width'].rescale('s').magnitude
    limit = par['corr_limit'].rescale('s').magnitude
    count, bins = correlogram(t1=sptr.times.magnitude, t2=None,
                              bin_width=bin_width, limit=limit,  auto=True)
    th = count[(bins[:-1] >= .05) & (bins[:-1] <= .07)].mean()
    pk = count[(bins[:-1] >= .1) & (bins[:-1] <= .14)].mean()
    return (pk - th)/(pk + th)


def fano_factor(trials, bins, return_mean_var=False):
    """
    Calculate mean matched fano factor over several trials

    Parameters
    ----------
    trials : list
        a list with neo.Spiketrains
    bins : np.ndarray or int
        bins of where to calculate fano factor
    return_mean_var : bool
        return mean count rate of trials and variance

    Returns
    -------
    out : fano factor (mean, var)
    """
    assert len(trials) > 0, 'trials cannot be empty'
    from scipy.stats import linregress
    if isinstance(bins, int):
        nbins = bins
    else:
        nbins = len(bins) - 1
    hists = np.zeros((len(trials), nbins))
    for row, trial in enumerate(trials):
        hist, _ = np.histogram(trial.times, bins)
        hists[row, :] = hist
    if len(trials) == 1:  # calculate fano over one trial
        axis = 1  # cols
    else:
        axis = 0  # rows
    if return_mean_var:
        return np.mean(hists, axis=axis), np.var(hists, axis=axis)
    else:
        return np.var(hists, axis=axis)/np.mean(hists, axis=axis)


def fano_factor_linregress(unit_trials, t_start, t_stop, binsize):
    '''calcs fano factor over several units with several trials'''
    from scipy.stats import linregress
    dim = 's'
    t_start = t_start.rescale(dim)
    t_stop = t_stop.rescale(dim)
    binsize = binsize.rescale(dim)
    bins = np.arange(t_start, t_stop + binsize, binsize)*pq.s
    means = np.zeros((len(unit_trials), len(bins)-1))
    varis = np.zeros((len(unit_trials), len(bins)-1))
    trials = []
    for row, trial in enumerate(unit_trials):
        if len(trial) == 0:
            continue
        mean, var = fano_factor(trial, bins, return_mean_var=True)
        means[row, :] = mean
        varis[row, :] = var
        trials.extend(trial)
    mean = np.mean(means, axis=0)
    nunits, nbins = means.shape
    fano = []
    for nb in range(nbins):
        slope, intercept, r_value, p_value, std_err = linregress(means[:, nb],
                                                                 varis[:, nb])
        fano.append(slope)
    return bins, means, varis, fano, trials


def coeff_var(trials):
    """
    Calculate the coefficient of variation in inter spike interval (ISI)
    distribution over several trials

    Parameters
    ----------
    trials : list of neo.Spiketrains

    Returns
    -------
    out : list of coefficient of variations
    """
    cvs = []
    for trial in trials:
        isi = np.diff(trial.times)
        if len(isi) > 0:
            cvs.append(np.std(isi) / np.mean(isi))
        else:
            cvs.append(np.nan)
    return cvs

def bootstrap(data, num_samples=10000, statistic=np.mean, alpha=0.05):
    """Returns bootstrap estimate of 100.0*(1-alpha) CI for statistic.
    Adapted from http://people.duke.edu/~ccc14/pcfb/analysis.html"""
    import numpy.random as npr
    n = len(data)
    idx = npr.randint(0, n, (num_samples, n))
    samples = data[idx]
    stat = np.sort(statistic(samples, 1))
    return (stat[int((alpha/2.0)*num_samples)],
            stat[int((1-alpha/2.0)*num_samples)])

def stat_test(tdict, test_func=None, nan_rule='remove'):
    '''performes statistic test between groups in tdict by given test function
    (test_func)'''
    if test_func is None:
        from scipy import stats
        test_func = lambda g1, g2: stats.ttest_ind(g1, g2, equal_var=False)
    ps = {}
    sts ={}
    lib = []
    for key1, item1 in tdict.iteritems():
        for key2, item2 in tdict.iteritems():
            if key1 != key2:
                if set([key1, key2]) in lib:
                    continue
                lib.append(set([key1, key2]))
                one = np.array(item1, dtype=np.float64)
                two = np.array(item2, dtype=np.float64)
                if nan_rule == 'remove':
                    one = one[np.isfinite(one)]
                    two = two[np.isfinite(two)]
                assert len(one) > 0, 'Empty list of values'
                assert len(two) > 0, 'Empty list of values'
                stat, p = test_func(one, two)
                ps[key1+'--'+key2] = p
                sts[key1+'--'+key2] = stat
    return pd.DataFrame([ps, sts], index=['p-value','statistic'])

def pairwise_corrcoef(nrns, binsize=5*pq.ms):
    from elephant.conversion import BinnedSpikeTrain
    from elephant.spike_train_correlation import corrcoef
    cc = []
    for id1, st1 in enumerate(nrns):
        for id2, st2 in enumerate(nrns):
            if id1 != id2:
                cc_matrix = corrcoef(BinnedSpikeTrain([st1, st2], binsize=binsize))
                cc.append(cc_matrix[0, 1])
    return cc
