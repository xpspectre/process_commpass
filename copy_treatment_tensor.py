import re
import util
import shelve
import numpy as np
from scipy.sparse import csr_matrix

def get_treatment_features(data_dir, people, field_names):

	people_list = []
	lengths = []
	frequencies = []
	drugs = []
	with open(data_dir+"treatment_frequency_data.csv") as fin:
		for line in fin:
			line = line.strip().split(",")
			people_list.append(line[0])
			lengths.append(int(line[2]) - int(line[1]))
			frequencies.append(line[3])
			drugs.append(line[4])

	cycle_lengths = []
	day_lists = []	
	for i, freq in enumerate(frequencies):
		frequencies[i] = freq.replace("(", " ").replace(")", " ").replace("&", "and").replace('"', " ").replace(" ", "")
		#frequencies[i] = frequencies[i].replace(" ", "")
		#if re.compile("\d+mg").search(freq):
		#	frequencies[i] = freq.replace(re.compile("\d+mg").search(freq).group(0), "")

		cycle_lengths.append(0)
		day_lists.append([])

	strings = util.read_yaml("frequency_dictionary.yaml")

	frequencies = list(set(frequencies))	
	for frequency in frequencies:
		found = False
		for key in strings:
			for string in strings[key]:
				if string == frequency:
					found = True
		if not found:
			print frequency
		else:
			frequencies.remove(frequency)

	"""
	assert False
	for i, freq in enumerate(frequencies):
		cycle = False
		for cycle_length in sorted(list(cycle_strings)):
			for string in cycle_strings[cycle_length]:
				if string == frequencies[i]:
					cycle_lengths[i] = cycle_length
					cycle = True
					length = cycle_length
		if cycle:
			print length
			print freq
			print ""
	
	assert False

	"""
        cycle_strings = {"day": ["((for)|(of)|(each)|(every)|(q)) ?\d*[^w]+", "\d+-?d(ay)? ?cycle"], "week": ["\d+-?w((eek)|(k))? ?cycle", "((for)|(each)|(every)|(of)|(q)) ?\d*w((eek)|(k))?s?"], "month": ["((each)|(every)|(q)) ?month"]}
        for i, freq in enumerate(frequencies):
                for cycle in cycle_strings:
                        for string in cycle_strings[cycle]:
                                pattern = re.compile(string)
                                if pattern.search(freq):
                                        length = re.compile("\d+").search(pattern.search(freq).group(0))
                                        if length:
                                                length = int(length.group(0))
                                        else:
                                                length = 1
                                        if cycle == "week":
                                                length = length * 7
					elif cycle == "month":
						length = length * 30
                                        cycle_lengths[i] = length

	day_strings = {"between": ["((d(ay)?(ays)?[ ]?)|;)\d+ ?(-|to) ?\d+"], "only": ["(((day)|(days)|(d)|(;)|(and)|&)( ?\d{1,2})+)"]}
	for i, freq in enumerate(frequencies):
		for cycle in day_strings:
			for string in day_strings[cycle]:
				pattern = re.compile(string)
				if pattern.search(freq):
					for sub_text in pattern.finditer(freq):
						sub_text = sub_text.group(0)
						if cycle == "only":
							for match in re.compile("\d{1,2}").finditer(sub_text):
								match = match.group(0)
								match = re.compile('[^\d]+').sub("", match)
								day_lists[i].append(int(match))
						elif cycle == "between":
							for match in pattern.finditer(sub_text):
								match = match.group(0)
								match = re.compile('[^\dto\-]+').sub("", match)
								if "-" in match:
									match = match.split("-")
								else:
									match = match.split("to")
								for j in range(int(match[0]), int(match[1])+1):
									day_lists[i].append(j)


	for i in range(len(day_lists)):
		day_lists[i] = sorted(list(set(day_lists[i])))
		#if day_lists[i] and max(day_lists[i]) >= lengths[i]:
		#	cycle_lengths[i] = 0
		#if day_lists[i]:
		#	cycle_lengths[i] = max(day_lists[i]) 
		
	for i in range(len(day_lists)):
		for j in range(len(day_lists[i])):
			day_lists[i][j] = str(day_lists[i][j])

        values = {}
        for i in range(len(frequencies)):
		if cycle_lengths[i]:
			key = "("+",".join(day_lists[i]) + ")-" + str(cycle_lengths[i])
		else:
			key = "("+",".join(day_lists[i]) + ")-?"
                if key not in values:
                        values[key] = []
                values[key].append(frequencies[i])

	for key in values:
		print key + ":"
		for value in list(set(values[key])):
			print "\t- " + value
		print ""

	"""
	values = {}
	for i in range(len(frequencies)):
		key = frequencies[i] + "," + "|".join(day_lists[i]) + "," + str(cycle_lengths[i])
		if not(len(day_lists[i]) and cycle_lengths[i] != 0):
			print key
		if key not in values:
			values[key] = []
		values[key].append(str(lengths[i]))
	"""

def main():
	file_paths = util.get_file_paths()
	data_dir = file_paths['commpass_tensor_dir']

	with open(data_dir+"people_list.txt") as fin:
		people = fin.read().splitlines()

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

	treatment_features = get_treatment_features(data_dir, people, field_names)

if __name__ == "__main__":
	main()
