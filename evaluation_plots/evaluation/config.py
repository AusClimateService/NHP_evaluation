import os
import json



def load_config():
    with open('config.json', 'r') as fp:
        parameters = json.load(fp)

    # Resolve any environment variables in string values
    for k in parameters.keys():
        value = parameters[k]
        if type(value) == str:
            parameters[k] = os.path.expandvars(value)

    return parameters