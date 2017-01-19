import util
from scipy.sparse import csr_matrix
import numpy as np

def main(file_types):
	file_paths = util.get_file_paths()
	tensor_dir = file_paths['tensor_dir']
	param_dir = file_paths['param_dir']

	feature_key = []
	feature_list = []
	for file_type in file_types:
		with open(tensor_dir+file_type+"_feature_key.csv") as fin:
			feature_key += fin.read().splitlines()
                with open(tensor_dir+file_type+"_raw_feature_list.csv") as fin:
                        feature_list += fin.read().splitlines()
	n_features = len(feature_key)

	feature_list = list(set(feature_list))

	with open(tensor_dir+"date_range.txt") as fin:
		min_date = int(fin.readline().strip())
		max_date = int(fin.readline().strip())
        n_days = max_date - min_date + 1

        with open(tensor_dir+"people_list.txt") as fin:
                people = fin.read().split()
	n_people = len(people)

	feature_tensor = np.zeros((n_people, n_days, n_features))
        dates = {}
        for file_type in file_types:
                with open(param_dir+file_type+"_fields.csv") as fin:
                        for line in fin:
                                line = line.strip().split(",")
                                dates[line[0]] = line[1]

        for feature in feature_list:
                feature = feature.split(",")
                person_ind = people.index(feature[0])
                day_ind = int(feature[1])
                feature_ind = feature_key.index(feature[2])
                value = float(feature[3])
                feature_tensor[person_ind, day_ind, feature_ind] = value

        outfile = open(tensor_dir+"feature_tensor.npz", "w")
        np.savez(outfile, tensor=feature_tensor)
	
	del feature_tensor

        with open(tensor_dir+"feature_key.csv", "w") as fout:
                fout.write("\n".join(feature_key))

	observation_tensor = np.zeros((n_people, n_days, n_features), dtype="bool")
        dates = {}
	for file_type in file_types:
		with open(param_dir+file_type+"_fields.csv") as fin:
			for line in fin:
				line = line.strip().split(",")
				dates[line[0]] = line[1]

	for feature in feature_list:
		feature = feature.split(",")
		person_ind = people.index(feature[0])
		day_ind = int(feature[1])
		feature_ind = feature_key.index(feature[2])
		value = float(feature[3])
		if value != 0:
			observation_tensor[person_ind, day_ind, feature_ind] = True

	print observation_tensor.sum()
	print len(feature_list)
	
        outfile = open(tensor_dir+"observation_tensor.npz", "w")
        np.savez(outfile, tensor=observation_tensor)

	del observation_tensor

if __name__ == "__main__":
	file_types = ["stand_alone_medhx", "stand_alone_famhx", "stand_alone_ae", "per_patient", "per_patient_visit"]
	main(file_types)
