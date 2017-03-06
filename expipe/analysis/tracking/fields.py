import numpy as np
import quantities as pq


def spatial_rate_map(x, y, t, sptr, binsize=0.01*pq.m, box_xlen=1*pq.m,
                     box_ylen=1*pq.m, mask_unvisited=True, convolve=True,
                     return_bins=False, smoothing=0.02):
    """Divide a 2D space in bins of size binsize**2, count the number of spikes
    in each bin and divide by the time spent in respective bins. The map can
    then be convolved with a gaussian kernel of size csize determined by the
    smoothing factor, binsize and box_xlen.

    Parameters
    ----------
    sptr : neo.SpikeTrain
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    t : quantities.Quantity array in s
        1d vector of times at x, y positions
    binsize : float
        spatial binsize
    box_xlen : quantities scalar in m
        side length of quadratic box
    mask_unvisited: bool
        mask bins which has not been visited by nans
    convolve : bool
        convolve the rate map with a 2D Gaussian kernel

    Returns
    -------
    out : rate map
    if return_bins = True
    out : rate map, xbins, ybins
    """
    from expipe.analysis.misc.tools import is_quantities
    if not all([len(var) == len(var2) for var in [x,y,t] for var2 in [x,y,t]]):
        raise ValueError('x, y, t must have same number of elements')
    if box_xlen < x.max() or box_ylen < y.max():
        raise ValueError('box length must be larger or equal to max path length')
    from decimal import Decimal as dec
    decimals = 1e10
    remainderx = dec(float(box_xlen)*decimals) % dec(float(binsize)*decimals)
    remaindery = dec(float(box_ylen)*decimals) % dec(float(binsize)*decimals)
    if remainderx != 0 or remaindery != 0:
        raise ValueError('the remainder should be zero i.e. the ' +
                                     'box length should be an exact multiple ' +
                                     'of the binsize')
    is_quantities([x, y, t], 'vector')
    is_quantities(binsize, 'scalar')
    t = t.rescale('s')
    box_xlen = box_xlen.rescale('m').magnitude
    box_ylen = box_ylen.rescale('m').magnitude
    binsize = binsize.rescale('m').magnitude
    x = x.rescale('m').magnitude
    y = y.rescale('m').magnitude

    # interpolate one extra timepoint
    t_ = np.array(t.tolist() + [t.max() + np.median(np.diff(t))]) * pq.s
    spikes_in_bin, _ = np.histogram(sptr.times, t_)
    time_in_bin = np.diff(t_.magnitude)
    xbins = np.arange(0, box_xlen + binsize, binsize)
    ybins = np.arange(0, box_ylen + binsize, binsize)
    ix = np.digitize(x, xbins, right=True)
    iy = np.digitize(y, ybins, right=True)
    spike_pos = np.zeros((xbins.size, ybins.size))
    time_pos = np.zeros((xbins.size, ybins.size))
    for n in range(len(x) - 1):
        spike_pos[ix[n], iy[n]] += spikes_in_bin[n]
        time_pos[ix[n], iy[n]] += time_in_bin[n]
    # correct for shifting of map since digitize returns values at right edges
    spike_pos = spike_pos[1:, 1:]
    time_pos = time_pos[1:, 1:]
    with np.errstate(divide='ignore', invalid='ignore'):
        rate = np.divide(spike_pos, time_pos)
    if convolve:
        rate[np.isnan(rate)] = 0.  # for convolution
        from astropy.convolution import Gaussian2DKernel, convolve_fft
        csize = (box_xlen / binsize) * smoothing
        kernel = Gaussian2DKernel(csize)
        rate = convolve_fft(rate, kernel)  # TODO edge correction
    if mask_unvisited:
        was_in_bin = np.asarray(time_pos, dtype=bool)
        rate[np.invert(was_in_bin)] = np.nan
    if return_bins:
        return rate.T, xbins, ybins
    else:
        return rate.T


def gridness(rate_map, box_xlen, box_ylen, return_acorr=False,
             step_size=0.1*pq.m):
    '''Calculates gridness of a rate map. Calculates the normalized
    autocorrelation (A) of a rate map B where A is given as
    A = 1/n\Sum_{x,y}(B - \bar{B})^{2}/\sigma_{B}^{2}. Further, the Pearsson's
    product-moment correlation coefficients is calculated between A and A_{rot}
    rotated 30 and 60 degrees. Finally the gridness is calculated as the
    difference between the minimum of coefficients at 60 degrees and the
    maximum of coefficients at 30 degrees i.e. gridness = min(r60) - max(r30).
    In order to focus the analysis on symmetry of A the the central and the
    outer part of the gridness is maximized by increasingly mask A at steps of
    ``step_size``. This function is inspired by Lukas Solankas gridcells
    package from Matt Nolans lab.

    Parameters
    ----------
    rate_map : numpy.ndarray
    box_xlen : quantities scalar in m
        side length of quadratic box
    step_size : quantities scalar in m
        step size in masking
    return_acorr : bool
        return autocorrelation map or not

    Returns
    -------
    out : gridness, (autocorrelation map)
    '''
    from scipy.ndimage.interpolation import rotate
    import numpy.ma as ma
    from expipe.analysis.misc.tools import (is_quantities, fftcorrelate2d,
                                            masked_corrcoef2d)
    is_quantities([box_xlen, box_ylen, step_size], 'scalar')
    box_xlen = box_xlen.rescale('m').magnitude
    box_ylen = box_ylen.rescale('m').magnitude
    step_size = step_size.rescale('m').magnitude
    tmp_map = rate_map.copy()
    tmp_map[~np.isfinite(tmp_map)] = 0
    acorr = fftcorrelate2d(tmp_map, tmp_map, mode='full', normalize=True)
    rows, cols = acorr.shape
    b_x = np.linspace(-box_xlen/2., box_xlen/2., rows)
    b_y = np.linspace(-box_ylen/2., box_ylen/2., cols)
    B_x, B_y = np.meshgrid(b_x, b_y)
    grids = []
    acorrs = []
    # TODO find size of middle gaussian and exclude
    for outer in np.arange(box_xlen/4, box_xlen/2, step_size):
        m_acorr = ma.masked_array(acorr, mask=np.sqrt(B_x**2 + B_y**2) > outer)
        for inner in np.arange(0, box_xlen/4, step_size):
            m_acorr = \
                ma.masked_array(m_acorr, mask=np.sqrt(B_x**2 + B_y**2) < inner)
            angles = range(30, 180+30, 30)
            corr = []
            # Rotate and compute correlation coefficient
            for angle in angles:
                rot_acorr = rotate(m_acorr, angle, reshape=False)
                corr.append(masked_corrcoef2d(rot_acorr, m_acorr)[0, 1])
            r60 = corr[1::2]
            r30 = corr[::2]
            grids.append(np.min(r60) - np.max(r30))
            acorrs.append(m_acorr)
    if return_acorr:
        return max(grids), acorr,  # acorrs[grids.index(max(grids))]
    else:
        return max(grids)
