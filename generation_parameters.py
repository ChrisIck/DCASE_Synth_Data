# Parameters used in the data generation process.
import os
# Parameters used in the data generation process.

tau_rir_path = "/scratch/ci411/DCASE_GEN/tau_srir"
sim_rir_path = "/scratch/ci411/DCASE_GEN/sim_rirs"
tau_noise_path = "/scratch/ci411/TAU_SRIR_DB/TAU-SNoise_DB"
fsd50k_path = "/scratch/work/marl/datasets/sound_datasets/fsd50k"
nigens_path ="/scratch/ci411/NIGENS"
mixture_path = "/scratch/ci411/DCASE_GEN/mixtures"

def get_params(argv='1'):
    print("SET: {}".format(argv))
    # ########### default parameters (NIGENS data) ##############
    params = dict(
        db_name = 'nigens',  # name of the audio dataset used for data generation
        rirpath = tau_rir_path, 
        mixturepath = os.path.join(mixture_path, "nigens_tau_real"),  # output path for the generated dataset
        noisepath = tau_noise_path,  # path containing background noise recordings
        nb_folds = 2,  # number of folds (default 2 - training and testing)
        #rooms2fold = [[10, 6, 1, 4, 3, 8], # FOLD 1, rooms assigned to each fold (0's are ignored)
        #              [9, 5, 2, 0, 0, 0]], # FOLD 2
        rooms2fold = [['tc352','sc203','bomb_shelter','pc226','pb132','se203'],
                        ['tb103','sa203','gym']],
        db_path = nigens_path,  # path containing audio events to be utilized during data generation
        max_polyphony = 3,  # maximum number of overlapping sound events
        active_classes = [0, 1, 2, 3, 5, 6, 8, 9, 10, 11, 12, 13],  # list of sound classes to be used for data generation
        nb_mixtures_per_fold = [900, 300], # if scalar, same number of mixtures for each fold
        mixture_duration = 60., #in seconds
        event_time_per_layer = 40., #in seconds (should be less than mixture_duration)
        audio_format = 'both', # 'foa' (First Order Ambisonics) or 'mic' (four microphones) or 'both'
            )
        

    # ########### User defined parameters ##############
    if argv == '1':
        print("USING DEFAULT PARAMETERS FOR NIGENS DATA\n")
        
    elif argv == '1s':
        print("USING DEFAULT PARAMETERS FOR NIGENS DATA w/ SIMULATED RIRS\n")
        params['rirpath'] = sim_rir_path
        params['mixturepath'] = os.path.join(mixture_path, "nigens_tau_sim")

    elif argv == '2': ###### FSD50k DATA
        params['db_name'] = 'fsd50k'
        params['db_path']= fsd50k_path
        params['mixturepath'] = os.path.join(mixture_path, "fsd_1"),  # output path for the generated dataset
        params['active_classes'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        params['max_polyphony'] = 2

    elif argv == '3': ###### NIGENS interference data
        params['active_classes'] = [4, 7, 14] 
        params['max_polyphony'] = 1
        
    else:
        print('ERROR: unknown argument {}'.format(argv))
        exit()

    for key, value in params.items():
        print("\t{}: {}".format(key, value))
    return params
