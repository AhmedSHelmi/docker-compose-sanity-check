#!/usr/bin/env python
from __future__ import print_function
import argparse
from datetime import timedelta
from datetime import datetime
import sys

from dateutil.parser import parse as parse_date
import docker
import pytz
parser = argparse.ArgumentParser()
parser.add_argument("compose_project",
                    help="The name of the docker-compose project")
parser.add_argument("compose_service",
                    help="The name of the docker-compose service")
args = vars(parser.parse_args())

client = docker.from_env()
service_containers = client.containers.list(filters={
    "label": [
        "com.docker.compose.oneoff=False",
        "com.docker.compose.project={}".format(args["compose_project"]),
        "com.docker.compose.service={}".format(args["compose_service"])
    ]})

if len(service_containers) == 0:
    print("CRITICAL: project({})/service({}) doesn't exist!".format(
        args["compose_project"], args["compose_service"]))
    sys.exit(2)
elif len(service_containers) > 1:
    print("CRITICAL: project({})/service({}) has more than 1 "
          "container!".format(
              args["compose_project"], args["compose_service"]))
    sys.exit(2)

service_container = service_containers[0]
created_at = parse_date(service_container.attrs['Created'])
status = service_container.attrs['State']['Status']
started_at = parse_date(service_container.attrs['State']['StartedAt'])
now = datetime.utcnow().replace(tzinfo=pytz.utc)
uptime = now - started_at

if status in ['stopped', 'exited', 'dead']:
    print("CRITICAL: project({})/service({}) is status={}".format(
        args["compose_project"], args["compose_service"], status))
    sys.exit(2)

if (started_at - created_at) > timedelta(minutes=5):
    if uptime < timedelta(seconds=5):
        print("CRITICAL: project({})/service({}) appears to be "
              "crash-looping".format(
                  args["compose_project"], args["compose_service"]))
        sys.exit(2)

if status == "restarting":
    print("WARNING: project({})/service({}) is restarting".format(
        args["compose_project"], args["compose_service"]))
    sys.exit(1)

print ("OK: project({})/service({}) is up for {}".format(
    args["compose_project"], args["compose_service"], uptime
))
sys.exit(0)
