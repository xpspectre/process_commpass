import util
import shelve
import numpy as np

def main(cutoff=1):
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	output_dir = file_paths['tensor_dir']

        ##Get the data matrix and the field_names
        data, fields = util.read_clinical_data(data_dir+"PER_PATIENT_VISIT.csv")
	
	visits = {}
	for person in data:
		visits[person] = []
		for visit in data[person].values():
			if visit[fields.index("VISIT")]:
				visits[person].append(int(visit[fields.index("VISIT")]))

	count = 0
	people = []
	for person in data:
		if cutoff in visits[person]:
			people.append(person)
		else:
			count += 1
	print str(len(people)) + " people have at least 1 visit past the baseline visit."
	print str(count) + " people do not have any visits past the baseline."

	with open(output_dir+"people_list.txt", "w") as fout:
		fout.write("\n".join(people))

if __name__ == "__main__":
	main(cutoff=1)
