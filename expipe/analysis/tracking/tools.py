import numpy as np
import quantities as pq
from ..misc.tools import is_quantities, normalize


def get_raw_position(spot_group):
        """
        Get postion data from exdir led group

        Parameters
        ----------
        spot_group : exdir.group

        Returns
        ----------
        out : x, y, t
            1d vectors with position and time from LED 
        """
        coords = spot_group["data"]
        t = pq.Quantity(spot_group["timestamps"].data,
                        spot_group["timestamps"].attrs['unit'])
        # TODO: is this correct mapping?
        x = pq.Quantity(coords[:, 0], coords.attrs['unit'])
        y = pq.Quantity(coords[:, 1], coords.attrs['unit'])
        
        return x, y, t


def get_tracking(postion_group):
        """
        Get postion data from exdir position group

        Parameters
        ----------
        position_group : exdir.group

        Returns
        ----------
        out : dict
            dictionary with position and time from leds in position group 
        """
        
        tracking = {}
        for name, group in postion_group.items():
            x, y, t = get_raw_position(spot_group=group)
            # TODO: Remove nans etc
            tracking[name] = {"x": x, "y": y, "t": t}
        return tracking

    

# def get_raw_position(spot_group):
#     """
#     Get postion data from block
#     TODO: where is the signals saved - refer to /address
# 
#     Parameters
#     ----------
#     blk : neo.block
# 
#     Returns
#     ----------
#     out : x1, y1, t1, x2, y2, t2
#         1d vectors with position and time from LED 1,2
#     """
#     xy1 = blk.segments[0].irregularlysampledsignals[0]
#     xy1 = xy1.magnitude*xy1.units
#     t1 = blk.segments[0].irregularlysampledsignals[0].times
#     xy2 = blk.segments[0].irregularlysampledsignals[1]
#     xy2 = xy2.magnitude*xy2.units
#     t2 = blk.segments[0].irregularlysampledsignals[1].times
#     # else:
#     #     cnt = blk.segments[0].irregularlysampledsignals[2].magnitude[:,0]
#     #     cnt = np.array(cnt - cnt[0], dtype=int)
#     #     t = blk.segments[0].eventarrays[0].times[cnt]
# 
#     # TODO Sometimes, bonsai sends zeros when LED is lost from cam
#     xy1[xy1 == 0.0] = np.nan*xy1.units
#     xy2[xy2 == 0.0] = np.nan*xy2.units
#     x2, x1, y2, y1 = xy2[:, 0], xy1[:, 0], xy2[:, 1], xy1[:, 1]
# 
#     def cut(*x):
#         minlen = min([len(a) for a in x])
#         cutx = []
#         for a in x:
#             cutx.append(a[:minlen])
#         return cutx
#     return cut(x1, y1, t1, x2, y2, t2)


def select_best_position(x1, y1, t1, x2, y2, t2, speed_filter=5*pq.m/pq.s):
    """
    selects position data with least nan after speed filtering

    Parameters
    ----------
    x1 : quantities.Quantity array in m
        1d vector of x positions from LED 1
    y1 : quantities.Quantity array in m
        1d vector of x positions from LED 1
    t1 : quantities.Quantity array in s
        1d vector of times from LED 1 at x, y positions
    x2 : quantities.Quantity array in m
        1d vector of x positions from LED 2
    y2 : quantities.Quantity array in m
        1d vector of x positions from LED 2
    t2 : quantities.Quantity array in s
        1d vector of times from LED 2 at x, y positions
    speed_filter : None or quantities in m/s
        threshold filter for translational speed
    """
    is_quantities([x1, y1, t1, x2, y2, t2], 'vector')
    is_quantities(speed_filter, 'scalar')
    measurements1 = len(x1)
    measurements2 = len(x2)
    x1, y1, t1 = rm_nans(x1, y1, t1)
    x2, y2, t2 = rm_nans(x2, y2, t2)
    if speed_filter is not None:
        x1, y1, t1 = velocity_threshold(x1, y1, t1, speed_filter)
        x2, y2, t2 = velocity_threshold(x2, y2, t2, speed_filter)

    if len(x1) > len(x2):
        print('Removed %.2f %% invalid measurements in path' %
              ((1. - len(x1) / float(measurements1)) * 100.))
        x = x1
        y = y1
        t = t1
    else:
        print('Removed %.2f %% invalid measurements in path' %
              ((1. - len(x2) / float(measurements2)) * 100.))
        x = x2
        y = y2
        t = t2
    return x, y, t


def interp_filt_position(x, y, tm, box_size=1*pq.m, pos_fs=100*pq.Hz,
                         f_cut=10*pq.Hz):
    """
    Calculeate head direction in angles or radians for time t

    Parameters
    ----------
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    tm : quantities.Quantity array in s
        1d vector of times at x, y positions
    pos_fs : quantities scalar in Hz
        return radians

    Returns
    -------
    out : angles, resized t
    """
    import scipy.signal as ss
    assert len(x) == len(y) == len(tm), 'x, y, t must have same length'
    is_quantities([x, y, tm], 'vector')
    is_quantities([pos_fs, box_size, f_cut], 'scalar')
    spat_dim = x.units
    t = np.arange(tm.min(), tm.max() + 1./pos_fs, 1./pos_fs) * tm.units
    x = np.interp(t, tm, x)
    y = np.interp(t, tm, y)
    # rapid head movements will contribute to velocity artifacts,
    # these can be removed by low-pass filtering
    # see http://www.ncbi.nlm.nih.gov/pmc/articles/PMC1876586/
    # code addapted from Espen Hagen
    b, a = ss.butter(N=1, Wn=f_cut*2/pos_fs)
    # zero phase shift filter
    x = ss.filtfilt(b, a, x)*spat_dim
    y = ss.filtfilt(b, a, y)*spat_dim
    assert not np.isnan(x).any() and not np.isnan(y).any(), 'nans found in \
        position, x nans = %i, y nans = %i' % (sum(np.isnan(x)),
                                               sum(np.isnan(y)))
    assert (x.min() >= 0 and x.max() <= box_size and y.min() >= 0 and
            y.max() <= box_size), ("Interpolation produces path values outside \
            given box_size = %.2f, min [x, y] = [%.2f, %.2f], max [x, y] = \
            [%.2f, %.2f]" % (box_size,  x.min(), y.min(), x.max(), y.max()))
    R = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    V = R/np.diff(t)
    print('Maximum speed %.2f %s' % (V.max(), V.dimensionality))
    return x, y, t


def rm_nans(*args):
    """
    Removes nan from all corresponding arrays

    Parameters
    ----------
    args : arrays, lists or quantities which should have removed nans in
           all the same indices

    Returns
    -------
    out : args with removed nans
    """
    nan_indices = []
    for arg in args:
        nan_indices.extend(np.where(np.isnan(arg))[0].tolist())
    nan_indices = np.unique(nan_indices)
    out = []
    for arg in args:
        if isinstance(arg, pq.Quantity):
            unit = arg.units
        else:
            unit = 1
        out.append(np.delete(arg, nan_indices) * unit)
    return out


def velocity_threshold(x, y, t, threshold):
    """
    Removes values above threshold

    Parameters
    ----------
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    t : quantities.Quantity array in s
        1d vector of times at x, y positions
    threshold : float
    """
    assert len(x) == len(y) == len(t), 'x, y, t must have same length'
    is_quantities([x, y, t], 'vector')
    is_quantities(threshold, 'scalar')
    r = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    v = np.divide(r, np.diff(t))
    speed_lim = np.concatenate(([False], v > threshold), axis=0)
    x[speed_lim] = np.nan*x.units
    y[speed_lim] = np.nan*y.units
    x, y, t = rm_nans(x, y, t)
    return x, y, t
