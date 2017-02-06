import numpy as np


def test_rm_nans():
    """
    Test of rm_nans(x,y,t)
    """
    import quantities as pq
    from expipe.analysis.tracking.tools import rm_nans

    x = np.arange(0., 10.) * 0.1 * pq.m
    y = np.arange(0., 10.) * 1.0 * pq.m
    t = np.arange(0., 10.) * 10. * pq.m

    x[[0, 3, 4]] = np.nan * pq.m
    y[[3, 5]] = np.nan * pq.m
    t[[1, 2, 3, 4]] = np.nan * pq.m

    x_e = np.arange(6., 10.) * 0.1 * pq.m
    y_e = np.arange(6., 10.) * 1.0 * pq.m
    t_e = np.arange(6., 10.) * 10. * pq.m

    np.testing.assert_equal((x_e, y_e, t_e), rm_nans(x, y, t))


def test_spatial_rate_map():
    import quantities as pq
    from expipe.analysis.tracking.fields import spatial_rate_map
    import neo
    N = 10
    x = np.linspace(0., 1., N) * pq.m
    y = np.linspace(0., 1., N) * pq.m
    t = np.linspace(0.1, 10., N) * pq.s
    sptr = neo.SpikeTrain(times=np.arange(0.01, max(t.magnitude), 0.1) * pq.s,
                          t_stop=max(t))
    ratemap, xbins, ybins = spatial_rate_map(x, y, t, sptr, binsize=0.1*pq.m,
                                             box_xlen=1.0*pq.m,
                                             box_ylen=1.0*pq.m,
                                             mask_unvisited=False,
                                             convolve=False,
                                             return_bins=True)
    assert all(np.diff(np.diag(ratemap)) < 1e-10)
    assert ratemap.shape == (9, 9)
    ratemap1 = spatial_rate_map(x, y, t, sptr, binsize=0.1*pq.m,
                                box_xlen=1.0*pq.m, box_ylen=1.0*pq.m,
                                mask_unvisited=False, convolve=False,
                                return_bins=False)
    assert all(np.diag(ratemap - ratemap1) < 1e-10)
    ratemap2 = spatial_rate_map(x, y, t, sptr, binsize=0.1*pq.m,
                                box_xlen=1.0*pq.m, box_ylen=1.0*pq.m,
                                mask_unvisited=False, convolve=True,
                                return_bins=False, smoothing=0.02)
    assert all(np.diff(np.diag(ratemap2)) < 0.02)
