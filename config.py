import glob
import os
import yaml

def load():
    with open('./config.yaml', 'r') as fd:
        return yaml.safe_load(fd)