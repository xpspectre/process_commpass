import util
import shelve
import numpy as np
import pylab as plt
from scipy.sparse import csr_matrix
import select_feature_fields as sff

def main(file_type="feature", sort="count"):
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	tensor_dir = file_paths['tensor_dir']

	tensor = np.load(tensor_dir+file_type+"_tensor.npz")['tensor']

	n_people, n_days, n_features = tensor.shape
	print "Shape of the matrix matrix: " + str(n_people) + " people X " + str(n_days) + " days X " + str(n_features) + " features"

	with open(tensor_dir+file_type+"_key.csv") as fin:
		feature_key = fin.read().splitlines()
	feature_key = np.array(feature_key)

	counts = []
	values = []
	avgs = []
	for i in range(n_features):
		count = 0
		mean = 0
		people_count = 0
		for j in range(n_people):
			if tensor[j, :, i].sum():
				people_count += 1
			count += tensor[j, :, i].astype(bool).sum()
			mean += tensor[j, :, i].sum()
                if mean:
                        mean = mean/float(count)
		if count:
			count = count/float(people_count)
		counts.append(people_count)
		values.append(mean)
		avgs.append(count)

	if sort == "count":
		sorted_indices = np.argsort(counts)[::-1]
	elif sort == "avg":	
		sorted_indices = np.argsort(avgs)[::-1]

	for i in sorted_indices:
		description = feature_key[i].split("|")[0]
		if "|" in feature_key[i]:
			value = feature_key[i].split("|")[1]
			print description + "," + value + ", recorded for " + str(counts[i]) + " people, mean: " + str(values[i]) + ", average count / person recorded: " + str(avgs[i])
		else:
			print description + ", recorded for " + str(counts[i]) + " people, mean: " + str(values[i]) + ", average count / person recorded: " + str(avgs[i])

if __name__ == "__main__":
	main()
