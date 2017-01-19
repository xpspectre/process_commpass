import re
import util
import shelve
import numpy as np
import pylab as plt
from scipy.sparse import csr_matrix

def build_feature_list(file_type, data, fields, people, num_days, min_date, max_date, feature_key, date_fields, uncertain_responses, value_possibilities, values, verbose=False):
	num_features = len(feature_key)
	date_diffs = []
	count = 0
	n = 0
	features = []
	for person in people:
		if person in data:
			for i, visit in enumerate(data[person].values()):
				for j in range(len(fields)):
					if fields[j] in value_possibilities:
						visit[j] = visit[j].lower().replace(' ', '').replace("*", "")
						if visit[j] in uncertain_responses:
							visit[j] = ""
						
						if visit[j] != "" and visit[j] != "0":
							date = util.get_date(visit, fields, date_fields[fields[j]], file_type)	
							if date != "no date" and date >= min_date and date <= max_date:
								date = date - min_date

							if value_possibilities[fields[j]] == "numerical":
								if visit[j] in values:
									visit[j] = float(values[visit[j]])
								elif visit[j]:
									visit[j] = float(visit[j])
								features.append(person+","+str(date)+","+fields[j]+","+str(visit[j]))
							else:
								if visit[j] in value_possibilities[fields[j]]:
									features.append(person+","+str(date)+","+fields[j]+"|"+str(visit[j])+",1")
	return features

def get_prefix_descriptions(file_type, data_dir):
        ##Get the list of field prefixes to use as features
        prefixes = []
        prefix_descriptions = {}
        with open(data_dir+file_type+"_field_prefixes.txt") as fin:
                for line in fin:
                        prefix = line.strip().split(",")[0].lower()
                        prefixes.append(prefix)
                        prefix_descriptions[prefix] = ",".join(line.strip().split(",")[1:]).lower()
	return prefixes, prefix_descriptions

def get_field_descriptions(file_type, data_dir):
        ##Get the list of fields and descriptions
        field_descriptions = {}
        with open(data_dir+file_type+"_field_descriptions.csv") as fin:
                for line in fin:
                        line = line.strip().split(",")
                        field_descriptions[line[0].lower()] = ",".join(line[1:]).lower()
	return field_descriptions

def main(file_type, verbose=False):
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	tensor_dir = file_paths['tensor_dir']
	param_dir = file_paths['param_dir']

        ##Treat these as zeros
	with open(param_dir+"uncertain_strings.txt") as fin:
		uncertain_responses = fin.read().splitlines()

	value_possibilities = {}
	feature_key = []
	with open(tensor_dir+file_type+"_feature_key.csv") as fin:
		for line in fin:
			feature_key.append(line.strip())
			line = line.strip().split("|")
			if len(line) == 1:
				value_possibilities[line[0]] = "numerical"
			else:
				if line[0] not in value_possibilities:
					value_possibilities[line[0]] = []
				value_possibilities[line[0]].append(line[1])

	with open(tensor_dir+"people_list.txt") as fin:
                people = fin.read().splitlines()

	##Read in the dictionary for converting some text values to numerical scales
        values = util.read_yaml(param_dir+"word_to_scale.yaml")

        ##Get the data matrix and the field_names
        data, fields = util.read_clinical_data(data_dir+file_type.upper()+".csv")
        for i in range(len(fields)):
                fields[i] = fields[i].lower()

        dates = {}
        with open(param_dir+file_type+"_fields.csv") as fin:
                for line in fin:
                        line = line.strip().split(",")
                        dates[line[0]] = line[1]
	
	with open(tensor_dir+"date_range.txt") as fin:
		min_date = int(fin.readline().strip())
		max_date = int(fin.readline().strip())
	
	num_days = max_date - min_date + 1
	print "Min date: " + str(min_date)
	print "Max date: " + str(max_date)

	##Build the tensor
	features = build_feature_list(file_type, data, fields, people, num_days, min_date, max_date, feature_key, dates, uncertain_responses, value_possibilities, values, verbose=verbose)

	with open(tensor_dir+file_type+"_raw_feature_list.csv", "w") as fout:
		fout.write("\n".join(features))

if __name__ == "__main__":
	main(file_type="per_patient")
