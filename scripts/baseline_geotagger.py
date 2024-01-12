# baseline_geotagger.py
# R.A. Kinds
# 1/11/2023
# Take images as input and geotag them with a baseline system


from PIL import Image
import pytesseract
import spacy
import pandas as pd
import os
import re


# Use OCR to extract text on poster, return list
def detect_text(file):
    # Detect text
    config_file = r'-l nld'
    detected_text = [pytesseract.image_to_string(Image.open(file), config=config_file), {}]

    # Return text in dict
    return detected_text


# Perform NER, return list
def ner_tagging(detected_text):
    counter = 0
    nlp = spacy.load("nl_core_news_lg")
    doc = nlp(detected_text[0])
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            counter += 1
            detected_text[1][str(counter)] = [ent.text, '']

    return detected_text


# Find the geonames ids for a given list of place names, return list
def find_geonames_id(gazetteer, detected_entities):
    for ent in detected_entities[1]:
        print(re.sub('[^\w-]', '', detected_entities[1][ent][0]))
        candidates = gazetteer.query("name =='" + re.sub('[^\w-]', '', detected_entities[1][ent][0]) + "'")
        if len(candidates) > 0:
            result = candidates.iloc[0]["geonameid"]
            detected_entities[1][ent][1] = str(result)
        else:
            detected_entities[1][ent][1] = None
    return detected_entities


def main():
    # Create an empty file for results
    results_file = ""

    # Open the gazetteer
    gazetteer = pd.read_csv('../data/gazetteer/gazetteer.csv', engine='python', sep='\t')
    x = 0
    # Geotag the data and save to file
    for file in os.listdir('../data/testimages/'):
        x += 1
        print(x)
        # geotagging
        file_path = '../data/testimages/' + file
        detected_text = detect_text(file_path)
        detected_entities = ner_tagging(detected_text)
        geo_entities = find_geonames_id(gazetteer, detected_entities)
        # write results to file
        for ent in geo_entities[1]:
            if geo_entities[1][ent][1]:
                print(file + '\t' + geo_entities[1][ent][0] + '\t' + geo_entities[1][ent][1] + '\n')
                results_file += file + '\t' + geo_entities[1][ent][1] + '\n'

    # save full results file
    new_file = open("../data/baseline_results.txt", "w")
    new_file.write(results_file)
    new_file.close()


main()
