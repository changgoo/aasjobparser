#!/usr/bin/env python
from bs4 import BeautifulSoup
import requests
import json
import os

from datetime import datetime
import pandas as pd
import numpy as np

URL = "https://jobregister.aas.org"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

facjobs=soup.find_all('table')[1]
jobs=facjobs.find_all('tr')[1:]

if os.path.exists("jobs.json"):
    with open("jobs.json",mode="r") as fp:
        alljob = json.load(fp)
else:
    alljob = dict()

for j in jobs:
    inst = j.find_all('td')[1].text
    joburl = '{}{}'.format(URL,j.a.attrs['href'])
    if joburl in alljob: continue
    jobpage = requests.get(joburl)
    jobsoup = BeautifulSoup(jobpage.content, "html.parser")
    deadline=jobsoup.find('div',class_="field-name-field-application-deadline").find("span").text
    detail=jobsoup.find("fieldset",class_='group-announcement').find("div",class_="field-item").text
    jobdict=dict(name=inst,url=joburl,deadline=deadline,detail=detail)
    alljob[joburl] = jobdict

for job in alljob.values():
    if "interested" in job: continue
    #if job['interested'] == 'n': continue
    print("\n\n=== {} ===\n\n".format(job["name"]))
    print(job["detail"])
    answer=input("Are you interested in this job?[y/n]")
    if answer in ['y','Y','yes','Yes','YES']:
        job["interested"] = "y"
        comment = input("Comments: ")
        job["comment"] = comment
    elif answer in ['n','N','no','No','NO']:
        job["interested"] = "n"
    print()

with open('jobs.json',mode='w') as fp:
    json.dump(alljob,fp,indent=4)

print("== Current Interested Job List ==")
df = pd.read_json('jobs.json').T
df = df.where(df['interested']=='y').dropna()
df_short = df.iloc[np.argsort([datetime.strptime(v,"%A, %B %d, %Y") for v in df.deadline])]
for k,v in df_short.T.items():
    print("{} -- {} -- {}".format(v['name'],v["deadline"],v["comment"]))

df_short.index = np.arange(len(df_short))
df_short.pop("detail")
df_short.pop("interested")
df_short.to_csv("interested_jobs.csv")
