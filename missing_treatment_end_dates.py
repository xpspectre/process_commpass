import re
import util
import shelve
import numpy as np
import pylab as plt
from scipy.sparse import csr_matrix

def get_treatment_features(data_dir, tensor_dir, people, field_names, last_dates):
	response_data, response_fields = util.read_clinical_data(data_dir+"STAND_ALONE_TRTRESP.csv")

	data, fields = util.read_clinical_data(data_dir+"STAND_ALONE_TREATMENT_REGIMEN.csv")

	indices = {}
	for field_name in field_names:
		indices[field_name] = fields.index(field_names[field_name])

	patterns = []
	count = 0

	heights, weights = util.get_height_weight(data_dir, people)

	d = {}

        treatments = {}
	for person in people:
		treatments[person] = {"starts":[], "ends":[], "drugs":[], "frequencies": [], "doses": []}
                for treatment in data[person].values():	
			if treatment[indices["frequency"]] == "Oth":
				frequency = treatment[indices["specify_frequency"]].lower()
			else:
				frequency = treatment[indices["frequency"]].lower()
			frequency = frequency.replace(",", "|")
			name = treatment[indices["name"]].lower()

			try:
				dose = float(treatment[indices["dose"]])
				if treatment[indices["units"]].lower() == "mg/m^":
					dose = dose * np.sqrt(heights[person] * weights[person] / 3600)
				elif treatment[indices["units"]].lower() == "mg/kg":
					dose = dose * weights[person]
				#elif treatment[indices["units"]].lower() != "mg":
				#	print treatment[indices["units"]].lower()
				#	print dose
				#	print name
				#	print ""


				if name not in d:
					d[name] = []
				d[name].append(dose)
			except:
				print treatment

			if not name:
				continue

			start = int(treatment[indices["start"]])
			if treatment[indices["ongoing"]] == "Checked":
				end = int(last_dates[person])
			else:
				end = int(treatment[indices["end"]])

			if start > last_dates[person]:
				continue

			if (start < 0 and end < 0) or frequency == "unk" or frequency == "unknown":
				continue

			trt = False
                        if start < 0:
                                for combination in response_data[person].values():
                                        if int(combination[response_fields.index("trtstdy")]) <= end and int(combination[response_fields.index("trtendy")]) >= end and name in combination[response_fields.index("trtname")].lower():
                                                start = int(combination[response_fields.index("trtstdy")])
						trt = True
						break

			if end < 0:
				for combination in response_data[person].values():
					if int(combination[response_fields.index("trtstdy")]) <= start and int(combination[response_fields.index("trtendy")]) >= start and name in combination[response_fields.index("trtname")].lower():
						end = int(combination[response_fields.index("trtendy")])
						trt = True
						break

			if trt:
				count += 1

			if start < 0 or end < 0:
				continue

			treatments[person]["ends"].append(end)
			treatments[person]["starts"].append(start)
			treatments[person]["drugs"].append(name)
			treatments[person]["frequencies"].append(frequency)
			treatments[person]["doses"].append(dose)

	with open(tensor_dir+"treatment_frequency_data.csv", "w") as fout:
		for person in treatments:
			for i in range(len(treatments[person]["starts"])):
				fout.write(person+","+str(treatments[person]["starts"][i])+","+str(treatments[person]["ends"][i])+","+treatments[person]["frequencies"][i]+","+treatments[person]["drugs"][i]+","+str(treatments[person]["doses"][i])+"\n")
	
def get_last_visit_date(data_dir, people):
	data, fields = util.read_clinical_data(data_dir+"STAND_ALONE_SURVIVAL.csv")
	for i in range(len(fields)):
		fields[i] = fields[i].lower()

	end_index = fields.index("lvisitdy")
	last_date = {}
	for person in people:
		assert len(data[person].values()) == 1
		date = data[person].values()[0][end_index]
		last_date[person] = int(date)
	return last_date

def main():
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	tensor_dir = file_paths['tensor_dir']

	with open(tensor_dir+"people_list.txt") as fin:
		people = fin.read().splitlines()

	print str(len(people)) + " people"
	last_dates = get_last_visit_date(data_dir, people)

        field_names = {
                "start": "startday",
                "end": "stopday",
                "route": "MMTX_ROUTE",
                "frequency": "MMTX_FREQUENCY",
                "specify_frequency": "MMTX_SPECIFY3",
                "dose": "MMTX_DOSE",
                "units": "MMTX_UNITS",
                "ongoing": "MMTX_ONGOING",
                "name": "MMTX_THERAPY"
        }

	treatment_features = get_treatment_features(data_dir, tensor_dir, people, field_names, last_dates)

if __name__ == "__main__":
	main()
