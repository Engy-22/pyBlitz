#!/usr/bin/env python3

import json
import pdb
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import csv
from collections import OrderedDict
import os.path
from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import sys

def CalcPercent(total, skip, correct):
    try:
        return  round(correct / (total - skip) * 100., 2)
    except ZeroDivisionError:
        return None

def GetPercent(item):
    newstr = item.replace("%", "")
    newstr = newstr.replace("?", "")
    if (newstr.strip()==""):
        return -1
    return float(newstr)

def GetIndex(item):
    idx = re.findall(r'\d+', str(item))
    if (len(idx) == 0):
        idx.append("-1")
    return int(idx[0])

def GetFiles(path, templatename):
    file_dict = {}
    for p in Path(path).glob(templatename):
        idx = GetIndex(p)
        file_dict[idx] = str(p)
    file_list = []
    for idx in range(len(file_dict)):
        file_list.append(file_dict[idx + 1])
    return file_list

def CurrentScheduleFiles(filename):
    stat = os.path.getmtime(filename)
    stat_date = datetime.fromtimestamp(stat)
    if stat_date.date() < datetime.now().date():
        return False
    return True

def RefreshScheduleFiles():
    import scrape_schedule

def GetActualScores(abbra, abbrb, scores):
    items = re.split(r'(,|\s)\s*', str(scores).lower())
    if (items[0].strip() == "?"):   # Cancelled, Postponed or not yet Played Game
        return -1, -1
    if (len(items) != 7):
        return -1, -1
    if (abbra.lower().strip() not in items):
        if (verbose):
            print ("Missing Abbreviation [{0}] [{1}] in Score {2}".format(abbra, abbrb, scores))
        return -1, -1
    if (abbrb.lower().strip() not in items):
        if (verbose):
            print ("Missing Abbreviation [{0}] [{1}] in Score {2}".format(abbra, abbrb, scores))
        return -1, -1
    if (abbra.lower().strip() == items[0].lower().strip()):
        scorea = int(items[2])
        scoreb = int(items[6])
    else:
        scorea = int(items[6])
        scoreb = int(items[2])
    return scorea, scoreb

verbose = False
if (len(sys.argv)==1):
    verbose = False
elif (len(sys.argv)==2):
    verbose = True
else:
    print ("???")
    print ("error, usage: no arg be quiet, 1 arg be verbose")
    print ("./measure_results.py")
    print ("./measure_results.py --verbose")
    print ("???")
    sys.exit("error: incorrect number of arguments")

    print ("Measure Actual Results Tool")
    print ("**************************")

if (not CurrentScheduleFiles('data/sched1.json')):
    RefreshScheduleFiles()

file = 'data/sched1.json'
if (not os.path.exists(file)):
    if (verbose):
        print ("schedule files are missing, run the scrape_schedule tool to create")
    exit()

file = 'week1.csv'
if (not os.path.exists(file)):
    if (verbose):
        print ("Weekly files are missing, run the score_week tool to create")
    exit()

sched_files = GetFiles("data/", "sched*.json")
list_sched = []
for file in sched_files:
    with open(file) as sched_file:
        list_sched.append(json.load(sched_file, object_pairs_hook=OrderedDict))

week_files = GetFiles(".", "week*.csv")
list_week = []
for file in week_files:
    with open(file) as week_file:
        reader = csv.DictReader(week_file)
        for row in reader:
            list_week.append(row)

IDX=[]
A=[]
B=[]
C=[]
D=[]
E=[]
index = 0
alltotal = 0
allskip = 0
allcorrect = 0
count = 0
for idx in range(len(list_sched)):
    total = 0
    skip = 0
    correct = 0
    for item in list_sched[idx].values():
        total += 1
        chancea = GetPercent(list_week[index]["ChanceA"])
        abbra = list_week[index]["AbbrA"]
        abbrb = list_week[index]["AbbrB"]
        index += 1
        scorea, scoreb = GetActualScores(abbra, abbrb, item["Score"])
        if (chancea < 0 or scorea < 0 or scoreb < 0 or abbra.strip() == "" or abbrb.strip() == ""):
            skip += 1
        else:
            if (chancea >= 50 and (scorea >= scoreb)):
                correct += 1
            if (chancea < 50 and (scorea < scoreb)):
                correct += 1
    count += 1
    IDX.append(count)
    A.append(idx + 1)
    B.append(total)
    C.append(skip)
    D.append(correct)
    E.append(CalcPercent(total, skip, correct))
    if (verbose):
        print ("week{0} total={1}, skip={2}, correct={3} Percent={4}%".format(idx + 1, total, skip,
            correct, CalcPercent(total, skip, correct)))
    alltotal = alltotal + total
    allskip = allskip + skip
    allcorrect = allcorrect + correct
count += 1
IDX.append(count)
A.append(99)
B.append(alltotal)
C.append(allskip)
D.append(allcorrect)
E.append(CalcPercent(alltotal, allskip, allcorrect))

if (verbose):
    print ("====================================================================")
    print ("Totals total={0}, skip={1}, correct={2} Percent={3}%".format(alltotal, allskip,
        allcorrect, CalcPercent(alltotal, allskip, allcorrect)))
    print ("====================================================================")

df=pd.DataFrame(IDX,columns=['Index'])
df['Week']=A
df['Total Games']=B
df['Count Unpredicted']=C
df['Count Correct']=D
df['Percent Correct']=E

path = "data/"
now = datetime.now()
file = "{0}{1}_{2}.json".format(path, 'results', now.year)
with open(file, 'w') as f:
    f.write(df.to_json(orient='index'))

with open(file) as results_json:
    dict_results = json.load(results_json, object_pairs_hook=OrderedDict)

file = "{0}{1}_{2}.csv".format(path, 'results', now.year)
results_sheet = open(file, 'w', newline='')
csvwriter = csv.writer(results_sheet)
count = 0
for row in dict_results.values():
    if (count == 0):
        header = row.keys()
        csvwriter.writerow(header)
        count += 1
    csvwriter.writerow(row.values())
results_sheet.close()
print ("done.")