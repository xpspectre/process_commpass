# Raw Feature Tensors
The raw feature tensors have the dimensions person X date X feature and store the feature values.  The 3 tensors are the clinical tensor, which includes all temporal observations except medications, the intial tensor, which includes features that are only recorded once per person (before the start of treatment), and the treatment tensor, which includes all treatment data.  
**A note on the treatment tensor: the values are binary instead of medication doses, and the dates may not be exact (the prescribing information isn't always specific enough to get exact dates).**

# Aggregated Tensors
The aggregated tensors are the mm_seperate and the mm_joined tensors.  These have the features aggregated in 3-month bins and labels computed for whether a death date is recorded, what the death date is, whether a progression date is recorded, what the first progression date is, and the date of the last visit.  mm_seperate keeps initial, clinical and treatment features separate, while mm_joined puts them in the same tensor.  These may or may not be useful for you, depending on what you decide to do.

## To build the tensors:
Set the data_dir and desc_dir file paths in Process_CoMMpass_Data.ipynb to the locations of the clinical flatfiles and the clinical data dictionaries respectively.  Then run the notebook.

## To test the output:
Test_Data.ipynb has a few simple checks for the raw feature tensors.  You can use this to check the most and least common feature of each type.

## Some of the variables you can change include: 
**file_names:** the flat file names to include when deciding which fields to consider as features

**invalid_strings:** what strings to use to rule out fields as potential features.  Right now this mostly rules out date fields.

**baseline_cutoff:** what day marks the end of baseline features and the start of temporal features?  You’ll probably want to leave this at 0.

**temporal_frac:** What fraction of features must be after the baseline to record the feature past the baseline?

**visit_cutoff:** How many visits must a person have to be included in the dataset?

**min_date:** What is the minimum date to consider when building the tensors?

**calc_min_date:** Use the first recorded feature (around -1500), or set a closer cutoff?

**min_occurrences:** How many people must have a feature recorded to include it in the dataset?

**debug:** Run with only 50 people and min_occurrences = 5 to test changes.  This is much faster than the full dataset

**binarize_qol:** Binarize 4-point quality of life questions to [1,2][3,4]?

**load_raw_tensors** and **load_aggregated_tensors:** Setting these to true loads the tensors after they’re created.  There is probably no reason to do this, but you can use this code to load them in other files.

# Setup

To get this running, have a Python 2 installation. I did this by using the latest Anaconda2, then
```
conda create -n commpass numpy scipy h5py jupyter pyyaml xlrd scikit-learn matplotlib
source activate commpass
```