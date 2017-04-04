#Setup MM dataset 
import sys,os
sys.path.append('../dataset/')
import load
import util
import h5py
import numpy as np
from sklearn.preprocessing import normalize,StandardScaler
np.set_printoptions(precision=4)
import pylab as plt
from collections import OrderedDict

##saveHDF5 and saveDataHDF5 from theano_models: https://github.com/clinicalml/theanomodels/blob/master/utils/misc.py
def saveHDF5(fname, savedata):
    with h5py.File(fname,mode='w') as ff:
        for k in savedata:
            saveDataHDF5(ff,k,savedata[k])

def saveDataHDF5(file,key,savedata):
    if isinstance(savedata,dict):
        grp = file.create_group(key)
        for k,v in savedata.iteritems():
            saveDataHDF5(grp,k,v)
    else:
        file.create_dataset(key,data=savedata)

def splitRatio(idx ,train = 0.7, test = 0.2):
    assert idx.ndim==1,'Bad dims'
    shuf = np.random.permutation(idx.shape[0])
    N = len(idx)
    Ntrain = int(N*train)
    Ntest = int(N*test)
    Nvalid = N-Ntrain-Ntest
    print N, Ntrain, Nvalid, Ntest
    return idx[shuf[:Ntrain]],idx[shuf[Ntrain:Ntrain+Nvalid]],idx[shuf[Ntrain+Nvalid:]]

#aggregate a tensor over the time axis
def aggregateOverTime(tensor, mask, data_types, FREQ=90):
    markers   = np.arange(0,tensor.shape[1],FREQ)
    new_tensor = np.zeros((tensor.shape[0], len(markers), tensor.shape[2]))
    new_obs_tensor = np.zeros((tensor.shape[0], len(markers), tensor.shape[2]))
    
    for i in range(tensor.shape[0]):
        for j in range(len(markers)):
            for k in range(tensor.shape[2]):
                start_date = markers[j]
                end_date = min(start_date+FREQ+1, tensor.shape[1]+1)
                nz_ind = np.where(tensor[i, start_date:end_date, k] > 0)[0]
                for l in range(len(nz_ind)):
                        nz_ind[l] += start_date
                nz_values = tensor[i, nz_ind, k]
                if len(nz_values) > 0:
                    new_obs_tensor[i, j, k] = 1
                    if data_types[k] =='continuous':#Mean of continuous features
                        new_tensor[i, j, k] = sum(nz_values)/float(len(nz_values))
                    elif data_types[k] =='binary' or data_types[k] =='text':
                        new_tensor[i, j, k] = 1
                    elif data_types[k] =='categorical':
                        new_tensor[i, j, k] = max(nz_values)
                    else:
                        assert False, 'Invalid data type!'
            
    print 'Old: ',tensor.shape,' New: ',new_tensor.shape
    return new_tensor, new_obs_tensor

def normalize(train, valid, test, feature_types):
    means = []
    std_devs = []
    for i in range(train.shape[2]):
        people, days = np.nonzero(train[:, :, i])
        
        nz_values = train[people, days, i]
        
        if len(list(nz_values)) > 0:
            means.append(nz_values.mean())
            std_devs.append(nz_values.std())
        else:
            means.append(0)
            std_devs.append(0)       
        
    for i in range(train.shape[0]):
        for j in range(train.shape[1]):
            for k in range(train.shape[2]):
                if train[i, j, k] > 0.:
                    if std_devs[k] > 0.:
                        train[i, j, k] = (train[i, j, k] - means[k]) / std_devs[k]

 
    for i in range(valid.shape[0]):
        for j in range(valid.shape[1]):
            for k in range(valid.shape[2]):
                if valid[i, j, k] > 0.:
                    if std_devs[k] > 0.:
                        valid[i, j, k] = (valid[i, j, k] - means[k]) / std_devs[k]                   
                    
    for i in range(test.shape[0]):
        for j in range(test.shape[1]):
            for k in range(test.shape[2]):
                if test[i, j, k] > 0.:
                    if std_devs[k] > 0.:
                        test[i, j, k] = (test[i, j, k] - means[k]) / std_devs[k]   
                    
    return train, valid, test

def main(binarize_qol, tensor_dir, min_date, cutoff):

    #Remove old tensors
    if os.path.exists(tensor_dir+"mm_joined.h5"):
        os.remove(tensor_dir+"mm_joined.h5")
    if os.path.exists(tensor_dir+"mm_separate.h5"):
        os.remove(tensor_dir+"mm_separate.h5")

    dataset = load.main("clinical", tensor_dir)
    clinical_tensor = dataset['tensor']
    clinical_obs_tensor = dataset['obs_tensor']
    clinical_feature_names = dataset['feature_names']
    clinical_feature_types = dataset['feature_types']
    people = dataset['people']

    if binarize_qol:
        ##Binarize QOL variables
        for k in range(clinical_tensor.shape[2]):
            if 'qol' in clinical_feature_names[k] and clinical_feature_types[k]=='categorical':
                clinical_tensor[:,:,k] = (clinical_tensor[:,:,k]>=2.)*1.
                clinical_feature_types[k] = 'binary'

    #Clinical data before the start of treatment in 2-d
    initial_clinical_tensor, initial_clinical_mask = aggregateOverTime(clinical_tensor[:,:abs(min_date),:], 
                                     clinical_obs_tensor[:,:abs(min_date),:], clinical_feature_types, FREQ=abs(min_date))

    print "Initial clinical aggregated"

    #Clinical data after the start of treatment in bins of 90 days
    aggregated_clinical_tensor, binary_clinical_mask = aggregateOverTime(clinical_tensor[:,abs(min_date)+1:,:], 
                                     clinical_obs_tensor[:,abs(min_date)+1:,:], clinical_feature_types)

    del clinical_tensor
    del clinical_obs_tensor

    print "Clinical aggregated"

    dataset = load.main("initial", tensor_dir)
    initial_tensor = dataset['tensor']
    initial_obs_tensor = dataset['obs_tensor']
    initial_feature_names = dataset['feature_names']
    initial_feature_types = dataset['feature_types']
    assert np.array_equal(dataset['people'], people)

    #Clinical data before the start of treatment in 2-d
    aggregated_initial_tensor, aggregated_initial_mask = aggregateOverTime(initial_tensor[:,:abs(min_date),:], 
                                     initial_obs_tensor[:,:,:], initial_feature_types, FREQ=initial_tensor.shape[1])

    del initial_tensor
    del initial_obs_tensor

    print "Initial aggregated"

    dataset = load.main("treatment", tensor_dir)
    treatment_tensor = dataset['tensor']
    treatment_obs_tensor = dataset['obs_tensor']
    treatment_feature_names = dataset['feature_names']
    treatment_feature_types = dataset['feature_types']
    assert np.array_equal(dataset['people'], people)

    #Treatment data after the start of treatment in bins of 90 days
    aggregated_treatment_tensor, binary_treatment_mask = aggregateOverTime(treatment_tensor[:,abs(min_date)+1:,:], 
                                     treatment_obs_tensor[:,abs(min_date)+1:,:], treatment_feature_types)

    del treatment_tensor
    del treatment_obs_tensor

    print "Treatment aggregated"

    INITIAL_MATRIX = np.concatenate([initial_clinical_tensor, aggregated_initial_tensor], axis=2)
    INITIAL_MASK = np.concatenate([initial_clinical_mask, aggregated_initial_mask], axis=2)
    INITIAL_FEATURE_NAMES = np.concatenate([clinical_feature_names, initial_feature_names])
    INITIAL_FEATURE_TYPES = np.concatenate([clinical_feature_types, initial_feature_types])

    indices = []
    for i in range(len(INITIAL_FEATURE_NAMES)):
        if len(np.nonzero(INITIAL_MATRIX[:, 0, i])[0]) >= cutoff:
            indices.append(i)

    INITIAL_MATRIX = INITIAL_MATRIX[:, :, indices]
    INITIAL_MASK = INITIAL_MASK[:, :, indices]
    INITIAL_FEATURE_NAMES = INITIAL_FEATURE_NAMES[indices]
    INITIAL_FEATURE_TYPES = INITIAL_FEATURE_TYPES[indices]

    #Treatment binary for now
    TREATMENT_TENSOR = binary_treatment_mask
    TREATMENT_MASK = binary_treatment_mask
    TREATMENT_FEATURE_NAMES = treatment_feature_names
    TREATMENT_FEATURE_TYPES = treatment_feature_types

    ##Shuffle features by type
    reshufidx = np.argsort(clinical_feature_types)
    CLINICAL_TENSOR = aggregated_clinical_tensor[:,:,reshufidx]
    CLINICAL_MASK = binary_clinical_mask[:,:,reshufidx]
    CLINICAL_FEATURE_NAMES = clinical_feature_names[reshufidx]
    CLINICAL_FEATURE_TYPES = clinical_feature_types[reshufidx]

    RESPONSE_IDX = list(CLINICAL_FEATURE_NAMES).index("at_treatmentresp-treatment response-numerical")
    DEATH_IDX = list(CLINICAL_FEATURE_NAMES).index("se_primaryreason-primary reason for discontinuation-death")

    patient_response = CLINICAL_TENSOR[:,:,RESPONSE_IDX]
    NpatientsProgressed = np.sum((patient_response.max(1)==6)*1.)
    prog_idx = np.where(patient_response.max(1)==6)[0]
    print NpatientsProgressed, 'patients progressed'

    patient_death = CLINICAL_TENSOR[:,:,DEATH_IDX]
    NpatientsDied = np.sum((patient_death.max(1)==1)*1.)
    death_idx = np.where(patient_death.max(1)==1)[0]
    print NpatientsDied, 'patients died'

    both_idx = np.array(list(set(prog_idx.tolist()).intersection(set(death_idx.tolist()))))
    print len(both_idx),' progressed and died'

    only_prog  = np.array([k for k in prog_idx if k not in both_idx.tolist()]) 
    only_death = np.array([k for k in death_idx if k not in both_idx.tolist()])
    print 'Only death: ',len(only_death), ' Only progressed', len(only_prog)

    np.random.seed(0)
    train_both, valid_both, test_both = splitRatio(both_idx)
    train_prog, valid_prog, test_prog = splitRatio(only_prog)
    train_death, valid_death, test_death = splitRatio(only_death)

    assert len(only_prog)+len(only_death)+len(both_idx)==len(set(prog_idx.tolist()+death_idx.tolist())),'Check failed'

    remaining_idx = np.array(list(set(range(CLINICAL_TENSOR.shape[0]))-set(prog_idx.tolist()+death_idx.tolist())))
    train_remain, valid_remain, test_remain = splitRatio(remaining_idx)

    train_total = np.array(train_both.tolist()+train_prog.tolist()+train_death.tolist()+train_remain.tolist())
    valid_total = np.array(valid_both.tolist()+valid_prog.tolist()+valid_death.tolist()+valid_remain.tolist())
    test_total = np.array(test_both.tolist()+test_prog.tolist()+test_death.tolist()+test_remain.tolist())

    np.random.shuffle(train_total)
    np.random.shuffle(valid_total)
    np.random.shuffle(test_total)

    print train_total.shape[0] + test_total.shape[0] + valid_total.shape[0], CLINICAL_TENSOR.shape[0]

    #Find index under current feature names
    LABEL_NAMES = np.array(['progression','progression_days', 'surrogates for overall survival', 'os days', 'last obs days'])

    CLINICAL_Y = np.concatenate([util.PDlabel(CLINICAL_TENSOR, RESPONSE_IDX).reshape(-1,1),
                    util.PDdays(CLINICAL_TENSOR, RESPONSE_IDX).reshape(-1,1),
                    util.deathLabel(CLINICAL_TENSOR, DEATH_IDX).reshape(-1,1),
                    util.deathDays(CLINICAL_TENSOR, DEATH_IDX).reshape(-1,1),
                    util.obsDays(CLINICAL_TENSOR).reshape(-1,1)],axis=1)

    #Separate Tensors
    ## Clinical
    CLINICAL_TRAIN = CLINICAL_TENSOR[train_total]
    CLINICAL_TRAIN_Y = CLINICAL_Y[train_total]
    CLINICAL_TRAIN_MASK = CLINICAL_MASK[train_total]
    CLINICAL_VALID = CLINICAL_TENSOR[valid_total]
    CLINICAL_VALID_Y = CLINICAL_Y[valid_total]
    CLINICAL_VALID_MASK = CLINICAL_MASK[valid_total]
    CLINICAL_TEST_Y = CLINICAL_Y[test_total]
    CLINICAL_TEST = CLINICAL_TENSOR[test_total]
    CLINICAL_TEST_MASK = CLINICAL_MASK[test_total]

    ## Treatment 
    TREATMENT_TRAIN = TREATMENT_TENSOR[train_total]
    TREATMENT_TRAIN_MASK = TREATMENT_MASK[train_total]
    TREATMENT_VALID = TREATMENT_TENSOR[valid_total]
    TREATMENT_VALID_MASK = TREATMENT_MASK[valid_total]
    TREATMENT_TEST = TREATMENT_TENSOR[test_total]
    TREATMENT_TEST_MASK = TREATMENT_MASK[test_total]

    ## Initial
    INITIAL_TRAIN = INITIAL_MATRIX[train_total]
    INITIAL_VALID = INITIAL_MATRIX[valid_total]
    INITIAL_TEST = INITIAL_MATRIX[test_total]

    #Normalize all according to train data distributions
    INITIAL_TRAIN, INITIAL_VALID, INITIAL_TEST = normalize(INITIAL_TRAIN, INITIAL_VALID, INITIAL_TEST, INITIAL_FEATURE_TYPES)
    CLINICAL_TRAIN, CLINICAL_VALID, CLINICAL_TEST = normalize(CLINICAL_TRAIN, CLINICAL_VALID, CLINICAL_TEST, CLINICAL_FEATURE_TYPES)
    TREATMENT_TRAIN, TREATMENT_VALID, TREATMENT_TEST = normalize(TREATMENT_TRAIN, TREATMENT_VALID, TREATMENT_TEST, TREATMENT_FEATURE_TYPES)

    DATASET_SEPARATE = OrderedDict()
    DATASET_SEPARATE['train_y'] = CLINICAL_TRAIN_Y
    DATASET_SEPARATE['valid_y'] = CLINICAL_VALID_Y
    DATASET_SEPARATE['test_y'] = CLINICAL_TEST_Y
    DATASET_SEPARATE['y_names'] = LABEL_NAMES

    DATASET_SEPARATE['train_x'] = CLINICAL_TRAIN
    DATASET_SEPARATE['train_x_mask'] = CLINICAL_TRAIN_MASK
    DATASET_SEPARATE['valid_x'] = CLINICAL_VALID
    DATASET_SEPARATE['valid_x_mask'] = CLINICAL_VALID_MASK
    DATASET_SEPARATE['test_x'] = CLINICAL_TEST
    DATASET_SEPARATE['test_x_mask'] = CLINICAL_TEST_MASK
    DATASET_SEPARATE['x_names'] = CLINICAL_FEATURE_NAMES
    DATASET_SEPARATE['x_types'] = CLINICAL_FEATURE_TYPES

    DATASET_SEPARATE['train_u'] = TREATMENT_TRAIN
    DATASET_SEPARATE['train_u_mask'] = TREATMENT_TRAIN_MASK
    DATASET_SEPARATE['valid_u'] = TREATMENT_VALID
    DATASET_SEPARATE['valid_u_mask'] = TREATMENT_VALID_MASK
    DATASET_SEPARATE['test_u'] = TREATMENT_TEST
    DATASET_SEPARATE['test_u_mask'] = TREATMENT_TEST_MASK
    DATASET_SEPARATE['u_names'] = TREATMENT_FEATURE_NAMES
    DATASET_SEPARATE['u_types'] = TREATMENT_FEATURE_TYPES

    DATASET_SEPARATE['train_init'] = INITIAL_TRAIN[:, 0, :]
    DATASET_SEPARATE['valid_init'] = INITIAL_VALID[:, 0, :]
    DATASET_SEPARATE['test_init'] = INITIAL_TEST[:, 0, :]
    DATASET_SEPARATE['init_names'] = INITIAL_FEATURE_NAMES
    DATASET_SEPARATE['init_types'] = INITIAL_FEATURE_TYPES
    saveHDF5(tensor_dir+'mm_separate.h5',DATASET_SEPARATE)                            
                                        
    #Combined Tensors
    print 'WARNING: ASSUMES BINARY TREATMENT!!!'
    BOTH_TRAIN = np.concatenate([TREATMENT_TRAIN, CLINICAL_TRAIN], axis=2)
    BOTH_TRAIN_MASK = np.concatenate([TREATMENT_TRAIN_MASK, CLINICAL_TRAIN_MASK], axis=2)
    BOTH_VALID = np.concatenate([TREATMENT_VALID, CLINICAL_VALID], axis=2)
    BOTH_VALID_MASK = np.concatenate([TREATMENT_VALID_MASK, CLINICAL_VALID_MASK], axis=2)
    BOTH_TEST = np.concatenate([TREATMENT_TEST, CLINICAL_TEST], axis=2)
    BOTH_TEST_MASK = np.concatenate([TREATMENT_TEST_MASK, CLINICAL_TEST_MASK], axis=2)

    BOTH_FEATURE_NAMES = np.array(TREATMENT_FEATURE_NAMES.tolist()+CLINICAL_FEATURE_NAMES.tolist())
    BOTH_FEATURE_TYPES = np.array(TREATMENT_FEATURE_TYPES.tolist()+CLINICAL_FEATURE_TYPES.tolist())

    DATASET_JOINED = OrderedDict()
    DATASET_JOINED['train_y'] = CLINICAL_TRAIN_Y
    DATASET_JOINED['valid_y'] = CLINICAL_VALID_Y
    DATASET_JOINED['test_y'] = CLINICAL_TEST_Y
    DATASET_JOINED['y_names'] = LABEL_NAMES
    DATASET_JOINED['train_x'] = BOTH_TRAIN
    DATASET_JOINED['train_mask'] = BOTH_TRAIN_MASK
    DATASET_JOINED['valid_x'] = BOTH_VALID
    DATASET_JOINED['valid_mask'] = BOTH_VALID_MASK
    DATASET_JOINED['test_x'] = BOTH_TEST
    DATASET_JOINED['test_mask'] = BOTH_TEST_MASK
    DATASET_JOINED['x_names'] = BOTH_FEATURE_NAMES
    DATASET_JOINED['x_types'] = BOTH_FEATURE_NAMES
    saveHDF5(tensor_dir+'mm_joined.h5',DATASET_JOINED)