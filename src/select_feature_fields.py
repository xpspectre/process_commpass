import os
import util
import xlrd
import numpy as np

def get_descriptions(desc_dir):
    file_names = os.listdir(desc_dir)
    descriptions = {}
    for fname in file_names:
        if ".xlsx" in fname:
            descriptions[fname.replace(".xlsx", "").lower()] = {}
            sheet = xlrd.open_workbook(desc_dir+fname).sheet_by_index(0)
            for row in range(sheet.nrows):
                row = sheet.row_values(row)[1:4]
                row = "|".join(row).encode('ascii', 'ignore').split("|")
                descriptions[fname.replace(".xlsx", "").lower()][row[0].lower()] = row[1].lower().replace(",", ";")
    return descriptions

def main(file_names, invalid_strings, baseline_cutoff, temporal_frac, data_dir, param_dir, desc_dir):
    descriptions = get_descriptions(desc_dir)
    for fname in file_names:    
        potential_features = {}
        dates = {}

        data, fields = util.read_clinical_data(data_dir+fname.upper()+".csv", param_dir)

        for field in fields:
            if "_" in field:
                if field[:2] == "d_":
                    prefix = "_".join(field.split("_")[:2])
                else:
                    prefix = "_".join(field.split("_")[:1])
            else:
                prefix = "none_"

            if "date" in field or "date" in descriptions[fname][field]:
                ##Hard code these 2 edge cases
                if fname == "stand_alone_treatment_regimen" and field == "stopday":
                    dates[prefix] = field
                if fname == "stand_alone_ae" and field == "lvisitdy":
                    dates[prefix] = field
                elif prefix not in dates:
                    dates[prefix] = field
            else:
                valid = True
                for invalid_string in invalid_strings:
                    if invalid_string in field or invalid_string in descriptions[fname][field]:
                        valid = False

                if valid:
                    if prefix not in potential_features:
                        potential_features[prefix] = []
                    potential_features[prefix].append(field)

        ##Hard code this edge case
        if fname == "per_patient":
            dates["none_"] = "BASELINE"

        features = {}
        feature_dates = {}
        for prefix in potential_features:
            if prefix in dates:
                date_field = dates[prefix]
            elif "none_" in dates:
                date_field = dates["none_"]
            else:
                date_field = "BASELINE"
            for feature in potential_features[prefix]:
                features[feature] = {"date_field": date_field, "description": descriptions[fname][feature]}
                feature_dates[feature] = {"temporal": 0, "baseline": 0}

        for person in data:
            for visit in data[person]:
                for field in features:
                    if visit[fields.index(field)] != "":
                        date = util.get_date(visit, fields, features[field]["date_field"], fname)
                        if date != "no date":
                            if date > baseline_cutoff:
                                feature_dates[field]["temporal"] += 1
                            else:
                                feature_dates[field]["baseline"] += 1

        baseline_features = []
        temporal_features = []
        for feature in features:
            if feature_dates[feature]["temporal"] + feature_dates[feature]["baseline"] == 0:
                continue
            elif feature_dates[feature]["baseline"] == 0 or feature_dates[feature]["temporal"]/float(feature_dates[feature]["baseline"]) >= temporal_frac:
                temporal_features.append(feature+","+features[feature]["description"]+","+features[feature]["date_field"])
            elif feature_dates[feature]["temporal"] == 0 or feature_dates[feature]["temporal"]/float(feature_dates[feature]["baseline"]) < temporal_frac:
                if fname == "per_patient_visit":
                    baseline_features.append(feature+","+features[feature]["description"]+","+features[feature]["date_field"])
                else:
                    baseline_features.append(feature+","+features[feature]["description"]+",BASELINE")
            else:
                assert False

        if len(temporal_features):
            with open(param_dir+fname+"_fields.csv", "w") as fout:
                fout.write("\n".join(temporal_features))
        if len(baseline_features):
            with open(param_dir+fname+"_baseline_fields.csv", "w") as fout:
                fout.write("\n".join(baseline_features)) 