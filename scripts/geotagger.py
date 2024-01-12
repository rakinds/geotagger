# geotagger.py
# R.A. Kinds
# 1/11/2023
# Take images as input and geotag them
import cv2
import pytesseract
import spacy
import cv2 as cv
import pandas as pd
import os
import re
import numpy as np


# Preprocess image, returns Image object
def preprocess(file):
    img = cv.imread(file)
    kernel = np.ones((5, 5), np.uint8)
    opening = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)

    return opening


# Use OCR to extract text on poster, returns dict
def detect_text(file, neg_img):
    # Detect text
    config_file = r'-l nld'
    detected_text = {'v1': [pytesseract.image_to_string(cv.imread(file, cv2.IMREAD_GRAYSCALE), config=config_file), []],
                     'v2': [pytesseract.image_to_string(neg_img, config=config_file), []]}

    # Return text in dict
    return detected_text


# Perform NER, return dict
def ner_tagging(detected_text, nlp):
    for version in detected_text:
        # Extract GPE ents for three versions
        regular_geo_ents = []
        title_geo_ents = []
        lower_geo_ents = []

        doc_regular = nlp(detected_text[version][0])
        doc_title = nlp(detected_text[version][0].title())
        doc_lower = nlp(detected_text[version][0].lower())

        for ent in doc_regular.ents:
            if ent.label_ == 'GPE':
                regular_geo_ents.append([ent.text, ent.start, ent.end])
        for ent in doc_title.ents:
            if ent.label_ == 'GPE':
                title_geo_ents.append([ent.text, ent.start, ent.end])
        for ent in doc_lower.ents:
            if ent.label_ == 'GPE':
                lower_geo_ents.append([ent.text, ent.start, ent.end])

        # Combine all versions
        if regular_geo_ents == title_geo_ents == lower_geo_ents:
            version_ents = []
            for item in regular_geo_ents:
                version_ents.append(item[0])
            detected_text[version][1].append(version_ents)
        else:
            version_ents = []
            for item in regular_geo_ents:
                for option in title_geo_ents:
                    if item[0].title() in option:
                        title_geo_ents.remove(option)
                for option in lower_geo_ents:
                    if item[0].lower() in option:
                        lower_geo_ents.remove(option)
                version_ents.append(item[0])
            for item in title_geo_ents:
                version_ents.append(item[0])
            for item in lower_geo_ents:
                version_ents.append(item[0])

        # Add to the detected text dict
        detected_text[version][1] = version_ents

    return detected_text


# Compare results from 2 image options, return list
def compare_entities(detected_text):
    if detected_text['v1'][1] == detected_text['v2'][1]:
        return detected_text['v1'][1]
    else:
        combined_ents = []
        for ent in detected_text['v1'][1]:
            if ent in detected_text['v2'][1]:
                detected_text['v2'][1].remove(ent)
                combined_ents.append(ent)
            else:
                combined_ents.append(ent)
        for ent in detected_text['v2'][1]:
            combined_ents.append(ent)
        return combined_ents


def find_geonames_id(gazetteer, entity, num_of_ents):
    entity = re.sub("[^\w\-']", ' ', entity)
    candidates = gazetteer.query('''name == @entity.title() ''')
    # if there are no 'name' candidates, search the 'alternate names' column
    if len(candidates) == 0:
        if len(entity) > 2:
            alternate_candidates = gazetteer[True == gazetteer['alternatenames'].str.contains(',' + entity.title() + ',')]
            # if there is only one candidate, return it
            if len(alternate_candidates) == 1:
                return alternate_candidates.iloc[0]["geonameid"]

            elif len(alternate_candidates) > 1:
                # if there is a country option, return it
                if len(alternate_candidates.query(
                        "`feature code` == 'PCL' or `feature code` == 'PCLD' or `feature code` == 'PCLF' "
                        "or `feature code` == 'PCLH' or `feature code` == 'PCLI' or `feature code` == 'PCLIX' "
                        "or `feature code` == 'PCLS'")) == 1:
                    return \
                        alternate_candidates.query(
                            "`feature code` == 'PCL' or `feature code` == 'PCLD' or `feature code` == 'PCLF' "
                            "or `feature code` == 'PCLH' or `feature code` == 'PCLI' "
                            "or `feature code` == 'PCLIX' or `feature code` == 'PCLS'").iloc[0]["geonameid"]

                # If one option is city and the other is municipality, return the city
                elif len(alternate_candidates) == 2 and alternate_candidates.iloc[0]["feature code"] == 'ADM2' and \
                        alternate_candidates.iloc[1]["feature code"] == 'PPL':
                    return alternate_candidates.iloc[1]["geonameid"]
                elif len(alternate_candidates) == 2 and alternate_candidates.iloc[0]["feature code"] == 'PPL' and \
                        alternate_candidates.iloc[1]["feature code"] == 'ADM2':
                    return alternate_candidates.iloc[0]["geonameid"]

                # if there is an option with population > 50,000, return it
                elif len(alternate_candidates.query('`population` > 50000') == 1):
                    return alternate_candidates.query('`population` > 50000').iloc[0]["geonameid"]

                # If no other option is found, find the largest population option in NL.
                    # If no other option is found, find the largest population option in NL.
                else:
                    print('largest!')
                    alternate_candidates_nl = alternate_candidates.query("`country code` == 'NL' and `feature code` == 'PPL'")
                    sorts = alternate_candidates_nl.sort_values(by='population')
                    if len(sorts) > 0:
                        return sorts.iloc[-1]["geonameid"]

    # if there is only one 'name' candidate, return it
    elif len(candidates) == 1:
        return candidates.iloc[0]["geonameid"]

    # if there are several 'name' candidates, continue
    elif len(candidates) > 1:
        # if there is a country option, return it
        if len(candidates.query("`feature code` == 'PCL' or `feature code` == 'PCLD' or `feature code` == 'PCLF' "
                                "or `feature code` == 'PCLH' or `feature code` == 'PCLI' or `feature code` == 'PCLIX' "
                                "or `feature code` == 'PCLS'")) == 1:
            return candidates.query("`feature code` == 'PCL' or `feature code` == 'PCLD' or `feature code` == 'PCLF' "
                                    "or `feature code` == 'PCLH' or `feature code` == 'PCLI' "
                                    "or `feature code` == 'PCLIX' or `feature code` == 'PCLS'").iloc[0]["geonameid"]

        # if one option is city and the other is municipality, return the city
        elif len(candidates) == 2 and candidates.iloc[0]["feature code"] == 'ADM2' and candidates.iloc[1][
            "feature code"] == 'PPL':
            return candidates.iloc[1]["geonameid"]
        elif len(candidates) == 2 and candidates.iloc[0]["feature code"] == 'PPL' and candidates.iloc[1][
            "feature code"] == 'ADM2':
            return candidates.iloc[0]["geonameid"]

        # if there is an option with population > 50,000, return it
        elif len(candidates.query('`population` > 50000') == 1):
            return candidates.query('`population` > 50000').iloc[0]["geonameid"]

        # If no other option is found, find the largest population option in NL.
        else:
            candidates = candidates.query("`country code` == 'NL' and `feature code` == 'PPL'")
            sorts = candidates.sort_values(by='population')
            if len(sorts) > 0:
                return sorts.iloc[-1]["geonameid"]


def main():
    # Create an empty file for results
    results_file = ""

    # Open the gazetteer
    gazetteer = pd.read_csv('../data/gazetteer/gazetteer.csv', engine='python', sep='\t')
    x = 0
    nlp = spacy.load("nl_core_news_lg")

    # Geotag the data
    for file in os.listdir('../data/dataset/'):
        x += 1
        file_path = '../data/dataset/' + file
        preprocessed_img = preprocess(file_path)
        detected_text = detect_text(file_path, preprocessed_img)
        geo_entities = ner_tagging(detected_text, nlp)
        best_entities = compare_entities(geo_entities)
        for ent in best_entities:
            if len(ent) > 1 and ent.lower() != 'tel' and ent.lower() != 'tel.':
                geo_id = str(find_geonames_id(gazetteer, ent.title(), len(best_entities)))
            else:
                geo_id = 'None'
            if geo_id != 'None':
                print(file + '\t' + ent + '\t' + geo_id)
                results_file += file + '\t' + geo_id + '\n'
        print(x)

    # save full results file
    new_file = open("../data/system_results.txt", "w")
    new_file.write(results_file)
    new_file.close()


main()
