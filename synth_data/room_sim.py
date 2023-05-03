import np

import pyroomacoustics as pra
from pyroomacoustics import directivities as dr
from pyroomacoustics.experimental.rt60 import measure_rt60

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
                 [5,4,3],
                 [20,15,6],
                 [9,7,4],
                 [15,10,4],
                 [20,15,6],
                 [5,4,3]]

def plot_energy_db(ax, rir, fs=24000):

    # The power of the impulse response in dB
    power = rir**2
    energy = np.cumsum(power[::-1])[::-1]  # Integration according to Schroeder

    # remove the possibly all zero tail
    i_nz = np.max(np.where(energy > 0)[0])
    energy = energy[:i_nz]
    energy_db = 10 * np.log10(energy)
    energy_db -= energy_db[0]
    ax.plot(energy_db)