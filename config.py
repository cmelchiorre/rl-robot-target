import yaml
import argparse

# fixed constants
MAX_GRAPH_NODES = 1000

parser = argparse.ArgumentParser()
parser.add_argument( '-c', '--config', type=str, default='config.cfg', help='configuration file')
args = parser.parse_args()

# takes all the config from .cfg file except input data
config = yaml.safe_load(open(args.config, 'r'))

def debug(message):
    if config["debug"]:
        print(message)