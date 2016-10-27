#!/usr/bin/env python3

import os
from glob import glob
import subprocess
import json
import datetime

def system(cmd):
    """
    Invoke a shell command.

    :returns: A tuple of output, err message, and return code
    """
    ret = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    out, err = ret.communicate()
    return out, err, ret.returncode

def clean_works(filename):
    "Let us clean the works directory after each job."
    names = os.listdir("./works/")
    for name in names:
        os.remove(os.path.join("./works/",name))
    os.remove(filename)
    os.remove(filename+".json")

def update_html(status, config, jobname):
    "Creates the HTML and RSS feed"
    jobstatus = "good"
    msg = "All is working well."
    if config["TotalFailedNonGatingTests"] > 0:
        jobstatus = "minor"
        msg = "Non gating tests failed: {0}".format(config["TotalFailedNonGatingTests"])
    if not status:
        jobstatus = "major"
        msg = "Latest Job failed."
    cmd = './manage.py {0} "{1}" {2}'.format(jobstatus, msg, jobname)
    print(cmd)
    system(cmd)
    system("./generate.py html > output/index.html")


def main():
    #  We will find all the jobs from jobsd directory and execute the jobs
    with open("primaryconfig.yml") as f:
        primaryconfig = f.read()
    job_configs = glob("./jobsd/*.yml")
    for job_config in job_configs:
        now = datetime.datetime.now()
        jobdir_name = now.strftime("%Y-%m-%d-%H-%M-%S")
        status = False
        text = ""
        result_json = {}
        job_base_name = os.path.basename(job_config)
        job_name = job_base_name.split(".")[0]
        with open(job_config) as fobj:
            data = fobj.read()
        workingconfig = primaryconfig + '\n' + data
        # Now copy the configs into works dirctory
        with open(os.path.join("./works/", job_base_name), "w") as fobj:
            fobj.write(workingconfig)
        system("cp ./jobsd/{0}.txt ./works/".format(job_name))
        # Now do the real work
        out, err, rcode = system("gotun --job {0} --config-dir ./works/".format(job_name))
        if rcode == 0:
            status = True

        for line in out.decode('utf-8').split('\n'):
            if line.find("Result file at:") != -1:
                # First get the result filename
                filename = line.split(': ')[1]
                # Now grab the result text
                with open(filename) as fobj:
                    text = fobj.read()
                with open(filename + ".json") as fobj:
                    result_json = json.load(fobj)
        if not text:
            text = out.decode('utf-8')+ err.decode('utf-8')
        with open(os.path.join("./output/",job_name, jobdir_name), "w") as fobj:
            fobj.write(text)

        # Now generate the HTML files using status project.
        update_html(status, result_json, job_name)
        clean_works(filename)


if __name__ == '__main__':
    main()