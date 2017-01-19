file_types = ["stand_alone_medhx", "stand_alone_famhx", "stand_alone_ae", "per_patient", "per_patient_visit"]

import person_inclusion_exclusion
visit_cutoff = 1
person_inclusion_exclusion.main(cutoff=visit_cutoff)

import select_feature_fields
select_feature_fields.main()

import date_range
min_date = -180
calc_min_date=False
date_range.main(file_types=file_types, override_min_date=min_date, calc_min_date=calc_min_date)

import feature_list
import feature_dates_and_values
min_occurences = 10
for file_type in file_types:
	feature_list.main(file_type=file_type, min_occurences=min_occurences, verbose=True)
	feature_dates_and_values.main(file_type=file_type)

import feature_tensor
feature_tensor.main(file_types)

import missing_treatment_end_dates
missing_treatment_end_dates.main()

import treatment_tensor
treatment_tensor.main()
