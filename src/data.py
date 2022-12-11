import json
import logging
import time

logging.basicConfig(filename='data/usage.log',
                    encoding='utf-8', level=logging.DEBUG)

LOG_IDENTIFIER = 'data: '

def write_cache(name, data):
    start_t = time.time()
    logging.info(LOG_IDENTIFIER + f"Writing cache with name: {name}")
    with open(name, 'w') as f:
        f.write(json.dumps(data))
    
    logging.info(LOG_IDENTIFIER +
                f"Cache written with name: {name} in {(time.time() - start_t) / 1000}s")
    

def read_cache(name):
    start_t = time.time()
    logging.info(LOG_IDENTIFIER + f"Reading cache with name: {name}")

    try:
        with open(name, 'r') as f:
            data = f.read()
        json_data = json.loads(data)
        logging.info(LOG_IDENTIFIER +
                     f"Cache read with name: {name} in {(time.time() - start_t) / 1000}s")
    except:
        logging.warning(LOG_IDENTIFIER + "Error with json.loads.")
    return json_data