import os
import build_tensors as process
import h5py
import pickle
import numpy as np

def main(dataset, tensor_dir, sparse=False):
    if dataset == "clinical":
        if sparse:
            dataset = pickle.load(open(tensor_dir+"clinical_feature_tensor.p",mode='r'))
        else:
            data_file = h5py.File(tensor_dir+"clinical_feature_tensor.h5",mode='r')
    elif dataset == "treatment":
        if sparse:
            dataset = pickle.load(open(tensor_dir+"treatment_feature_tensor.p",mode='r'))
        else:
            data_file = h5py.File(tensor_dir+"treatment_feature_tensor.h5",mode='r')
    elif dataset == "initial":
        if sparse:
            dataset = pickle.load(open(tensor_dir+"initial_feature_tensor.p",mode='r'))
        else:
            data_file = h5py.File(tensor_dir+"initial_feature_tensor.h5",mode='r')
    elif dataset == "mm_separate":
        data_file = h5py.File(tensor_dir+"mm_separate.h5",mode='r')
    elif dataset == "mm_joined":
        data_file = h5py.File(tensor_dir+"mm_joined.h5",mode='r')
    else:
        assert False

    if dataset == "clinical" or dataset == "treatment" or dataset == "initial":
        if sparse == False:
            dataset = {}
            dataset['feature_names'] = data_file['feature_names'].value
            dataset['feature_types'] = data_file['feature_types'].value
            dataset['tensor'] = data_file['tensor'].value
            dataset['obs_tensor'] = data_file['obs_tensor'].value
            dataset['people'] = data_file['people'].value
    elif "mm" in dataset:
        dataset = {}
        dataset['train_x'] = data_file['train_x'].value
        dataset['train_x_mask'] = data_file['train_x_mask'].value
        dataset['test_x']  = data_file['test_x'].value
        dataset['test_x_mask'] = data_file['test_x_mask'].value
        dataset['valid_x'] = data_file['valid_x'].value
        dataset['valid_x_mask'] = data_file['valid_x_mask'].value
        dataset['x_names'] = data_file['x_names'].value
        dataset['x_types'] = data_file['x_types'].value

        dataset['train_u'] = data_file['train_u'].value
        dataset['train_u_mask'] = data_file['train_u_mask'].value
        dataset['test_u']  = data_file['test_u'].value
        dataset['test_u_mask'] = data_file['test_u_mask'].value
        dataset['valid_u'] = data_file['valid_u'].value
        dataset['valid_u_mask'] = data_file['valid_u_mask'].value
        dataset['u_names'] = data_file['u_names'].value
        dataset['u_types'] = data_file['u_types'].value

        dataset['train_y'] = data_file['train_y'].value
        dataset['test_y']  = data_file['test_y'].value
        dataset['valid_y'] = data_file['valid_y'].value
        dataset['y_names'] = data_file['y_names'].value

        dataset['train_init'] = data_file['train_init'].value
        dataset['test_init']  = data_file['test_init'].value
        dataset['valid_init'] = data_file['valid_init'].value
        dataset['init_names'] = data_file['init_names'].value
        dataset['init_types'] = data_file['init_types'].value

    return dataset