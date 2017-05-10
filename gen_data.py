import json
import random
import uuid

from datetime import datetime, timedelta


def generate_uuid_list(num=10):
    return ['%s' % uuid.uuid4() for i in range(num)]


# Generate users
USER_IDS = generate_uuid_list(50)


# Generate  some metadata: segments, recordings and activities
METADATA = {
    'segment': generate_uuid_list(20),
    'recording': generate_uuid_list(200),
    'activity': generate_uuid_list(100),
}


# Possible metric types
METRIC_TYPES = [
    'time',
    'jump_height',
    'jump_length',
]


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

    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, 365),
        milliseconds=random.randint(0, 1e8))
    timestamp = now - delta

    metric_type = random.choice(METRIC_TYPES)
    # The values dict elements are functions
    value = VALUES[metric_type]()

    metadata = []

    # Avoid adding two identical resource types
    choices = list(METADATA.keys())
    random.shuffle(choices)
    for i in range(0, random.randint(1, len(METADATA))):
        resource_type = choices.pop()
        resource_id = random.choice(METADATA[resource_type])
        metadata.append(
            {
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )

    data = {
        "metric_type": metric_type,
        "user_id": user_id,
        "timestamp": timestamp.isoformat(),
        "metadata": metadata,
        "value": value,
    }
    return data


if __name__ == '__main__':
    with open('test-data.json', 'w') as f:
        # Write 10000 records to the file
        for i in range(0, 100000):
            f.write('{"index":{"_id":%s}}\n' % i)
            f.write(json.dumps(gen_row()))
            f.write('\n')
