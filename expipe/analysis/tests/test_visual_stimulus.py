import numpy as np


# def test_average_rate():
#     """
#     Test average rate function
#     """
#     from expipe.analysis.visual_stimulus.tools import average_rate
#     from neo.core import SpikeTrain
#     import quantities as pq
# 
#     trails = [
#             SpikeTrain(np.arange(0, 10, 1.)*pq.s, t_stop=10.0, annotations="90"),
#             SpikeTrain(np.arange(0, 10, 0.5)*pq.s, t_stop=10.0, annotations="90"),
#             SpikeTrain(np.arange(0, 10, 2)*pq.s, t_stop=10.0, annotations="45"),
#             SpikeTrain(np.arange(0, 10, 2)*pq.s, t_stop=10.0, annotations="135"),
#             SpikeTrain(np.arange(0, 10, 5)*pq.s, t_stop=10.0, annotations="0"),
#             SpikeTrain(np.arange(0, 10, 5)*pq.s, t_stop=10.0, annotations="0"),
#             SpikeTrain(np.arange(0, 10, 6)*pq.s, t_stop=10.0, annotations="315"),
#             SpikeTrain([]*pq.s, t_stop=10.0, annotations="270")
#             ]
# 
#     av_rate, orients = average_rate(trails)
#     np.testing.assert_array_equal(orients, [0, 45, 90, 135, 270, 315]*pq.deg)
#     np.testing.assert_array_equal(av_rate, [0.2, 0.5, 1.5, 0.5, 0.0, 0.2]/pq.s)



def test_wrap_angle_360():
    """
    Wrap angles in range [0, 360]
    """
    from expipe.analysis.visual_stimulus.tools import wrap_angle
    angles = np.array([  85.26, -437.34,  298.14,   57.47,  -28.98,  681.25, -643.99,
         43.71, -233.82, -549.63,  593.7 ,  164.48,  544.05,  -52.66,
         79.87,  -21.11,  708.31,   29.45,  279.14, -586.88])

    angles_ex =  np.array([  85.26,  282.66,  298.14,   57.47,  331.02,  321.25,   76.01,
         43.71,  126.18,  170.37,  233.7 ,  164.48,  184.05,  307.34,
         79.87,  338.89,  348.31,   29.45,  279.14,  133.12])

    result = wrap_angle(angles, 360)
    np.testing.assert_almost_equal(result, angles_ex, decimal=13)

def test_wrap_angle_2pi():
    """
    Wrap angles in range [0, 2pi]
    """
    from expipe.analysis.visual_stimulus.tools import wrap_angle
    angles = np.array([ -7.15,  -7.3 ,   7.74,   4.68,  -9.33,   1.32,   4.18,   3.49,
         8.21,   1.43,  -0.96,   6.63,   1.32,   9.66, -10.57,  -7.17,
         1.84, -10.24,  -7.31, -11.71,  -1.82,   2.85,   1.99,  -5.11,
       -10.16,   3.6 ,   9.36,  -3.13,  -0.64,  -1.77])

    angles_ex = np.array([ 5.41637061,  5.26637061,  1.45681469,  4.68      ,  3.23637061,
        1.32      ,  4.18      ,  3.49      ,  1.92681469,  1.43      ,
        5.32318531,  0.34681469,  1.32      ,  3.37681469,  1.99637061,
        5.39637061,  1.84      ,  2.32637061,  5.25637061,  0.85637061,
        4.46318531,  2.85      ,  1.99      ,  1.17318531,  2.40637061,
        3.6       ,  3.07681469,  3.15318531,  5.64318531,  4.51318531])


    result = wrap_angle(angles, 2*np.pi)
    np.testing.assert_almost_equal(result, angles_ex, decimal=8)
