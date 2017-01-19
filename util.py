import re
import yaml
import numpy as np

def get_file_paths(path_fname="file_paths.txt"):
	paths = {}
	with open(path_fname, 'r') as fin:
		for line in fin:
			line = line.strip().split(':')
			paths[line[0]] = line[1]
 	return paths

def read_yaml(fname):
        with open(fname, 'rb') as fin:
                return yaml.load(fin)

def read_clinical_data(fname):
        patient_data = {}
	n_visits = {}
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
                for line in data[1:]:
                        if line:
                                line = line.strip().split(",")
                                pid = line[0]
                                if pid not in patient_data.keys():
                                        patient_data[pid] = {}
					n_visits[pid] = 0
				patient_data[pid][n_visits[pid]] = line
				n_visits[pid] += 1
        return patient_data, fields

def get_field_key(fname):
	key = {}
        with open(fname, "r") as fin:
		for line in fin:
			line = line.strip().split(",")
			key[line][1] = line[1:]
	return key
	
def get_field_names_and_types(fname, field_indices):
	field_names = []
        with open(fname) as fin:
		count = 0
                for line in fin:
			if count in field_indices:
				line = line.strip().split(",")	
				field_names.append(",".join(line[2:]))
			count += 1
	return field_names

def get_date(visit, fields, date_field, file_type):
        if file_type != "per_patient_visit" and file_type != "stand_alone_ae":
                date = 0
	elif visit[fields.index(date_field)]:
		date = int(visit[fields.index(date_field)])
	elif "visitdy" in fields and visit[fields.index("visitdy")]:
		date = int(visit[fields.index("visitdy")])
	else:
		if "Month" == visit[fields.index("vj_interval")].split(" ")[0]:
			num = int(re.sub("\D", "", visit[fields.index("vj_interval")]))
			date = 30 * num
		elif "Year" == visit[fields.index("vj_interval")].split(" ")[0]:
			num = int(re.sub("\D", "", visit[fields.index("vj_interval")]))
			date = 365 * num
		elif "Baseline" == visit[fields.index("vj_interval")].split(" ")[0] or "Screening" == visit[fields.index("vj_interval")].split(" ")[0]:
			date = 0
		else:
			date = "no date"
	return date

def get_height_weight(data_dir, people):
	data, fields = read_clinical_data(data_dir+"PER_PATIENT.csv")

	weight_ind = fields.index("DEMOG_WEIGHT")
	weight_unit_ind = fields.index("DEMOG_WEIGHTUNITOFM")
	
        height_ind = fields.index("DEMOG_HEIGHT")  
        height_unit_ind = fields.index("DEMOG_HEIGHTUNITOFM")

	heights = {}
	weights = {}
	for person in people:
		visit = data[person].values()[0]

		weight = int(visit[weight_ind])
		if visit[weight_unit_ind] == "lb":
			weight = weight * (1/2.2)

                height = int(visit[height_ind])
                if visit[height_unit_ind] == "in":
                        height = height * 2.54

		heights[person] = height
		weights[person] = weight

	return heights, weights
