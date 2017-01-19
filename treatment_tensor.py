import re
import util
import shelve
import numpy as np
from scipy.sparse import csr_matrix

def main():
        file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	param_dir = file_paths['param_dir']
        tensor_dir = file_paths['tensor_dir']

        with open(tensor_dir+"people_list.txt") as fin:
                people = fin.read().splitlines()

	with open(tensor_dir+"date_range.txt") as fin:
		min_date = int(fin.readline())
		max_date = int(fin.readline())
	num_days = max_date - min_date + 1

        strings = util.read_yaml(param_dir+"frequency_dictionary.yaml")

	people_list = []
	lengths = []
	frequencies = []
	drugs = []
	doses = []
	starts = []
	ends = []
	with open(tensor_dir+"treatment_frequency_data.csv") as fin:
		for line in fin:
			line = line.strip().split(",")
			people_list.append(line[0])
			starts.append(int(line[1]))
			ends.append(int(line[2]))
			lengths.append(int(line[2]) - int(line[1]))
			frequencies.append(line[3].replace("(", " ").replace(")", " ").replace("&", "and").replace('"', " ").replace(" ", ""))
			drugs.append(line[4])
			doses.append(float(line[5]))

	cycles = {}
	for i in range(len(frequencies)):
		for pattern in strings:
			for string in strings[pattern]:
				if frequencies[i] == string:
					if drugs[i] not in cycles:
						cycles[drugs[i]] = []
					cycles[drugs[i]].append(pattern.split("-")[1])

	frequent_cycles = []
	cycs = {}
	for drug in cycles:
		cyc_lens = []
		cyc_counts = []
		for cyc in list(set(cycles[drug])):
			if cyc != "?" and cyc != "1" and cyc != "0":
				cyc_lens.append(int(cyc))
				cyc_counts.append(cycles[drug].count(cyc))
		cyc_lens = np.array(cyc_lens)
		cyc_counts = np.array(cyc_counts)
		cycs[drug] = list(cyc_lens[np.argsort(cyc_counts)[::-1]])

	cycle_lengths = []
	dose_patterns = []
        for i in range(len(frequencies)):
		length_found = False
		count = 0
                for pattern in strings:
                        for string in strings[pattern]:
                                if frequencies[i] == string:
					count += 1
					frequency = pattern.split("-")[1]
					pattern = pattern.split("-")[0].replace("(", "").replace(")", "").split(",")
					for j in range(len(pattern)):
						pattern[j] = int(pattern[j])
					dose_patterns.append(pattern)
					
					if frequency != "?":
						cycle_lengths.append(int(frequency))
						length_found = True
					else:
						for length in cycs[drug]:
							if length >= max(pattern):
								cycle_lengths.append(int(length))
								length_found = True
								break
						if not length_found:
							cycle_lengths.append(max(pattern))
							length_found = True
		
		##If unknown, assume given daily
		if not length_found:
			cycle_lengths.append(1)
			dose_patterns.append(1)

	assert len(cycle_lengths) == len(dose_patterns)
	assert len(cycle_lengths) == len(frequencies)

        ##Add in BMT from visit data file
        data, fields = util.read_clinical_data(data_dir+"PER_PATIENT_VISIT.csv")
        date_ind = fields.index("BMT_DAYOFTRANSPL")
        auto_ind = fields.index("BMT_AUTOLOGOUS")
        allo_ind = fields.index("BMT_ALLOGENIC")
        for person in people:
                for visit in data[person].values():
                        if visit[auto_ind] == "Checked":
				people_list.append(person)
                                date = int(visit[date_ind])
				starts.append(date)
				ends.append(date)
				drugs.append("autologous_sct")
				doses.append(1)
				cycle_lengths.append(0)
				dose_patterns.append([1])
                        elif visit[allo_ind] == "Checked":
                                people_list.append(person)
                                date = int(visit[date_ind])
                                starts.append(date)
                                ends.append(date)
                                drugs.append("allogeneic_sct")
                                doses.append(1)
                                cycle_lengths.append(0)
                                dose_patterns.append([1])

	treatment_key = list(set(drugs))
	with open(tensor_dir+"treatment_key.txt", "w") as fout:
		fout.write("\n".join(treatment_key))
	num_treatments = len(treatment_key)

	tensor = []
	for person in people:
		treatment_matrix = treatment_vector = np.zeros((num_treatments, num_days))
		count = 0
		treatment_counts = {}
		for treatment in treatment_key:
			treatment_counts[treatment] = 0

		for i in range(len(people_list)):
			if people_list[i] == person:
				drug_index = treatment_key.index(drugs[i])

				start = starts[i] - min_date
				end = ends[i] - min_date
				date = start
				cycle_ind = 0

				while date <= end:
					treatment_matrix[drug_index, date] = doses[i]
					count += 1
					treatment_counts[drugs[i]] += 1

					date = start + dose_patterns[i][cycle_ind]
					if cycle_ind == len(dose_patterns[i])-1 and cycle_lengths[i] != 0:
						cycle_ind = 0						
						start += cycle_lengths[i]
					elif cycle_lengths[i] == 0:
						date = end + 1
					else:
						cycle_ind += 1
		tensor.append(treatment_matrix)

	tensor = np.array(tensor)

        outfile = open(tensor_dir+"treatment_data_tensor.npz", "w")
        np.savez(outfile, tensor=tensor)

if __name__ == "__main__":
	main()
