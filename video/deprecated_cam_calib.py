import numpy as np

# set camera calibration from some hard coded options
def set_camera_calibration(value):
    if value == 0:
        name = "Mobius 1920x1080 (Curt)"
        K = np.array( [[1362.1,    0.0, 980.8],
                       [   0.0, 1272.8, 601.3],
                       [   0.0,    0.0,   1.0]] )
        dist = [-0.36207197, 0.14627927, -0.00674558, 0.0008926, -0.02635695]
    elif value == 1:
        name = "Mobius 1920x1080 (UMN 002)"
        K = np.array( [[983.02,   0.,         939.97982344],
                      [  0.,         984.37 , 483.59345072],
                      [  0.,           0.,           1.        ]] )

        dist = [-0.37987874,  0.2016648,  -0.00027986, -0.00000415, -0.06917004]
    elif value == 2:
        name = "Mobius 1920x1080 (UMN 003)"
        K = np.array( [[ 1401.21111735,     0.       ,    904.25404757],
                       [    0.        ,  1400.2530882,    490.12157373],
                       [    0.        ,     0.       ,      1.        ]] )
        dist = [-0.39012303,  0.19687255, -0.00069657,  0.00465592, -0.05845262]
    elif value == 3:
        name = "RunCamHD2 1920x1080 (Curt)"
        K = np.array( [[ 971.96149426,   0.        , 957.46750602],
                       [   0.        , 971.67133264, 516.50578382],
                       [   0.        ,   0.        ,   1.        ]] )
        dist = [-0.26910665, 0.10580125, 0.00048417, 0.00000925, -0.02321387]
    elif value == 4:
        name = "RunCamHD2 1920x1440 (Curt)"
        K = np.array( [[ 1296.11187055,     0.        ,   955.43024994],
                       [    0.        ,  1296.01457451,   691.47053988],
                       [    0.        ,     0.        ,     1.        ]] )
        dist = [-0.28250371, 0.14064665, 0.00061846, 0.00014488, -0.05106045]
    elif value == 5:
        name = "RunCamHD2 1920x1440 (UMN)"
        K = np.array( [[ 1300.21142205,     0.        ,   905.34625643],
                       [    0.        ,  1299.95340627,   675.19425751],
                       [    0.        ,     0.        ,     1.        ]] )
        dist = [-0.2804515,   0.13299211,  0.00211206,  0.00128484, -0.04957892]
    elif value == 6:
        name = "Sony A6000 SEL20F28 (still shot)"
        # calibrated with 96 still shots
        K = np.array( [[ 5405.06334404,     0.        ,  2794.37314413],
                       [    0.        ,  5411.68843156,  2141.95772584],
                       [    0.        ,     0.        ,     1.        ]] )
        dist = [-0.16982874,  0.00414135,  0.00025503,  0.00259518,  0.04215282]
    elif value == 7:
        name = "Sony A6000 SEL20F28 (movie mode)"
        K = np.array( [[ 1684.73041209,     0.        ,   943.23763223],
                       [    0.        ,  1683.14718211,   545.48606484],
                       [    0.        ,     0.        ,     1.        ]] )
        dist = [-0.17650495,  0.19188425,  0.00157936, -0.00020868, -0.06309823]
    elif value == 8:
        name = "Mobius 1280x720 (Matt)"
        K = np.array( [[ 1713.27,    0.0,  651.4],
                       [    0.0,  1714.36, 338.2],
                       [    0.0,     0.0,   1.0]] )
        dist = [-0.43730502,  1.1380363,  -0.00389018, -0.00234571, -4.34796866]

    else:
        print "unknown camera"
        name = "None"
        K = None
        dist = None
    return name, K, dist
    