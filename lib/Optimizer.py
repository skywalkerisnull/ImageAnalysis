#!/usr/bin/python3

# Prep the point and camera data and run it through the scipy least
# squares optimizer.
#
# (old: This version does not try to solve for any camera parameters, just
# the camera pose and 3d feature locations.)
#
# This optimizer explores using cv2 native functions to do per-image
# reprojection, and then extract out the errors from that.  This will
# require some 'assembly' and 'accounting' work.  It will also
# hopefully let me add the K and distortion parameters to the
# optimizer.

import cv2
import numpy as np
import os

import matplotlib.pyplot as plt
from matplotlib import cm


graph = None
last_mre = 1.0e+10              # a big number
def fun(params, n_cameras, n_points, by_camera_point_indices, by_camera_points_2d):
    """Compute residuals.
    
    `params` contains camera parameters, 3-D coordinates, and camera calibration parameters.
    """
    global last_mre

    error = None
    camera_params = params[:n_cameras * 6].reshape((n_cameras, 6))
    points_3d = params[n_cameras * 6:n_cameras * 6 + n_points * 3].reshape((n_points, 3))
    calib_params = params[n_cameras * 6 + n_points * 3:]
    
    K = np.identity(3)
    K[0,0] = calib_params[0]
    K[1,1] = calib_params[1]
    K[0,2] = calib_params[2]
    K[1,2] = calib_params[3]
    distCoeffs = calib_params[4:]
    #print('K:', K, 'distCoeffs', distCoeffs)

    sum = 0
    for i, cam in enumerate(camera_params):
        rvec = cam[:3]
        tvec = cam[3:6]
        proj_points, jac = cv2.projectPoints(points_3d[by_camera_point_indices[i]], rvec, tvec, K, distCoeffs)
        # print(i, points_3d[by_camera_point_indices[i]].shape, proj_points.shape, proj_points.ravel().shape)
        sum += len(proj_points.ravel())
        #print('cam:', proj_points)
        #print('point2d:', by_camera_points_2d[i])
        #print('error:', (by_camera_points_2d[i] - proj_points).ravel())
        #print('debug:', by_camera_points_2d[i].shape, proj_points.shape)
        if error is None:
            #print("first time")
            error = (by_camera_points_2d[i] - proj_points).ravel()
            #print('error:', error)
        else:
            error = np.append(error, (by_camera_points_2d[i] - proj_points).ravel())
        #print('sum:', sum, 'len error:', len(error), error.shape)
            
    mre = np.mean(np.abs(error))
    if 1.0 - mre/last_mre > 0.001:
        # mre has improved by more than 0.1%
        print('mre:', mre)
        if not graph is None:
            last_mre = mre
            graph.set_offsets(points_3d[:,[1,0]])
            graph.set_array(-points_3d[:,2])
            plt.xlim(points_3d[:,1].min(), points_3d[:,1].max() )
            plt.ylim(points_3d[:,0].min(), points_3d[:,0].max() )
            cmin = int(-points_3d[:,2].min() / 10) * 10
            cmax = (int(-points_3d[:,2].max() / 10) + 1) * 10
            #plt.clim(-points_3d[:,2].min(), -points_3d[:,2].max() )
            plt.clim(cmin, cmax)
            plt.draw()
            plt.savefig('opt-plot.png', dpi=80)
            plt.pause(0.01)
    return error

from scipy.sparse import lil_matrix

def bundle_adjustment_sparsity(n_cameras, n_points, camera_indices, point_indices):
    m = camera_indices.size * 2
    n = n_cameras * 6 + n_points * 3
    n += 9                      # four K params + five dist params
    A = lil_matrix((m, n), dtype=int)
    print('sparcity matrix is {} x {}'.format(m, n))

    i = np.arange(camera_indices.size)
    for s in range(6):
        A[2 * i, camera_indices * 6 + s] = 1
        A[2 * i + 1, camera_indices * 6 + s] = 1

    for s in range(3):
        A[2 * i, n_cameras * 6 + point_indices * 3 + s] = 1
        A[2 * i + 1, n_cameras * 6 + point_indices * 3 + s] = 1

    for s in range(9):
        A[2 * i, n_cameras * 6 + n_points * 3 + s] = 1
        A[2 * i + 1, n_cameras * 6 + n_points * 3 + s] = 1

    print('A non-zero elements = {}'.format(A.nnz))
    
    return A

# This is a python class that optimizes the estimate camera and 3d
# point fits by minimizing the mean reprojection error.

class Optimizer():
    def __init__(self, root):
        self.root = root
        self.camera_map_fwd = {}
        self.camera_map_rev = {}
        self.feat_map_fwd = {}
        self.feat_map_rev = {}

    # write the camera (motion) parameters, feature (structure)
    # parameters, and calibration (K) to files in the project
    # directory.
    def run(self, image_list, placed_images, matches_list, K, distCoeff,
            use_sba=False):
        global graph
        
        if placed_images == None:
            placed_images = set()
            # if no placed images specified, mark them all as placed
            for i in range(len(image_list)):
                placed_images.add(i)
                
        # construct the camera index remapping
        self.camera_map_fwd = {}
        self.camera_map_rev = {}
        for i, index in enumerate(placed_images):
            self.camera_map_fwd[i] = index
            self.camera_map_rev[index] = i
        print(self.camera_map_fwd)
        print(self.camera_map_rev)
        
        # initialize the feature index remapping
        self.feat_map_fwd = {}
        self.feat_map_rev = {}
        
        # iterate through the matches dictionary to produce a list of matches
        feat_used = 0
        f = open( self.root + '/sba-points.txt', 'w' )
        for i, match in enumerate(matches_list):
            ned = np.array(match[0])
            #print type(ned), ned.size, ned
            count = 0
            for p in match[1:]:
                if p[0] in placed_images:
                    count += 1
            if ned.size == 3 and count >= 2:
                self.feat_map_fwd[i] = feat_used
                self.feat_map_rev[feat_used] = i
                feat_used += 1
                s = "%.4f %.4f %.4f  " % (ned[0], ned[1], ned[2])
                f.write(s)
                s = "%d  " % (count)
                f.write(s)
                for p in match[1:]:
                    if p[0] in placed_images:
                        local_index = self.camera_map_rev[p[0]]
                        kp = image_list[p[0]].kp_list[p[1]].pt # orig/distorted
                        # kp = image_list[p[0]].uv_list[p[1]]      # undistorted
                        s = "%d %.2f %.2f " % (local_index, kp[0], kp[1])
                        f.write(s)
                f.write('\n')
        f.close()

        # assemble the initial camera estimates
        n_cameras = len(placed_images)
        camera_params = np.empty(n_cameras * 6)
        cam_idx = 0
        for index in placed_images:
            image = image_list[index]
            rvec, tvec = image.get_proj()
            camera_params[cam_idx*6:cam_idx*6+6] = np.append(rvec, tvec)
            cam_idx += 1

        # count number of 3d points and observations
        n_points = 0
        n_observations = 0
        for i, match in enumerate(matches_list):
            # count the number of referenced observations
            used = False
            for p in match[1:]:
                if p[0] in placed_images:
                    n_observations += 1
                    used = True
            if used:
                n_points += 1

        # assemble 3d point estimates and build indexing maps
        points_3d = np.empty(n_points * 3)
        point_idx = 0
        feat_used = 0
        for i, match in enumerate(matches_list):
            ned = np.array(match[0])
            used = False
            for p in match[1:]:
                if p[0] in placed_images:
                    used = True
            if used:
                self.feat_map_fwd[i] = feat_used
                self.feat_map_rev[feat_used] = i
                feat_used += 1
                points_3d[point_idx] = ned[0]
                points_3d[point_idx+1] = ned[1]
                points_3d[point_idx+2] = ned[2]
                point_idx += 3
                
        # assemble observations (image index, feature index, u, v)
        by_camera_point_indices = [ [] for i in range(n_cameras) ]
        by_camera_points_2d = [ [] for i in range(n_cameras) ]
        #print('by_camera:', by_camera)
        #points_2d = np.empty((n_observations, 2))
        #obs_idx = 0
        for i, match in enumerate(matches_list):
            for p in match[1:]:
                if p[0] in placed_images:
                    cam_index = self.camera_map_rev[p[0]]
                    feat_index = self.feat_map_fwd[i]
                    uv = image_list[p[0]].uv_list[p[1]]
                    by_camera_point_indices[cam_index].append(feat_index)
                    by_camera_points_2d[cam_index].append(uv)
                    #camera_indices[obs_idx] = cam_index
                    #point_indices[obs_idx] = feat_index
                    #obs_idx += 1
        # convert to numpy native structures
        for i in range(n_cameras):
            size = len(by_camera_point_indices[i])
            by_camera_point_indices[i] = np.array(by_camera_point_indices[i])
            by_camera_points_2d[i] = np.asarray([by_camera_points_2d[i]]).reshape(size, 1, 2)

        # generate the camera and point indices (for mapping the
        # sparse jacobian entries which define which observations
        # depend on which parameters.)
        camera_indices = np.empty(n_observations, dtype=int)
        point_indices = np.empty(n_observations, dtype=int)
        obs_idx = 0
        for i in range(n_cameras):
            for j in range(len(by_camera_point_indices[i])):
                camera_indices[obs_idx] = i
                point_indices[obs_idx] = by_camera_point_indices[i][j]
                obs_idx += 1
        print("num observations:", obs_idx)
            
        # def run(self, mode=''):
        x0 = np.hstack((camera_params.ravel(), points_3d.ravel(),
                        K[0,0], K[1,1], K[0,2], K[1,2], distCoeff))
        print('x0:')
        print(x0.shape)
        print(x0)
        f0 = fun(x0, n_cameras, n_points, by_camera_point_indices, by_camera_points_2d)
        #plt.figure()
        #plt.plot(f0)
        mre_start = np.mean(np.abs(f0))

        A = bundle_adjustment_sparsity(n_cameras, n_points, camera_indices, point_indices)

        # quick test of bounds ... allow camera parameters to go free,
        # but limit 3d points to +/- 100m of initial guess
        lower = []
        upper = []
        tol = 75.0
        for i in range(n_cameras):
            # rotation vector is unlimited
            lower.append( -np.inf )
            upper.append( np.inf )
            lower.append( -np.inf )
            upper.append( np.inf )
            lower.append( -np.inf )
            upper.append( np.inf )
            # translation vector is bounded
            lower.append( camera_params[i*6+3] - tol )
            upper.append( camera_params[i*6+3] + tol )
            lower.append( camera_params[i*6+4] - tol )
            upper.append( camera_params[i*6+4] + tol )
            lower.append( camera_params[i*6+5] - tol )
            upper.append( camera_params[i*6+5] + tol )
        for i in range(n_points * 3):
            lower.append( points_3d[i] - tol )
            upper.append( points_3d[i] + tol )

        import time
        from scipy.optimize import least_squares

        plt.figure(figsize=(16,9))
        plt.ion()
        mypts = points_3d.reshape((n_points, 3))
        graph = plt.scatter(mypts[:,1], mypts[:,0], 100, -mypts[:,2], cmap=cm.jet)
        plt.colorbar()
        plt.draw()
        plt.pause(0.01)
        
        t0 = time.time()
        with_bounds = False
        if with_bounds:
            res = least_squares(fun, x0, bounds=[lower, upper], jac_sparsity=A,
                                verbose=2,
                                x_scale='jac',
                                ftol=1e-3, method='trf',
                                args=(n_cameras, n_points,
                                      by_camera_point_indices,
                                      by_camera_points_2d))
        else:
            res = least_squares(fun, x0, jac_sparsity=A,
                                verbose=2,
                                x_scale='jac',
                                ftol=1e-3, method='trf',
                                args=(n_cameras, n_points,
                                      by_camera_point_indices,
                                      by_camera_points_2d))
        t1 = time.time()
        print("Optimization took {0:.0f} seconds".format(t1 - t0))
        # print(res['x'])
        print(res)
        #plt.plot(res.fun)
        plt.ioff()
        plt.show()
        
        camera_params = res.x[:n_cameras * 6].reshape((n_cameras, 6))
        points_3d = res.x[n_cameras * 6:n_cameras * 6 + n_points * 3].reshape((n_points, 3))

        # command = []
        #result = subprocess.check_output( command )
        # bufsize=1 is line buffered
        #process = subprocess.Popen( command, stdout=subprocess.PIPE)

        state = ''
        mre_final = np.mean(np.abs(res.fun))
        iterations = res.njev
        time_sec = t1 - t0

        print("Starting mean reprojection error: {}".format(mre_start))
        print("Final mean reprojection error: {}".format(mre_final))
        print("Iterations: {}".format(iterations))
        print("Elapsed time = {} sec".format(time_sec))
        return camera_params, points_3d, self.camera_map_fwd, self.feat_map_rev
