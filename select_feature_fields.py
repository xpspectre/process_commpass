import util
import shelve
import numpy as np

def get_fields(fields, field_descriptions, prefixes, prefix_descriptions, date_strings, remove_strings, verbose=False):
	##Get fields without any exclusion strings
	valid_fields = []
	for field in fields:
		if field[0] == "d": 
			field_prefix = "_".join(field.split("_")[:2])
		else:   
			field_prefix = field.split("_")[0]

		if field_prefix in prefixes:
			remove = False
			for string in remove_strings:
				if string in field_descriptions[field]:
					remove = True
					break
			if not remove:
				valid_fields.append(field)

	if verbose:
		print "Selected Fields:"
		for field in valid_fields:
			if field[0] == "d":
				field_prefix = "_".join(field.split("_")[:2])
			else:
				field_prefix = field.split("_")[0]
			print prefix_descriptions[field_prefix] + ": " + field_descriptions[field]

		print "\nRemoved Fields:"
		for field in fields:
			if field not in valid_fields:
				if field[0] == "d":
					field_prefix = "_".join(field.split("_")[:2])
				else:
					field_prefix = field.split("_")[0]
				if field_prefix in prefix_descriptions:
					print prefix_descriptions[field_prefix] + ": " + field_descriptions[field]
				else:
					print field_descriptions[field]


	return valid_fields

def get_date_fields(fields, field_descriptions, date_strings, valid_fields, verbose=False):
        ##Get the date fields for each prefix that has a corresponding date and the date field for the visit
        visit_date = ""
        date_fields = {}
        for field in fields:
                for date_string in date_strings:
                        if date_string in field_descriptions[field]:
                                ##Get the field prefix
                                if field[0] == "d":
                                        field_prefix = "_".join(field.split("_")[:2])
                                else:
                                        field_prefix = field.split("_")[0]
                                ##Record the first date field as the date
                                if not visit_date:
                                        visit_date = field
                                ##Otherwise record the first date field of each prefix as the date field for that group of fields
                                elif field_prefix not in date_fields:
                                        date_fields[field_prefix] = field

        dates = {}
        for field in valid_fields:
			##Get the prefix
                        if field[0] == "d":
                                field_prefix = "_".join(field.split("_")[:2])
                        else:
                                field_prefix = field.split("_")[0]

			##Assign the associated date field, or the visit date field if there is none
			if field_prefix in date_fields:
				dates[field] = date_fields[field_prefix]
			else:
				dates[field] = visit_date

	return dates

def get_prefix_descriptions(file_type, data_dir):
        ##Get the list of field prefixes to use as features
        prefixes = []
        prefix_descriptions = {}
        with open(data_dir+file_type+"_field_prefixes.txt") as fin:
                for line in fin:
                        prefix = line.strip().split(",")[0].lower()
                        prefixes.append(prefix)
                        prefix_descriptions[prefix] = ",".join(line.strip().split(",")[1:]).lower()
	return prefixes, prefix_descriptions

def get_field_descriptions(file_type, data_dir):
        ##Get the list of fields and descriptions
        field_descriptions = {}
        with open(data_dir+file_type+"_field_descriptions.csv") as fin:
                for line in fin:
                        line = line.strip().split(",")
                        field_descriptions[line[0].lower()] = ",".join(line[1:]).lower()
	return field_descriptions

def get_data_types(file_type, fields, data_dir):
        ##Get the types of the fields
        data_types = {}
        with open(data_dir+file_type+"_datatypes.txt") as fin:
                i = 0
                for line in fin:
                        data_types[fields[i]] = line.strip()
                        i += 1
	return data_types

def main():
	file_paths = util.get_file_paths()
	data_dir = file_paths['data_dir']
	param_dir = file_paths['param_dir']
	tensor_dir = file_paths['tensor_dir']

	file_type = "per_patient_visit"
	verbose = False

        ##Get the list of field prefixes to use as features
        prefixes, prefix_descriptions = get_prefix_descriptions(file_type, param_dir)
	field_descriptions = get_field_descriptions(file_type, data_dir)

        ##Get the data mtrix and the field_names
        data, fields = util.read_clinical_data(data_dir+file_type.upper()+".csv")
        for i in range(len(fields)):
                fields[i] = fields[i].lower()

	##Get the types of the fields
	data_types = get_data_types(file_type, fields, data_dir)

	##Strings that indicate a date in the field descriptions
	with open(param_dir+"date_strings.txt") as fin:
                date_strings = fin.read().splitlines()
	##Strings with metadata about the patient/tests
	with open(param_dir+"meta_data_strings.txt") as fin:
		meta_data_strings = fin.read().splitlines()

	##Get valid fields and corresponding date fields
	valid_fields = get_fields(fields, field_descriptions, prefixes, prefix_descriptions, date_strings, meta_data_strings, verbose=verbose)
	dates = get_date_fields(fields, field_descriptions, date_strings, valid_fields, verbose=verbose)

	#with open(tensor_dir+file_type+"_valid_fields.txt", "w") as fout:
	#	fout.write("\n".join(valid_fields))

	with open(param_dir+file_type+"_fields.csv", "w") as fout:
		for date_field in dates:
			fout.write(date_field+","+dates[date_field]+","+data_types[date_field]+"\n")

if __name__ == "__main__":
	main()
