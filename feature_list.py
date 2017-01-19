import util
import shelve
import numpy as np

def get_valid_text_fields(file_type, data, fields, people, data_types, cutoff, uncertain_responses, values, valid_fields, date_fields, min_date, max_date, verbose=False):
	##Mark numerical fields as such, save the text fields for further analysis
	char_fields = []
	char_indices = []
	value_possibilities = {}
	for i, field in enumerate(fields):
		if field in valid_fields:
			if data_types[field] == "Char":
				char_indices.append(i)
				char_fields.append(field)

	##Convert values to lower case, remove spaces and turn scale text values into the correpsonding numerical values
	for i in range(len(fields)):
		if fields[i] in valid_fields:
			numerical = True
			count = 0
			for person in people:
				if person in data:
					for visit in data[person].values():
						date = util.get_date(visit, fields, date_fields[fields[i]], file_type)
						if date != "no date" and date >= min_date and date <= max_date:
							if i in char_indices:
								##Clean up the text values
								visit[i] = visit[i].lower().replace(' ', '')

								##Record these as blank
								if visit[i] in uncertain_responses:
									visit[i] = ''

								##Convert these to a numerical scale and treat them as numerical values
								if visit[i] != "":
									if fields[i] not in value_possibilities:
										value_possibilities[fields[i]] = {}
									if visit[i] not in value_possibilities[fields[i]]:
										value_possibilities[fields[i]][visit[i]] = []
									value_possibilities[fields[i]][visit[i]].append(person)
								numerical = False
							elif visit[i] != "0" and visit[i] != "":
								if fields[i] not in value_possibilities:
									value_possibilities[fields[i]] = []
								value_possibilities[fields[i]].append(person)

			if numerical and fields[i] in value_possibilities and len(set(value_possibilities[fields[i]])) >= cutoff:
				value_possibilities[fields[i]] = "numerical"
			elif numerical:
				if fields[i] in value_possibilities:
					del value_possibilities[fields[i]]
				print fields[i]

	num_features = 0
	num_text_fields = 0
	num_numerical_fields = 0
	for field in value_possibilities.keys():
		num = True
		if type(value_possibilities[field]) == dict:
			temp = []
			for value in value_possibilities[field]:
				temp += value_possibilities[field][value]
				if value not in values:
					num = False
			if num:
				value_possibilities[field] = temp
			else:
				infrequent_values = []
				for value in value_possibilities[field]:
					if len(set(value_possibilities[field][value])) < cutoff:
						infrequent_values.append(value)
				for value in infrequent_values:
					print field + ": "+ value
					print len(set(value_possibilities[field][value])) 
				value_possibilities[field] = list(set(value_possibilities[field].keys()).difference(set(infrequent_values)))
				num_features += len(value_possibilities[field])
				if len(value_possibilities[field]) == 0:
					del value_possibilities[field]
				else:
					num_text_fields += 1
		if num:
			if value_possibilities[field] == "numerical" or len(set(value_possibilities[field])) >= cutoff:
				value_possibilities[field] = "numerical"
				num_features += 1
				num_numerical_fields += 1
			else:
				print field
				print set(value_possibilities[field])
				print len(set(value_possibilities[field]))
				del value_possibilities[field]

	if verbose:
		print str(num_features) + " total features including numerical features and text features occuring at least " + str(cutoff) + " times."
		print str(num_text_fields) + " text fields meet the cutoff for at least 1 value that occurs at least " + str(cutoff) + " times and " + str(num_numerical_fields) +  " numerical fields."

		#for field in value_possibilities:
		#	print field + ": " + str(value_possibilities[field])
	
	return value_possibilities

def get_feature_key(value_possibilities):
        feature_key = []
        for field in value_possibilities:
                if value_possibilities[field] == "numerical":
                        feature_key.append(field)
                else:
                        for value in value_possibilities[field]:
                                feature_key.append(field+"|"+value)
        return feature_key

def main(file_type, min_occurences=10, verbose=False):
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	tensor_dir = file_paths['tensor_dir']
	param_dir = file_paths['param_dir']

        ##Treat these as zeros
	with open(param_dir+"uncertain_strings.txt") as fin:
		uncertain_responses = fin.read().splitlines()
        ##Read in the dictionary for converting some text values to numerical scales
        values = util.read_yaml(param_dir+"word_to_scale.yaml")

        dates = {}
        with open(param_dir+file_type+"_fields.csv") as fin:
                for line in fin:
                        line = line.strip().split(",")
                        dates[line[0]] = line[1]

	valid_fields = []
	dates = {}
	data_types = {}
	with open(param_dir+file_type+"_fields.csv") as fin:
		for line in fin:
			line = line.strip().split(",")
			valid_fields.append(line[0])
			dates[line[0]] = line[1]
			data_types[line[0]] = line[2]

        with open(tensor_dir+"people_list.txt") as fin:
                people = fin.read().splitlines()

        with open(tensor_dir+"date_range.txt") as fin:
                min_date = int(fin.readline().strip())
                max_date = int(fin.readline().strip())

        ##Get the data matrix and the field_names
        data, fields = util.read_clinical_data(data_dir+file_type.upper()+".csv")
        for i in range(len(fields)):
                fields[i] = fields[i].lower()

	##Get all the possible text values for each field, or mark them as numerical
	value_possibilities = get_valid_text_fields(file_type, data, fields, people, data_types, min_occurences, uncertain_responses, values, valid_fields, dates, min_date, max_date, verbose=verbose)

        ##Get the feature key from the possible values of each field
        feature_key = get_feature_key(value_possibilities)

	with open(tensor_dir+file_type+"_feature_key.csv", "w") as fout:
		fout.write("\n".join(feature_key))

if __name__ == "__main__":
	main(file_type="per_patient_visit", min_occurences=10, verbose=True)
