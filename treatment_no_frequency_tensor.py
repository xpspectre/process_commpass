import re
import util
import shelve
import numpy as np
from scipy.sparse import csr_matrix
import clinical_data_tensor as cdt

def get_treatment_features(data_dir, people, field_names, last_dates, min_date, max_date):
	data, fields = util.read_clinical_data(data_dir+"STAND_ALONE_TREATMENT_REGIMEN.csv")

	num_days = max_date - min_date + 1

	indices = {}
	for field_name in field_names:
		indices[field_name] = fields.index(field_names[field_name])

	treatment_key = []
        for person in people:
                for treatment in data[person].values():
                        name = treatment[indices["name"]].lower()
			treatment_key.append(name)
	treatment_key = list(set(treatment_key))
	treatment_key += ["autologous_sct", "allogeneic_sct"]

	num_treatments = len(treatment_key)

	frequencies = []
	lengths = []

	complete_people = []
	treatment_data = {}
	count = 0
        for person in people:
		treatment_vector = np.zeros((num_treatments, num_days))
		incomplete_data = False
                for treatment in data[person].values():	
                        frequency = treatment[indices["frequency"]].lower()+","+treatment[indices["specify_frequency"]].lower()
			name = treatment[indices["name"]].lower()

			if treatment[indices["start"]] and int(treatment[indices["start"]]) <= int(last_dates[person]):
	
				start = int(treatment[indices["start"]])

				if treatment[indices["end"]]:
					end = int(treatment[indices["end"]])
				else:
					end = int(last_dates[person])

				if end < start or start < 0:
					end = start
					incomplete_data = True
				else:
					trt_ind = treatment_key.index(name)
					for i in range(start, end+1):
						treatment_vector[trt_ind, i] = 1

		if not incomplete_data:
			treatment_data[person] = treatment_vector
			complete_people.append(person)
			frequencies.append(frequency)
			lengths.append(end - start)

        ##Add in BMT from visit data file
        data, fields = util.read_clinical_data(data_dir+"PER_PATIENT_VISIT.csv")
        date_ind = fields.index("BMT_DAYOFTRANSPL")
        auto_ind = fields.index("BMT_AUTOLOGOUS")
        allo_ind = fields.index("BMT_ALLOGENIC")
        for person in complete_people:
                for visit in data[person].values():
                        if visit[auto_ind] == "Checked":
                                trt_ind = treatment_key.index("autologous_sct")
                                date = int(visit[date_ind]) - min_date
                                treatment_data[person][trt_ind, date] = 1
                        elif visit[allo_ind] == "Checked":
                                trt_ind = treatment_key.index("allogeneic_sct")
                                date = int(visit[date_ind]) - min_date
				treatment_data[person][trt_ind, date] = 1
		print treatment_data[person].shape
		print treatment_data[person].sum()

	#for i in range(len(frequencies)):
	#	print frequencies[i] + "," + str(lengths[i])

	return treatment_data, treatment_key, complete_people

def get_last_date_in_study(data_dir, people):
	data, fields = util.read_clinical_data(data_dir+"STAND_ALONE_SURVIVAL.csv")

	#end_index = fields.index("lstalive")
	end_index = fields.index("lvisitdy")

	count = 0

	last_date = {}
	for person in people:
		assert len(data[person].values()) == 1
		date = data[person].values()[0][end_index]
		if date:
			last_date[person] = int(date)
		else:
			last_date[person] = 0
			count += 1

	print str(count) + " people without a last date recorded"

	return last_date

def main():
	file_paths = util.get_file_paths()
	data_dir = file_paths['commpass_dir']

        feature_db = shelve.open(data_dir+"clinical_data.db")
	people = feature_db['people']
	min_date = feature_db['min_date']
	max_date = feature_db['max_date']
	
	last_dates = get_last_date_in_study(data_dir, people)

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

	print len(people)
	
	treatment_data, treatment_key, valid_people = get_treatment_features(data_dir, people, field_names, last_dates, min_date, max_date)

	for elem in treatment_key:
		print elem

	##Remove people without valid treatment data from feature data
	for person in people:
		if person not in valid_people:
			del feature_db[person]
	feature_db['people'] = valid_people
	feature_db.close()

	treatment_db = shelve.open(data_dir+"treatment_data.db")
        for person in treatment_data:
                treatment_db[person] = treatment_data[person]
        treatment_db['min_date'] = min_date
        treatment_db['max_date'] = max_date
        treatment_db['feature_key'] = treatment_key
        treatment_db['people'] = valid_people
        treatment_db.close()

	print len(valid_people)

if __name__ == "__main__":
	main()
