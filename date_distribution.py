import util
import shelve
import numpy as np
import pylab as plt

def histogram_of_dates(dates, plot_dir, save=False):
        min_dates = []
        for person in dates:
                min_dates.append(min(dates[person]))

        plt.hist(min_dates, bins=len(list(set(min_dates))))
        plt.title("Histogram of Minimum Dates")
        if save:
                plt.savefig(plot_dir+"min_date_hist.png")
        else:
                plt.show()

        plt.clf()

        max_dates = []
        for person in dates:
                max_dates.append(max(dates[person]))

        plt.hist(max_dates, bins=len(list(set(max_dates))))
        plt.title("Histogram of Maximum Dates")
        if save:
                plt.savefig(plot_dir+"max_date_hist.png")
        else:
                plt.show()

def main(file_types, override_min_date=-90, calc_min_date=False):
	
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	tensor_dir = file_paths['tensor_dir']
	param_dir = file_paths['param_dir']
	plot_dir = file_paths['plot_dir']

	with open(tensor_dir+"people_list.txt") as fin:
                people = fin.read().splitlines()

	dates = {}
	date_list = []
	for file_type in file_types:
		data, fields = util.read_clinical_data(data_dir+file_type.upper()+".csv")
		for i in range(len(fields)):
			fields[i] = fields[i].lower()
		
		date_fields = []
		with open(param_dir+file_type+"_fields.csv") as fin:
			for line in fin:
				line = line.strip().split(",")
				date_fields.append(line[1])
	
		date_fields = list(set(date_fields))
	
		for person in people:
			if person in data:
				if person not in dates:
					dates[person] = []
				for visit in data[person].values():
					for field in date_fields:
						date = util.get_date(visit, fields, field, file_type)
						if date != "no date":
							if date not in dates[person]:
								date_list.append(date)
                                                        dates[person].append(date)

	histogram_of_dates(dates, plot_dir, save=False)

	cutoffs = [0, -90, -180, -270, -360, -450]
	for cutoff in cutoffs:
		count = 0
		for date in date_list:
			if date < cutoff:
				count += 1
		print str(count) + " dates less than " + str(cutoff)

if __name__ == "__main__":
	file_types = ["stand_alone_medhx", "stand_alone_famhx", "stand_alone_ae", "per_patient", "per_patient_visit"]
	main(file_types = file_types, override_min_date=-90, calc_min_date=False)
