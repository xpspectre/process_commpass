
# coding: utf-8

# In[6]:

import numpy as np
import src.loadDataset as loadDataset
import src.build_tensors as build_tensors
import src.select_feature_fields as select_feature_fields
import src.build_features_from_tensors as build_features_from_tensors
import os


# In[7]:

##The code to load these is at the bottom.  It takes a while to load them, however.
load_raw_tensors = True
load_aggregated_tensors = True


# In[8]:

##Data dir should be set to the directory where the clinical data flatfiles are stored.  
##Tensor dir is where the output is saved.  This will be created if it doesn't already exist.
##Param dir is where the parameters for running the code are stored.  You shouldn't change this.
base_dir = 'data/raw'
data_dir = os.path.join(base_dir, 'clinical_data_tables/CoMMpass_IA9_FlatFiles/')
desc_dir = os.path.join(base_dir, 'clinical_data_tables/CoMMpass_IA9_FlatFile_Dictionaries/')
output_dir = 'data/process_commpass'
tensor_dir = os.path.join(output_dir, 'commpass_ia9_tensors/')
param_dir = "parameters/"


# This selects the fields in the data to use as potential features.  The field names and descriptions must not contain any of the invalid strings to be considered valid efatrues.  This mostly rules out redundant data, metadata, and dates.  The fields are then matched with a date field by trying to find one in the field subgroup, and if that fails, using a general visit date.  The baseline cutoff is used to decide after what date features are considered temporal.  The temporal frac dictates what percent of the observations must be after the baseline date for a feature to be considered temporal.  The file names dictate which files to search through.  The ones that aren't included are treatments that are processed slightly differently, and survival endpoints that should be apaprent from looking at features in other files.  Features must still make the count cutoff to be included as final features.

# In[9]:

##What files are we searching through to build features?
file_names = ["stand_alone_ae", "per_patient_visit", "stand_alone_treatment_regimen", 'stand_alone_emergency_dept', 'stand_alone_admissions', 'stand_alone_medhx', 'stand_alone_famhx', 'per_patient']
##What strings invalidate a field as a feature?  Mostly correspond to meta-data or dates
invalid_strings = ["date", "day", "week", "time", "enr", "interval", "dose", "unit", "frequency", "ongoing", "route", "_was", "visit", "censor", "d_pt", "ic_", "bmt", "flag", "vj", "mmtx_therapy", "mmtx_type", "dictionary"]
##What date are we using as the cutoff for no longer baseline?
baseline_cutoff = 0
##What fraction of the feature's observations must be before treatment to treat it as a baseline feature?
temporal_frac = 0.5

select_feature_fields.main(file_names, invalid_strings, baseline_cutoff, temporal_frac, data_dir, param_dir, desc_dir)


# In[ ]:

##Create tensor dir if it doesn't already exist
import os
if not os.path.exists(tensor_dir):
    os.makedirs(tensor_dir)


# This builds 3 3-d tensors from the CoMMpass data: clinical, treatment and initial tensors.  The initial tensor has measurements that are exclusively or heavily measured at the baseline visit.  These do not appear in the clinical tensor.  The clinical tensor has all temporal clinical measurements.  The treatment tensor has binary indicators for treatments (it doesn't include treatment doses yet).  
# 
# The data you can load from these files include:
# tensor: the data itself
# obs_tensor: indicates if marks observed features with a 1 and has zeros otherwise. This helps to differentiate between negative observations of a feature and missing values.  
# feature_names: names of features
# feature_types: whether the features are continuous, binary, or scale variables
# people: the patient identifiers.  These are in the same order across all three files.

# In[ ]:

##What's the min last visit number to include a person in the cohort?
visit_cutoff = 1
##What's the minimum date, i.e. where is time zero for the tensors?
min_date = -180
##Should we use the minimum date or set our own min date?
calc_min_date = False
##The minimum number of time to see a text value to count it as a feature
min_occurrences = 50
##Set debug to True to run with only 50 people and min_occurrences set to 5
debug = False

build_tensors.process_commpass(visit_cutoff, min_date, calc_min_date, min_occurrences, data_dir, tensor_dir, param_dir, debug=debug)


# This aggregates the features from the raw tensors into n month windows (this is a flag you can change) and puts everything before the start of treatment in the initial feature matrix.  It also binarizes quality of life questions (this is a flag you can change).  It then splits the dataset into train, test, validate with balanced numbers of patients who progress and patients who die across the splits.  It also normalizes the features in all three splits according to the distribution of the train features.  It also includes labels for time of first progression and time of death.

# In[ ]:

binarize_qol = True
build_features_from_tensors.main(binarize_qol, tensor_dir, min_date, min_occurrences)


# In[ ]:

if load_raw_tensors:
    dataset = loadDataset.main("clinical", tensor_dir)
    clinical_tensor = dataset['tensor']
    clinical_obs_tensor = dataset['obs_tensor']
    clinical_feature_names = dataset['feature_names']
    clinical_feature_types = dataset['feature_types']
    people = dataset['people']

    dataset = loadDataset.main("initial", tensor_dir)
    initial_tensor = dataset['tensor']
    initial_feature_names = dataset['feature_names']
    initial_feature_types = dataset['feature_types']
    assert np.array_equal(dataset['people'], people)

    dataset = loadDataset.main("treatment", tensor_dir)
    treatment_tensor = dataset['tensor']
    treatment_obs_tensor = dataset['obs_tensor']
    treatment_feature_names = dataset['feature_names']
    treatment_feature_types = dataset['feature_types']
    assert np.array_equal(dataset['people'], people)


# In[ ]:

if load_aggregated_tensors:
    dataset = loadDataset.main('mm_separate', tensor_dir)

    ##Clinical data
    mm_train_x = dataset['train_x']
    mm_train_x_mask = dataset['train_x_mask']
    mm_valid_x = dataset['valid_x']
    mm_valid_x_mask = dataset['valid_x_mask']
    mm_test_x = dataset['test_x']
    mm_test_x_mask = dataset['test_x_mask']
    mm_x_names = dataset['x_names']
    mm_x_types = dataset['x_types']
    print "MM separate clinical train matrix shape: " + str(mm_train_x.shape)

    ##Treatments
    mm_train_u = dataset['train_u']
    mm_train_u_mask = dataset['train_u_mask']
    mm_valid_u = dataset['valid_u']
    mm_valid_u_mask = dataset['valid_u_mask']
    mm_test_u = dataset['test_u']
    mm_test_u_mask = dataset['test_u_mask']
    mm_u_names = dataset['u_names']
    mm_u_types = dataset['u_types']
    print "MM separate treatment train matrix shape: " + str(mm_train_u.shape)

    ##Initial data matrix
    mm_train_init = dataset['train_init']
    mm_valid_init = dataset['valid_init']
    mm_test_init = dataset['test_init']
    mm_init_names = dataset['init_names']
    mm_init_types = dataset['init_types']
    print "MM separate initial train matrix shape: " + str(mm_train_init.shape)

    ##Labels
    mm_train_y = dataset['train_y']
    mm_valid_y = dataset['valid_y']
    mm_test_y = dataset['test_y']
    mm_y_names = dataset['y_names']


# In[ ]:



