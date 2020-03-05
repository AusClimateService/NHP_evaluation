import os
import json



def load_config():
    with open('config.json', 'r') as fp:
        parameters = json.load(fp)

    return parameters