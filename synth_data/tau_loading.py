import numpy as np
import mat73

def unitvec_to_cartesian(path_unitvec, height, dist):
    if type(dist) == np.ndarray:
        z_offset = height
        rad = np.sqrt(dist[0][0]**2 + (dist[0][2]+z_offset)**2)
        scaled_path = map_to_cylinder(path_unitvec, rad, axis=1)
        centered_path = scaled_path
    else:    
        scaled_path = map_to_cylinder(path_unitvec, dist, axis=2)
        centered_path = scaled_path
    return centered_path

def map_to_cylinder(path, rad, axis=2):
    #maps points (unit vecs) to cylinder of known radius along axis (default z/2)
    scaled_path = np.empty(path.shape)
    rad_axes = [0,1,2]
    rad_axes.remove(axis)
    for i in range(path.shape[0]):
        vec = path[i]
        scale_rad = np.sqrt(np.sum([vec[j]**2 for j in rad_axes]))
        scale = rad / scale_rad
        scaled_path[i] = vec * scale
    return scaled_path

def load_paths(room_idx, db_config, center_on_mic = False):
    rooms = ['bomb_shelter', 'gym', 'pb132', 'pc226', 'sa203', 'sc203', 'se203', 'tb103', 'tc352']
    room = rooms[room_idx]
    trajs = db_config._measinfo[room]['trajectories']
    heights = db_config._measinfo[room]['heights'][0]
    dists = db_config._measinfo[room]['distances']
    traj_type = db_config._measinfo[room]['trajectory_type']
    mic_pos = db_config._measinfo[room]['mic_position'][0]
    paths = db_config._rirdata[room_idx][0][2]
    output_paths = np.empty(paths.shape, dtype=object)
    path_metadata = np.empty(paths.shape, dtype=object)
    room_metadata = {'room': room, 'trajectory_type': traj_type, 'microphone_position': mic_pos}
    for i, traj in enumerate(trajs):
        for j, height in enumerate(heights):
            
            if traj_type == 'circular':
                dist = dists[0][i]
            elif traj_type =='linear':
                dist = dists[:,:,i]
            
            path_unitvec = paths[i,j][0]
            path_dict = {'trajectory': traj, 'height': height}
            path_cartesian = unitvec_to_cartesian(path_unitvec, height, dist)
            if center_on_mic:
                path_cartesian += mic_pos
            output_paths[i,j] = path_cartesian
            path_metadata[i,j] = path_dict
            
    return output_paths, path_metadata, room_metadata

def plot_path(paths, ax):
    for i in range(paths.shape[0]):
        for j in range(paths.shape[1]):
            #dist from z axis, might need to fix
            path = paths[i,j]
            ax.plot(path[:,0], path[:,1], path[:,2], '.', alpha=.1)
            
def sample_rirs(rirs, n, t_type='circular'):
    if t_type == 'circular':
        n_traj, n_heights, L, n_ch, n_points = np.array(rirs).shape
    elif t_type == 'linear':
        n_traj = len(rirs)
        L, n_ch, n_points = rirs[0][0].shape
    output = np.empty((n, L))
    for i in range(n):
        ts = np.random.randint(n_traj)
        if t_type == 'linear':
            n_heights = len(rirs[ts])
        hs = np.random.randint(n_heights)
        if t_type == 'linear':
            L, n_ch, n_points = rirs[ts][hs].shape
        cs = np.random.randint(n_ch)
        ps = np.random.randint(n_points)
        output[i, :] = rirs[ts][hs][:, cs, ps]
    return output
    
def load_rir_sample(rir_file, db_config, n=5, t_type='circular', audio_format='mic'):
    path = db_config._rirpath + '/' + rir_file
    rirs = mat73.loadmat(path)
    rirs = rirs['rirs'][audio_format]
    sample = sample_rirs(rirs, n, t_type=t_type)
    del rirs
    return sample