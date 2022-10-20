#!/usr/bin/env python
from bs4 import BeautifulSoup
import requests
import json
import os

from datetime import datetime
import pandas as pd
import numpy as np
import sys

def show_help():
    """show available options"""
    print("Usage: job_parser.py [option=new]")
    print("Options:")
    print("  help -- print this")
    print("  new -- review all new jobs")
    print("  all -- review all jobs")
    print("  tbd -- review not decided jobs")
    print("  yes -- review all jobs of interest")
    print("  no -- review all skipped jobs")

def retrieve_jobs(option):
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

    # override if option is all
    if option == "all":
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

    return alljob

def inspect_jobs(job):
    print("\n\n=== {} ===\n\n".format(job["name"]))
    print(job["detail"])
    answer=input("Are you interested in this job? [y/n/TBD] ")
    if answer in ['y','Y','yes','Yes','YES']:
        job["interested"] = "yes"
        comment = input("Comments: ")
        job["comment"] = comment
    elif answer in ['n','N','no','No','NO']:
        job["interested"] = "no"
    else:
        job["interested"] = "TBD"
    print()


def show_jobs(write=True):
    print("== Current Job List ==")
    for option in ['no','tbd','yes']:
        dfall = pd.read_json('jobs.json').T
        df = dfall.where(dfall['interested']==option).dropna()
        df_short = df.iloc[np.argsort([datetime.strptime(v,"%A, %B %d, %Y") for v in df.deadline])]
        for k,v in df_short.T.items():
            print("{} -- {} -- {} -- {}".format(v["interested"],v['name'],v["deadline"],v["comment"]))

    if write:
        df_short.index = np.arange(len(df_short))
        df_short.pop("detail")
        df_short.pop("interested")
        df_short.to_csv("interested_jobs.csv")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_help()
        sys.exit()
    else:
        option = sys.argv[1]

    if option == "help":
        show_help()
        show_jobs()
    else:
        alljob = retrieve_jobs(option)

        for job in alljob.values():
            if "interested" in job:
                skip = job["interested"].lower() != option.lower()
                skip = skip | (option == "new")
            else:
                skip = False
            if skip: continue
            inspect_jobs(job)
        # write
        with open('jobs.json',mode='w') as fp:
            json.dump(alljob,fp,indent=4)
