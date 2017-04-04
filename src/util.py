import re
import yaml
import numpy as np
import loadDataset
np.random.seed(0)

def get_train_test_indices(labels, fraction=0.66):
    num_elems = len(labels)
    train = list(np.random.choice(num_elems, int(num_elems*fraction), replace=False))
    test = list(np.setdiff1d(np.arange(num_elems), train))
    return train, test

def splitRatio(idx ,train = 0.7, test = 0.2):
    assert idx.ndim==1,'Bad dims'
    shuf = np.random.permutation(idx.shape[0])
    N = len(idx)
    Ntrain = int(N*train)
    Ntest = int(N*test)
    Nvalid = N-Ntrain-Ntest
    print N, Ntrain, Nvalid, Ntest
    return idx[shuf[:Ntrain]],idx[shuf[Ntrain:Ntrain+Nvalid]],idx[shuf[Ntrain+Nvalid:]]

def read_yaml(fname):
    with open(fname, 'rb') as fin:
        return yaml.load(fin)

def read_clinical_data(fname, param_dir):
    scale_conversion = get_scale_conversion(param_dir)

    patient_data = {}
    with open(fname, "r") as fin:
        data = fin.read()
        clean_data = []
        clean_commas = False
        for i in range(len(data)):
            if data[i] == '"' and clean_commas:
                clean_commas = False
            elif data[i] == '"': # And not clean commas (implied)
                clean_commas = True
            if data[i] == "," and clean_commas:
                clean_data.append(";")
            else:
                clean_data.append(data[i])
        data = "".join(clean_data)
        if "\n" in data:
            data = data.split("\n")
        else:
            data = data.split("\r")

    fields = data[0].strip().split(",")
    for i in range(len(fields)):
        fields[i] = fields[i].lower()

    calc_weight = False
    if "demog_weight" in fields:
        weight_ind = fields.index("demog_weight")
        weight_unit_ind = fields.index("demog_weightunitofm")
        height_ind = fields.index("demog_height")
        height_unit_ind = fields.index("demog_heightunitofm")
        calc_weight = True

    for line in data[1:]:
        if line:
            line = line.strip().lower().split(",")
            pid = line[0]

            for i in range(len(line)):
                line[i] = line[i].lower()
                if line[i] in scale_conversion:
                    line[i] = str(scale_conversion[line[i]])

            if calc_weight:
                if line[weight_unit_ind] == "lb":
                    line[weight_ind] = str(int(line[weight_ind]) * (1/2.2))
                if line[height_unit_ind] == "in":
                    line[height_ind] = str(int(line[height_ind]) * 2.54)

            if pid not in patient_data.keys():
                patient_data[pid] = []
            patient_data[pid].append(line)

    return patient_data, fields

def get_date(visit, fields, date_field, file_type, min_date=False, max_date=False):
    if date_field == "BASELINE":
        if min_date:
            date = min_date
        else:
            date = 0
    elif visit[fields.index(date_field)]:
        date = int(visit[fields.index(date_field)])
    elif "visitdy" in fields and visit[fields.index("visitdy")]:
        date = int(visit[fields.index("visitdy")])
    elif "vj_interval" in fields:
        if "Month" == visit[fields.index("vj_interval")].split(" ")[0]:
            num = int(re.sub("\D", "", visit[fields.index("vj_interval")]))
            date = 30 * num
        elif "Year" == visit[fields.index("vj_interval")].split(" ")[0]:
            num = int(re.sub("\D", "", visit[fields.index("vj_interval")]))
            date = 365 * num
        elif "Baseline" == visit[fields.index("vj_interval")].split(" ")[0] or "Screening" == visit[fields.index("vj_interval")].split(" ")[0]:
            if min_date:
                date = min_date
            else:
                date = 0
        else:
            date = "no date"
    else:
        date = "no date"

    if (min_date is not False and date < min_date) or (max_date is not False and date > max_date):
        date = "no date"

    return date

def get_date_fields(param_dir, file_type):
    date_fields = {}
    with open(param_dir+file_type+"_fields.csv") as fin:
        for line in fin:
            line = line.strip().split(",")
            date_fields[line[0]] = line[2]
    return date_fields

def get_frequency_strings(param_dir):
    return read_yaml(param_dir+"frequency_dictionary.yaml")

def get_treatment_frequency(frequency, specify_frequency, frequency_strings):
    frequency = frequency.lower()
    if frequency == "oth" or frequency == "other":
        frequency = specify_frequency.lower()
    frequency = frequency.replace(",", "|").replace("(", " ").replace(")", " ").replace("&", "and").replace('"', " ").replace(" ", "")
    if frequency == "unk" or frequency == "unknown" or frequency == "" or frequency == "unknow" or frequency == "other" or frequency == "physiciandiscretion":
        return False, False, False

    string = frequency

    found = False
    for pattern in frequency_strings:
        if frequency in frequency_strings[pattern]:
            frequency = pattern.split("-")[1]
            pattern = pattern.split("-")[0].replace("(", "").replace(")", "").split(",")
            found = True
            break
    
    if not found:
        print frequency

    #assert found, frequency
    for j in range(len(pattern)):
        pattern[j] = int(pattern[j])

    if frequency != "?":
        frequency = int(frequency)

    return frequency, pattern, string

def get_treatment_dates(treatment, indices, combinations, combination_fields, last_date):
    if treatment[indices["start"]]:
        start = int(treatment[indices["start"]])
    else:
        start = -1000

    if treatment[indices["ongoing"]] == "checked":
        end = int(last_date[person])
    else:
        if treatment[indices["end"]]:
            end = int(treatment[indices["end"]])
        else:
            end = -1000

    #If the treatment starts after the last recorded visit date, don't include it
    if start > last_date or (start < 0 and end < 0):
        return False, False

    #If the start date is invalid, try to find an entry in the treatment responses that includes the treatment and starts before or at the treatment and ends at or after the treatment. Use its end date
    if start < 0:
        for combination in combinations:
            if int(combination[combination_fields.index("trtstdy")]) <= end and int(combination[combination_fields.index("trtendy")]) >= end and treatment[indices["name"]] in combination[combination_fields.index("trtname")].lower():
                start = int(combination[combination_fields.index("trtstdy")])

    #Repeate process above, but for the end date
    if end < 0:
        for combination in combinations:
            if int(combination[combination_fields.index("trtstdy")]) <= start and int(combination[combination_fields.index("trtendy")]) >= start and treatment[indices["name"]] in combination[combination_fields.index("trtname")].lower():
                end = int(combination[combination_fields.index("trtendy")])

    #If the treatment is still missing a valid start or end date, skip it
    if start < 0 or end < 0:
        return False, False

    return start, end

def get_most_common_cycle_lengths_by_drug(cleaned_treatment_data):
    cycle_lengths = {}
    for treatment in cleaned_treatment_data:
        cycle_length = treatment["frequency"]
        if cycle_length != "?" and cycle_length != "1" and cycle_length != "0":
            if treatment["name"] not in cycle_lengths:
                cycle_lengths[treatment["name"]] = []
            cycle_lengths[treatment["name"]].append(cycle_length)
    for treatment in cycle_lengths:
        lengths = []
        length_counts = []
        for length in set(cycle_lengths[treatment]):
            lengths.append(length)
            length_counts.append(cycle_lengths[treatment].count(length))
        lengths = np.array(lengths)
        length_counts = np.array(length)
        cycle_lengths[treatment] = list(lengths[np.argsort(length_counts)[::-1]])
    return cycle_lengths

def get_treatment_field_indices(fields):
    field_names = {
        "start": "startday",
        "end": "stopday",
        "route": "mmtx_route",
        "frequency": "mmtx_frequency",
        "specify_frequency": "mmtx_specify3",
        "ongoing": "mmtx_ongoing",
        "name": "mmtx_therapy",
    }
    indices = {}
    for field_name in field_names:
        indices[field_name] = fields.index(field_names[field_name])

    return indices

def get_last_visit_date(data_dir, param_dir):
    ##Get last dates to adjust for ongoing treatments
    data, fields = read_clinical_data(data_dir+"STAND_ALONE_SURVIVAL.csv", param_dir)
    end_index = fields.index("lvisitdy")
    last_date = {}
    for person in data:
        assert len(data[person]) == 1
        date = data[person][0][end_index]
        last_date[person] = int(date)
    return last_date

def get_scale_conversion(param_dir):
    scale = read_yaml(param_dir+"word_to_scale.yaml")
    return scale

def get_feature_fields(param_dir, file_type):
    valid_fields = []
    date_fields = {}
    descriptions = {}
    with open(param_dir+file_type+"_fields.csv") as fin:
        for line in fin:
            line = line.strip().split(",")
            valid_fields.append(line[0])
            descriptions[line[0]] = line[1]
            date_fields[line[0]] = line[2]
    return valid_fields, date_fields, descriptions

##Figure out what kind of feature it is
##If all values are ints and there are 2 values, it's binary
##Else if all values are ints, it's categorical
##Else if all values are floats, its numerical
##Else it's text (which makes it binary, but each value is a feature)
def get_feature_type(values):
    int_val = True
    float_val = True
    for value in values:
        if int_val:
            try:
                int(value)
            except:
                int_val = False
        if float_val:
            try:
                float(value)
            except:
                float_val = False

    ##If the values are strings
    if not int_val and not float_val:
        feature_type = "text"
    elif int_val:
        if len(set(values)) == 0 or len(set(values)) == 1:
            feature_type = "binary"
        else:
            feature_type = "categorical"
    elif float_val:
        feature_type = "continuous"

    return feature_type

def deathDays(tensor, IDX):
    death_days = []
    for person in range(tensor.shape[0]):
        days = np.where(tensor[person,:,IDX] > 0.)[0]
        if len(days) > 0:
            day = days[0]
        else:
            day = -1
        death_days.append(day)
    death_days = np.array(death_days)
    return death_days

def deathLabel(tensor, IDX):
    Y = (tensor[:,:,IDX].max(1)>0)*1.
    return Y

def PDdays(tensor, IDX):
    prog_days = []
    for person in range(tensor.shape[0]):
        days = np.where(tensor[person,:,IDX] == 6)[0]
        if len(days) > 0:
            day = days[0]
        else:
            day = -1
        prog_days.append(day)
    prog_days = np.array(prog_days)
    return prog_days

def PDlabel(tensor, IDX):
    Y = (tensor[:,:,IDX].max(1) == 6)*1.
    return Y

def obsDays(tensor):
    obs_days = []
    for person in range(tensor.shape[0]):
        days = np.where(tensor[person,:,:]==1)[0]
        if len(days) > 0:
            max_day = days.max()
        else:
            print person
        obs_days.append(max_day)
    obs_days = np.array(obs_days)
    return obs_days

def most_common_features(tensor_dir, file_type="clinical", obs=False, sort="count", cutoff=10, top=True):
    dataset = loadDataset.main(file_type, tensor_dir)

    if obs == False:
        tensor = dataset['tensor']
    else:
        tensor = dataset['obs_tensor']
    feature_key = dataset['feature_names']

    n_people, n_days, n_features = tensor.shape
    print "Shape of the " + file_type + "  matrix: " + str(n_people) + " people X " + str(n_days) + " days X " + str(n_features) + " features"

    feature_key = np.array(feature_key)

    counts = []
    values = []
    avgs = []
    for i in range(n_features):
        count = 0
        mean = 0
        people_count = 0
        for j in range(n_people):
            if tensor[j, :, i].sum():
                people_count += 1
            count += len(np.nonzero(tensor[j, :, i])[0])
            mean += tensor[j, :, i].sum()
        if mean:
            mean = mean/float(count)
        if count:
            count = count/float(people_count)
        counts.append(people_count)
        values.append(mean)
        avgs.append(count)

    if sort == "count":
        if top:
            sorted_indices = np.argsort(counts)[::-1]
        else:
            sorted_indices = np.argsort(counts)
    elif sort == "avg": 
        if top:
            sorted_indices = np.argsort(avgs)[::-1]
        else:
            sorted_indices = np.argsort(avgs)

    if cutoff:
        sorted_indices = sorted_indices[:cutoff]

    for i in sorted_indices:
        description = feature_key[i]
        if "|" in feature_key[i]:
            value = feature_key[i].split("|")[1]
            print "\t" + description + "," + value + ", recorded for " + str(np.round(counts[i], 2)) + " people, mean: " + str(np.round(values[i], 2)) + ", average count / person recorded: " + str(np.round(avgs[i]))
        else:
            print description + ", recorded for " + str(np.round(counts[i], 2)) + " people, mean: " + str(values[i]) + ", average count / person recorded: " + str(np.round(avgs[i], 2))