

def load_dotenv(path):
    with open(path) as file:
        for line in file:
            line = line.rstrip()
            if line:
                key, value = line.split('=', 1)
                yield key, value
