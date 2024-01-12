# evaluation.py
# R.A. Kinds
# 1/11/2023
# A script to evaluate annotations and system results

# Precision = true positives / (true positives + false positives), return float
def precision(true_positives, false_positives):
    p = true_positives / (true_positives + false_positives)
    return p


# Recall = true positives / (true positives + false negatives), return float
def recall(true_positives, false_negatives):
    r = true_positives / (true_positives + false_negatives)
    return r


# F-score = 2 * (precision * recall / precision + recall), return float
def f_score(p, r):
    f = 2 * ((p * r) / (p + r))
    return f


# Take a file given as a list and return it as a dictionary
def create_dict(list_file):
    new_dict = {}
    for ann in list_file:
        ann = ann.split('\t')
        print(ann[0], ann[1])
        if ann[0] in new_dict:
            new_dict[ann[0]].append(ann[1].rstrip())
        else:
            new_dict[ann[0]] = [ann[1].rstrip()]
    return new_dict


def main():
    with open('../data/annotatie/final_annotations.txt', 'r') as file:
        annotations = file.readlines()
    with open('../data/system_results.txt', 'r') as file:
        system_results = file.readlines()

    annotations_dict = create_dict(annotations)
    results_dict = create_dict(system_results)

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for poster in annotations_dict:
        if poster in results_dict:
            corresponding_result = results_dict[poster]
            for label in corresponding_result:
                if label in annotations_dict[poster]:
                    print('tp', poster, label)
                    true_positives += 1
                    annotations_dict[poster].remove(label)
                elif label not in annotations_dict[poster]:
                    print('fp', poster, label)
                    false_positives += 1
            if len(annotations_dict[poster]) > 0:
                false_negatives += len(annotations_dict[poster])
        else:
            false_negatives += len(annotations_dict[poster])

    print('tp: ', true_positives)
    print('fp: ', false_positives)
    print('fn: ', false_negatives)

    p = precision(true_positives, false_positives)
    r = recall(true_positives, false_negatives)
    f = f_score(p, r)

    print('precision:', p)
    print('recall:', r)
    print('fscore:', f)


main()
