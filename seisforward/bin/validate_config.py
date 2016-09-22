import os
import argparse
from seisforward.io import load_config
from seisforward.validate_config import validate_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config_file = args.config_file
    if not os.path.exists(config_file):
        raise ValueError("Config file(%s) not exists!")

    config = load_config(config_file)
    validate_config(config)
    print("Config file('%s') is valid!" % (config_file))

if __name__ == "__main__":
    main()
