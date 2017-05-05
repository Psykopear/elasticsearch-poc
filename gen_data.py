import json
import random
import uuid

from datetime import datetime, timedelta


def generate_uuid_list(num=10):
    return ['%s' % uuid.uuid4() for i in range(num)]


# Generate users
USER_IDS = generate_uuid_list(50)

# Resource types
RESOURCE_TYPES = [
    'segment',
    'recording',
    'activity',
]

# Generate  some segments, recordings and activities
RESOURCE_IDS = {
    'segment': generate_uuid_list(20),
    'recording': generate_uuid_list(200),
    'activity': generate_uuid_list(100),
}

# Possible metric types
METRIC_TYPES = {
    'segment': ['time', 'jump_height', 'jump_length'],
    'recording': ['time', 'jump_height', 'jump_length'],
    'activity': ['time'],
}

# Random values
VALUES = {
    # Let's assume time in seconds
    'time': lambda: random.randint(1000, 9999999),
    # Jump height in cm
    'jump_height': lambda: random.randint(50, 500),
    # jump length in cm
    'jump_length': lambda: random.randint(50, 1000)
}



def gen_row():
    """
    Generate a meaningfull dict of values representing a record
    """
    user_id = random.choice(USER_IDS)
    timestamp = datetime.now() - timedelta(days=random.randint(0, 365),
                                           milliseconds=random.randint(0, 100000000))

    resource_type = random.choice(RESOURCE_TYPES)
    resource_id = random.choice(RESOURCE_IDS[resource_type])

    metric_type = random.choice(METRIC_TYPES[resource_type])
    # The values dict elements are functions
    value = VALUES[metric_type]()

    data = {
        "metric_type": metric_type,
        "user_id": user_id,
        "timestamp": timestamp.isoformat(),
        "resource_id": resource_id,
        "resource_type": resource_type,
        "value": value,
    }
    return data


if __name__ == '__main__':
    with open('test-data.json', 'w') as f:
        # Write 10000 records to the file
        for i in range(0, 10000):
            f.write('{"index":{"_id":%s}}\n' % i)
            f.write(json.dumps(gen_row()))
            f.write('\n')
