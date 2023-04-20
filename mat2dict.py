import pickle
import scipy.io
import mat73
import numpy as np

PATH_TO_RIRs = '/home/iran/datasets/TAU-SRIR_DB/'

db_handler = open('db_config_fsd.obj','rb')  
db_config = pickle.load(db_handler) 
db_handler.close()

measinfomat = scipy.io.loadmat('measinfo.mat')['measinfo']
def get_y(angle,x):
    angle2 = np.pi-angle-np.pi/2 
    return x * np.sin(angle) / np.sin(angle2)

rirdata2room_idx = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 6, 9: 7, 10: 8}
rirdata2room_idx = {v:k for k,v in rirdata2room_idx.items()}
rirdata2room_measinfo = {1: 'bomb_shelter', 2: 'gym', 3: 'pb132', 4: 'pc226', 5: 'sa203', 6: 'sc203', 8: 'se203', 9: 'tb103', 10: 'tc352'}

# 1. add room names to rirdata_dict
rirdata_dict = {}
for v in rirdata2room_measinfo.values():
    rirdata_dict[v] = {}
    rirdata_dict[v]['doa_xyz'] = None
    rirdata_dict[v]['dist'] = None

# 2. add the trajectories to each room 
for iroom, room in enumerate(rirdata_dict.keys()):

    #################################
    #################################
    #################################
    # work first with the rir metadata
    #################################
    #################################
    #################################

    trajs_data = db_config._rirdata[iroom][0][2]

    trajs_list = []
    for traj in trajs_data:

        heights_data = traj

        heights_list = []
        for height in heights_data:

            heights_list.append(height[0])

        trajs_list.append(heights_list)
    rirdata_dict[room]['doa_xyz'] = trajs_list

    #################################
    #################################
    # now add the distance information
    #################################
    #################################
    room_name = measinfomat['room'][iroom][0][0]
    assert room_name == room
    trajectories = [str(t[0]) for t in measinfomat['trajectories'][iroom][0][0]] 
    trajectory_type = (measinfomat['trajectoryType'][iroom][0][0]) 
    dists = np.array([t for t in measinfomat['distances'][iroom][0]]) 
    heights = np.array([t for t in measinfomat['heights'][iroom][0]])
    mic_position = np.array(measinfomat['micPosition'][iroom][0])
    # compute distances
    trajs_list = []
    for ntraj in range(len(trajectories)):
        heights_list = []
        for nheight in range(len(heights[0])):
            ndoas = rirdata_dict[room]['doa_xyz'][ntraj][nheight].shape[0]
            height_delta = heights[0,nheight] - 1.2 # the microphone height is assumed to be 1.2
            if trajectory_type == 'circular':
                dist_xy = dists[0,ntraj]
                distances = np.sqrt(dist_xy**2 + height_delta**2)*np.ones((ndoas,1))
            else: # assuming it's a straight line
                pse = dists[...,ntraj] # path start and end
                pse[:,-1] = height_delta
                # in this database of IRs, all IRs start with positive y and end with negative y
                # calculate the angle to the starting point
                angle_str = np.arctan2(pse[0,1],pse[0,0]) 
                angle_end = np.arctan2(pse[1,1],pse[1,0])

                if pse[0,0] < 0: # if on the negative side of x
                    angles = np.linspace(angle_str, 2*np.pi + angle_end, ndoas)
                    x = np.abs(pse[0,0]) 
                    x_y_z = [[-x,get_y(np.pi-a,x),height_delta] if a < np.pi else [-x,-get_y(a-np.pi,x),height_delta] for a in angles]
                elif pse[0,0] > 0: # if on the positive side of x
                    angles = np.linspace(angle_str, angle_end, ndoas)
                    x = np.abs(pse[0,0])
                    x_y_z = [[x,get_y(a,x),height_delta] if a > 0 else [x,-get_y(np.abs(a),x),height_delta] for a in angles]
                distances = np.sqrt(np.sum(np.square(np.array(x_y_z)),axis=1,keepdims=True))
            heights_list.append(distances)

        trajs_list.append(heights_list)
    rirdata_dict[room]['dist'] = trajs_list



    #################################
    #################################
    #################################
    # now generate a dictionary with the actual rirs
    #################################
    #################################
    #################################

    rirfile = '{}rirs_{:02d}_{}.mat'.format(PATH_TO_RIRs,rirdata2room_idx[iroom],room)
    rirwavs = mat73.loadmat(rirfile)['rirs']['mic'] # just mic for now
    with open('{}.pkl'.format(rirfile[:-4]), 'wb') as outp:
        pickle.dump(rirwavs, outp, pickle.HIGHEST_PROTOCOL)


with open('rirdata_dict.pkl', 'wb') as outp:
    pickle.dump(rirdata_dict, outp, pickle.HIGHEST_PROTOCOL)
