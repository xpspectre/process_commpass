import util
import shelve
import numpy as np
import pylab as plt

def main(file_types, override_min_date=-90, calc_min_date=False):
	
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	tensor_dir = file_paths['tensor_dir']
	param_dir = file_paths['param_dir']

	with open(tensor_dir+"people_list.txt") as fin:
                people = fin.read().splitlines()

	max_date = 0
	min_date = 0
	for file_type in file_types:
		##Get the data matrix `and the field_names
		data, fields = util.read_clinical_data(data_dir+file_type.upper()+".csv")
		for i in range(len(fields)):
			fields[i] = fields[i].lower()
		
		date_fields = []
		with open(param_dir+file_type+"_fields.csv") as fin:
			for line in fin:
				line = line.strip().split(",")
				date_fields.append(line[1])
	
		date_fields = list(set(date_fields))
	
		max_date = 0
		min_date = 0
		for person in people:
			if person in data:
				for visit in data[person].values():
					for field in date_fields:
						date = util.get_date(visit, fields, field, file_type)
						if date != "no date":
							min_date = min(date, min_date)
							max_date = max(date, max_date)

	##You could change this to only record data after the start of the study or a date before the start of the study
	if not calc_min_date:
		min_date = override_min_date

	num_days = max_date - min_date + 1
	print "Min date: " + str(min_date)
	print "Max date: " + str(max_date)
	print "Num days: " + str(num_days)

	with open(tensor_dir+"date_range.txt", "w") as fout:
		fout.write(str(min_date)+"\n"+str(max_date))

if __name__ == "__main__":
	file_types = ["stand_alone_medhx", "stand_alone_famhx", "stand_alone_ae", "per_patient", "per_patient_visit"]
	main(file_types = file_types, override_min_date=-90, calc_min_date=False)
