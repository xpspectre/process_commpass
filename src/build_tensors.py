import os
import util
import h5py
import pickle
import numpy as np
from scipy.sparse import lil_matrix
np.random.seed(0)

"""
Select all people with at least cutoff visits 
The assumption is that other people don't have enough data to be interesting
"""
def get_people(cutoff, data_dir, param_dir):
    ##Get the data matrix and the field_names
    data, fields = util.read_clinical_data(data_dir+"PER_PATIENT_VISIT.csv", param_dir)
    visits = {}
    for person in data:
        visits[person] = []
        for visit in data[person]:
            if visit[fields.index("visit")]:
                visits[person].append(int(visit[fields.index("visit")]))

    count = 0
    people = []
    for person in data:
        if cutoff in visits[person]:
            people.append(person)
        else:
            count += 1

    return people

"""
Finds the min and max dates in the dataset.  Min date can be overriden to only look at the n days before the start of treatment.
"""
def get_dates(file_types, people, data_dir, param_dir, override_min_date=-180, calc_min_date=False):
    max_date = 0
    min_date = 0
    for file_type in file_types:
            ##Get the data matrix and the field_names
            data, fields = util.read_clinical_data(data_dir+file_type.upper()+".csv", param_dir)
            for i in range(len(fields)):
                    fields[i] = fields[i].lower()

            date_fields = []
            with open(param_dir+file_type+"_fields.csv") as fin:
                    for line in fin:
                            line = line.strip().split(",")
                            date_fields.append(line[2])

            date_fields = list(set(date_fields))
            for person in people:
                if person in data:
                    for visit in data[person]:
                        for field in date_fields:
                            date = util.get_date(visit, fields, field, file_type)
                            if date != "no date":
                                min_date = min(date, min_date)
                                max_date = max(date, max_date)

    ##You could change this to only record data after the start of the study or a date before the start of the study
    if not calc_min_date:
        min_date = override_min_date

    return min_date, max_date

def get_features(file_type, people, data_dir, param_dir, min_date, max_date):
    data, fields = util.read_clinical_data(data_dir+file_type.replace("_baseline", "").upper()+".csv", param_dir)
    valid_fields, date_fields, descriptions = util.get_feature_fields(param_dir, file_type)

    features = {}
    ##Convert values to lower case, remove spaces and turn scale text values into the correpsonding numerical values
    for person in people:
        if person not in data:
            continue

        for visit in data[person]:
            for i in range(len(fields)):
                if fields[i] not in valid_fields:
                    continue

                date = util.get_date(visit, fields, date_fields[fields[i]], file_type, min_date, max_date)
                if visit[i] == "" or date == "no date":
                    continue

                feature_name = fields[i] + "-" + descriptions[fields[i]]
                if feature_name not in features:
                    features[feature_name] = {}
                if visit[i] not in features[feature_name]:
                    features[feature_name][visit[i]] = {}
                if person not in features[feature_name][visit[i]]:
                    features[feature_name][visit[i]][person] = []
                features[feature_name][visit[i]][person].append(date)

    return features

##Choose valid features from files
def get_feature_list(features, people, cutoff):
    feature_key = []
    feature_types = []
    feature_list = []
    for field in features:
        feature_type = util.get_feature_type(features[field].keys())
        if feature_type == "text":
            for value in features[field]:
                if len(features[field][value]) >= cutoff:
                    feature = field+"-"+value
                    feature_key.append(feature)
                    feature_types.append("binary")
                    for person in features[field][value]:
                        for date in features[field][value][person]:
                            feature_list.append([people.index(person), int(date), feature_key.index(feature), 1])
        else:
            people_list = []
            for value in features[field]:
                people_list += features[field][value].keys()
            people_list = list(set(people_list))
            if len(people_list) >= cutoff:
                feature = field+"-numerical"
                feature_key.append(feature)
                feature_types.append(feature_type)
                for value in features[field]:
                    for person in features[field][value]:
                        for date in features[field][value][person]:
                            feature_list.append([people.index(person), int(date), feature_key.index(feature), float(value)])

    return feature_key, feature_list, feature_types

##Write treatment dates to a text file.  Requires some extra processing to find missing values in other files, guess at cycle lengths
def get_treatment_list(people, min_date, max_date, data_dir, param_dir):
    last_dates = util.get_last_visit_date(data_dir, param_dir)

    data, fields = util.read_clinical_data(data_dir+"STAND_ALONE_TREATMENT_REGIMEN.csv", param_dir)
    response_data, response_fields = util.read_clinical_data(data_dir+"STAND_ALONE_TRTRESP.csv", param_dir)

    for person in people:
        if person not in response_data:
            response_data[person] = []

    frequency_strings = util.get_frequency_strings(param_dir)
    indices = util.get_treatment_field_indices(fields)

    ##Gather the treatment data and account for missing dates by mathcing them against treatment response file,
    ##frequency by looking at 
    freqs = []
    cleaned_treatment_data = []
    for person in people:
        for treatment in data[person]:
            cleaned_treatment = {}

            cleaned_treatment["person"] = person

            ##Get the name of the drug
            cleaned_treatment["name"] = treatment[indices["name"]].lower()

            ##Get the frequency or the free text frequency and clean it up
            frequency, pattern, string = util.get_treatment_frequency(treatment[indices["frequency"]], treatment[indices["specify_frequency"]], frequency_strings)
            if frequency == False and pattern == False:
                continue
            cleaned_treatment['frequency'] = frequency
            cleaned_treatment['pattern'] = pattern

            ##Do some error checking / getting rid of lines or fixing them
            ##If the treatment starts after the last recorded visit date, don't include it
            ##If you can't find a valid start or end date for the treatment in the treatment response file, don't include it
            start, end = util.get_treatment_dates(treatment, indices, response_data[person], response_fields, last_dates[person])
            if start == False and end == False:
                continue
            cleaned_treatment["start"] = start
            cleaned_treatment["end"] = end

            cleaned_treatment["string"] = string


            #if cleaned_treatment['frequency'] == 0 and (cleaned_treatment["end"] - (cleaned_treatment["start"] + max(cleaned_treatment['pattern']))) > 30:
            #    print cleaned_treatment
            #    cleaned_treatment['frequency'] = '?'

            cleaned_treatment_data.append(cleaned_treatment)

    ##Get most common cycle lengths by drug
    cycle_lengths = util.get_most_common_cycle_lengths_by_drug(cleaned_treatment_data)

    ##For treatments without a cycle length, choose the most common cycle length that is at least as lpng as the last day
    for treatment in cleaned_treatment_data:
        if treatment["frequency"] == "?":
            for length in cycle_lengths[treatment["name"]]:
                if length >= max(treatment["pattern"]):
                    treatment["frequency"] = length
                    break
        if treatment["frequency"] == "?":   
            treatment["frequency"] = max(treatment["pattern"])

    ##Add in BMT from visit data file
    visit_data, visit_fields = util.read_clinical_data(data_dir+"PER_PATIENT_VISIT.csv", param_dir)
    date_ind = visit_fields.index("bmt_dayoftranspl")
    auto_ind = visit_fields.index("bmt_autologous")
    allo_ind = visit_fields.index("bmt_allogenic")
    for person in people:
        for visit in visit_data[person]:
            if visit[auto_ind] == "checked" or visit[auto_ind] == "1" or visit[allo_ind] == "checked" or visit[allo_ind] == "1":
                cleaned_treatment = {"person": person, "start": int(visit[date_ind]), "end": int(visit[date_ind]), "frequency": 0, "pattern": [1]}
                if visit[auto_ind] == "checked" or visit[auto_ind] == "1":
                    cleaned_treatment["name"] = "autologous_sct"
                elif visit[allo_ind] == "checked" or visit[allo_ind] == "1":
                    cleaned_treatment["name"] = "allogeneic_sct"
                else:
                    assert False
                cleaned_treatment_data.append(cleaned_treatment)

    treatment_key = []
    for treatment in cleaned_treatment_data:
        treatment_key.append(treatment["name"])
    treatment_key = list(set(treatment_key))
    treatment_types = ["binary"] * len(treatment_key)

    ##Make treatment list with treatments marked at appropriate times during the cycle
    treatments = []
    for treatment in cleaned_treatment_data:
        start = treatment["start"]
        cycle_ind = 0
        date = start + treatment["pattern"][cycle_ind] - 1
        last = start
        while date <= treatment["end"]:
            last = date
            treatments.append([people.index(treatment["person"]),date,treatment_key.index(treatment["name"]),1])
            if cycle_ind == len(treatment["pattern"])-1 and treatment["frequency"] != 0:
                cycle_ind = 0
                start += treatment["frequency"]
            elif cycle_ind == len(treatment["pattern"])-1 and treatment["frequency"] == 0:
                if date <= treatment["end"]:
                    treatments.append([people.index(treatment["person"]),date,treatment_key.index(treatment["name"]),1])
                break
            else:
                cycle_ind += 1
            date = start + treatment["pattern"][cycle_ind] - 1

        #if abs(treatment["end"] - last) > 30:
        #    print treatment
        #    print last
        #    print ""

    return treatment_key, treatments, treatment_types

def build_tensor(file_types, prefix, tensor_dir, feature_key, feature_list, feature_types, people, min_date, max_date, sparse=False, obs=False):
    n_days = max_date - min_date + 1
    n_people = len(people)
    n_features = len(feature_key)

    if sparse:
        data = {}
        feature_tensor = []
        for person in people:
            feature_tensor.append(lil_matrix(np.zeros((n_days, n_features))))
        for feature in feature_list:
            feature_tensor[feature[0]][feature[1]-min_date, feature[2]] = feature[3]
        data['tensor'] = feature_tensor
    else:
        feature_tensor = np.zeros((n_people, n_days, n_features))
        for feature in feature_list:
            feature_tensor[feature[0], feature[1]-min_date, feature[2]] = feature[3]

        h5f = h5py.File(tensor_dir+prefix+"_feature_tensor.h5", mode='w')
        h5f.create_dataset('tensor',data=feature_tensor)
    del feature_tensor

    if obs:
        if sparse:
            obs_tensor = []
            for person in people:
                obs_tensor.append(lil_matrix(np.zeros((n_days, n_features))))
            for feature in feature_list:
                obs_tensor[feature[0]][feature[1]-min_date, feature[2]] = 1
            data['obs_tensor'] = obs_tensor
        else:
            obs_tensor = np.zeros((n_people, n_days, n_features))
            for feature in feature_list:
                obs_tensor[feature[0], feature[1]-min_date, feature[2]] = 1

            h5f.create_dataset('obs_tensor',data=obs_tensor)
        del obs_tensor

    if sparse:
        data['people'] = np.array(people)
        data['feature_names'] = np.array(feature_key)
        data['feature_types'] = np.array(feature_types)
        pickle.dump(data, open(tensor_dir+prefix+"_feature_tensor.p", mode='w'))
    else:
        h5f.create_dataset('people',data=np.array(people))
        h5f.create_dataset('feature_names',data=np.array(feature_key))
        h5f.create_dataset('feature_types',data=np.array(feature_types))
        h5f.close()

def process_commpass(visit_cutoff, min_date, calc_min_date, min_occurrences, data_dir, tensor_dir, param_dir, debug=False):
    ##The files to look through.  These correspond to lists of relevant fields and dates in the parameters dir
    file_types = []
    baseline_file_types = []
    file_names = os.listdir(param_dir)
    for fname in file_names:
        if "_baseline_fields.csv" in fname:
            baseline_file_types.append(fname.replace("_fields.csv", ""))
        elif "_fields.csv" in fname:
            file_types.append(fname.replace("_fields.csv", ""))

    people = get_people(visit_cutoff, data_dir, param_dir)
    if debug:
        np.random.seed(0)
        rand_indices = np.random.choice(len(people)-1, 50, replace=False)
        people = list(np.array(people)[rand_indices])
        min_occurrences = 5
        print str(len(people)) + " people"

    min_date, max_date = get_dates(file_types, people, data_dir, param_dir, override_min_date=min_date, calc_min_date=calc_min_date)
    print "Min date: " + str(min_date) + ", max date: " + str(max_date)

    features = {}
    for file_type in file_types:
        print file_type + " in progress"
        features.update(get_features(file_type, people, data_dir, param_dir, min_date, max_date)) 
    feature_key, feature_list, feature_types = get_feature_list(features, people, min_occurrences)
    print "Feature key created: " + str(len(feature_key)) + " features"
    build_tensor(file_types, "clinical", tensor_dir, feature_key, feature_list, feature_types, people, min_date, max_date, obs=True)
    print "Clinical tensor built"

    baseline_features = {}
    for file_type in baseline_file_types:
        print file_type + " in progress"
        baseline_features.update(get_features(file_type, people, data_dir, param_dir, min_date, max_date=0)) 
    baseline_feature_key, baseline_feature_list, baseline_feature_types = get_feature_list(baseline_features, people, min_occurrences)
    print "Initial feature key created: " + str(len(baseline_feature_key)) + " features"
    build_tensor(baseline_file_types, "initial", tensor_dir, baseline_feature_key, baseline_feature_list, baseline_feature_types, people, min_date, max_date=0, obs=True)
    print "Initial tensor built"

    treatment_feature_key, treatment_list, treatment_types = get_treatment_list(people, min_date, max_date, data_dir, param_dir)
    print "Treatment feature key created: " + str(len(treatment_feature_key)) + " features"

    build_tensor(file_types, "treatment", tensor_dir, treatment_feature_key, treatment_list, treatment_types, people, min_date, max_date, obs=True)
    print "Treatment tensor built"