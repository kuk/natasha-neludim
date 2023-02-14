
from os.path import exists


def find_dotenv():
    if exists('.env'):
        return '.env'


def load_dotenv(path='.env'):
    with open(path) as file:
        for line in file:
            line = line.rstrip()
            if line:
                key, value = line.split('=', 1)
                yield key, value
