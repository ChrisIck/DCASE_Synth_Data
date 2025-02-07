import numpy as np
from generation_parameters import get_params
from db_config import DBConfig
from scipy.io import loadmat
import os
import h5py
import pickle

import pyroomacoustics as pra
from pyroomacoustics import directivities as dr
from pyroomacoustics.experimental.rt60 import measure_rt60
import argparse
from synth_data import tau_loading

room_list = ["bomb_shelter",
             "gym",
             "pb132",
             "pc226",
             "sa203",
             "sc203",
             "se203",
             "tb103",
             "tc352"]

mat_file_list = ['rirs_01_bomb_shelter.mat',
                 'rirs_02_gym.mat',
                 'rirs_03_pb132.mat',
                 'rirs_04_pc226.mat',
                 'rirs_05_sa203.mat',
                 'rirs_06_sc203.mat',
                 'rirs_08_se203.mat',
                 'rirs_09_tb103.mat',
                 'rirs_10_tc352.mat']

room_dim_list = [[50,50,12],
                 [26,16,9],
                 [9, 7, 4],
                 [6,6,3],
                 [20,15,6],
                 [11,8,4],
                 [15,13,4],
                 [20,15,6],
                 [6,5,3]]

def get_y(angle,x):
    angle2 = np.pi-angle-np.pi/2 
    return x * np.sin(angle) / np.sin(angle2)

parser = argparse.ArgumentParser()

parser.add_argument("room_name", type=str,
                    help="name of room")

parser.add_argument("--output", dest="output_dir", type=str, 
                    help="directory for file output", required=False,
                    default='/scratch/ci411/DCASE_GEN/sim_rirs')

parser.add_argument("--decay-db", dest="decay_db", type=int,
                    help="decay db for estimating rt60", required=False,
                    default=15)

parser.add_argument("--t-type", dest="t_type", type=str, required=False,
                    help="type of trajectory (circular or linear)",
                    default="circular")

parser.add_argument("--max-order", dest="max_order", type=int, required=False,
                    help="maximum order of reflections for ISM sim",
                    default=25)

parser.add_argument("--noise-var", dest="noise_var", type=float, required=False,
                    help="noise variance passed to 'sigma2_awgn' room parameter",
                    default=1)

parser.add_argument("--rir-len", dest="rir_len", type=int, required=False,
                    help="the length of stored rirs in samples",
                    default=7200)

parser.add_argument("--sr", dest="sr", type=int, required=False,
                    help="the sample rate of the simulation/stored data",
                    default=24000)

parser.add_argument("--single-path", dest="single_path", type=bool, required=False,
                    help="debugging option for computing a single path",
                    default=False)

parser.add_argument("--store-hdf5", dest="store_hdf5", type=bool, required=False,
                    help="Option to store output to hdf5 files",
                    default=False)

args = parser.parse_args()

#microphone array definitions
print("Defining mics...")
m1_coords = [.042, 45, 35]
m2_coords = [.042, -45, -35]
m3_coords = [.042, 135, -35]
m4_coords = [.042, -135, 35]


m1_dir = dr.CardioidFamily(
    orientation=dr.DirectionVector(azimuth=45, colatitude=55, degrees=True),
    pattern_enum=dr.DirectivityPattern.HYPERCARDIOID,
)

m2_dir = dr.CardioidFamily(
    orientation=dr.DirectionVector(azimuth=-45, colatitude=125, degrees=True),
    pattern_enum=dr.DirectivityPattern.HYPERCARDIOID,
)

m3_dir = dr.CardioidFamily(
    orientation=dr.DirectionVector(azimuth=135, colatitude=125, degrees=True),
    pattern_enum=dr.DirectivityPattern.HYPERCARDIOID,
)

m4_dir = dr.CardioidFamily(
    orientation=dr.DirectionVector(azimuth=-135, colatitude=55, degrees=True),
    pattern_enum=dr.DirectivityPattern.HYPERCARDIOID,
)

mic_coords = [m1_coords, m2_coords, m3_coords, m4_coords]
mic_dirs = [m1_dir, m2_dir, m3_dir, m4_dir]

mic_loc_center = np.array([0.05, 0.05, 0.05])
mic_locs = np.empty((0,3))
for coord in mic_coords:
    rad, azi, ele = coord
    azi = azi * 2 * np.pi / 360
    ele = ele * 2 * np.pi / 360
    x_offset = rad * np.cos(azi) * np.cos(ele)
    y_offset = rad * np.sin(azi) * np.cos(ele)
    z_offset = rad * np.sin(ele)
    mic_loc = mic_loc_center + np.array([x_offset, y_offset, z_offset])
    mic_locs = np.vstack([mic_locs,mic_loc])
print("Mic placed at {}".format(mic_loc_center))

with open('db_config_synthgen.obj', 'rb') as file:
    db_config = pickle.load(file)
    
rirdata2room_idx = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 6, 9: 7, 10: 8}
rirdata2room_idx = {v:k for k,v in rirdata2room_idx.items()}

#load room info
print("Loading room info...")
room_idx = room_list.index(args.room_name)

#sample rirs for rt60 to calculate MAC
rir_file = mat_file_list[room_idx]
samples = tau_loading.load_rir_sample(rir_file, db_config, t_type=args.t_type)
decay_db = args.decay_db
rt = []
for i in range(samples.shape[0]):
    rt.append(measure_rt60(samples[i], fs=args.sr, decay_db=decay_db))
rt = np.array(rt) * (60/decay_db)
rt_avg = np.average(rt)

room_dim = room_dim_list[room_idx]
e_absorption, _ = pra.inverse_sabine(rt_avg, room_dim)

print("Loading path data...")
#load paths
paths, paths_meta, room_meta = tau_loading.load_paths(room_idx, db_config)

#place mics in center-ish of room
room_center = np.array([room_dim[0]/2, room_dim[1]/2, 0])
mic_center = room_meta['microphone_position'] + room_center
centered_mics = mic_locs + mic_center


#get dataset dimensions
n_traj, n_heights = paths.shape
path_len = len(paths[0,0])

if args.single_path:
    n_traj = 1
    n_heights = 1
    
#check for outputdir (create if doesn't exist)
room_rir_dir = os.path.join(args.output_dir, 'mic', args.room_name)
if not os.path.exists(room_rir_dir):
    os.mkdir(room_rir_dir)

#iterating through paths and simulating (one at a time)
print("Computing rirs...")
out_pickle = []
for i in range(n_traj):
    out_pickle.append([])
    for j in range(n_heights):
        
        room = pra.ShoeBox(room_dim, fs=args.sr, 
                         materials=pra.Material(e_absorption),
                         max_order=args.max_order, 
                         sigma2_awgn=args.noise_var)
        room.add_microphone_array(centered_mics.T, directivity=mic_dirs)
        print("t{}h{}".format(i,j))
        path = paths[i,j]
        centered_path = path + mic_center
        path_rirs = np.empty((4, len(path), args.rir_len))
        for source in centered_path:
            try:
                room.add_source(np.maximum(source,0))
            except ValueError:
                print("Source at {} is not inside room of dimensions {}".format(source, room_dim))
        room.compute_rir()
        for k in range(4):
            for l in range(len(path)):
                path_rirs[k,l] = room.rir[k][l][:args.rir_len]
        
        path_rirs = np.moveaxis(path_rirs, [0,1,2], [1,2,0])
        #save to pickle list
        out_pickle[i].append(path_rirs)
        
        #store to hdf5
        if args.store_hdf5:
            path_label = "{}_t{}h{}.hdf5".format(args.room_name, i, j)
            path_filename = os.path.join(room_rir_dir, path_label)
            if not os.path.exists(path_filename):
                with h5py.File(path_filename, 'w') as f:
                    f.create_dataset('rirs', data=path_rirs)
                    f.create_dataset('rate', data=np.array([args.sr]))
            else:
                with h5py.File(path_filename, 'r+') as f:
                    f['rirs'][:] = path_rirs
                    f['rate'][:] = np.array([args.sr])
            print("Stored path at {}".format(path_filename))
            
pickle_path = os.path.join(args.output_dir, 'rirs_{:02d}_{}.pkl'.format(rirdata2room_idx[room_idx],args.room_name))
print(f"Storing result to {pickle_path}")
with open(pickle_path, 'wb') as outp:
    pickle.dump(out_pickle, outp, pickle.HIGHEST_PROTOCOL)