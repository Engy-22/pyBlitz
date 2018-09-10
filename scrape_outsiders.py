#!/usr/bin/env python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import html5lib
import pdb
from collections import OrderedDict
import json
import csv
import contextlib
import os
import re
from pathlib import Path

import settings

def CleanString(data):
    data = re.sub(' +',' ', data)
    return re.sub("'",'', data)

# Please note, I have written this scraper in case you want to learn/use it
# Be aware that the statistics in this scraper are not currently used in any of my calculations
# ( that doesn't mean that you can't )

url = "http://www.footballoutsiders.com/stats/ncaa"

print ("Scrape Outsiders Tool")
print ("**************************")
print ("data is from {0}".format(url))
print ("Directory Location: {0}".format(settings.data_path))
print ("**************************")

with contextlib.closing(urlopen(url)) as page:
    soup = BeautifulSoup(page, "html5lib")
ratings_table=soup.find('table', {"class":"stats"})

IDX=[]
A=[]
B=[]
index=0
for row in ratings_table.findAll("tr"):
    col=row.findAll('td')
    if len(col)>0 and col[0].find(text=True)!="Team":
        index+=1
        IDX.append(index)
        A.append(CleanString(col[0].find(text=True)))
        B.append(col[4].find(text=True))

df=pd.DataFrame(IDX,columns=['Index'])
df['Team']=A
df['S&P+M']=B

Path(settings.data_path).mkdir(parents=True, exist_ok=True) 
with open(settings.data_path + 'outsiders.json', 'w') as f:
    f.write(df.to_json(orient='index'))

with open(settings.data_path + "outsiders.json") as stats_json:
    dict_stats = json.load(stats_json, object_pairs_hook=OrderedDict)
stats_sheet = open(settings.data_path + 'outsiders.csv', 'w', newline='')
csvwriter = csv.writer(stats_sheet)
count = 0
for row in dict_stats.values():
    if (count == 0):
        header = row.keys()
        csvwriter.writerow(header)
        count += 1
    csvwriter.writerow(row.values())
stats_sheet.close()
print ("done.")
