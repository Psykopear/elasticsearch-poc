from datetime import datetime

from elasticsearch_dsl import (
    DocType, Keyword, Date, Float, Nested, InnerObjectWrapper
)
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.connections import connections


# Connect to a local ES instance
connections.create_connection(hosts=['localhost'], timeout=20)


class BasicMetric(DocType):
    """
    Besic metric mapping
    """
    metric_type = Keyword()
    user_id = Keyword()
    timestamp = Date()
    value = Float()
    metadata = Nested(
        properties={
            'type': Keyword(),
            'unique_id': Keyword(),
        }
    )

    class Meta:
        index = 'metrics'


# Initialize metric


metric = BasicMetric(metric_type='time', user_id='prova id', timestamp=datetime.now(), value=1.245)

metric.metadata.append({'type': 'provatype', 'unique_id': 'very unique id'})

# Add the metric to the index
metric.save()

# And now search
s = Search()
s = s.source(['user_id', 'value', 'metadata'])
s.to_dict()
response = s.execute()
print(response.success())
print(response.hits.total)


# Get all records with a time metric value between 2000 and 30000, returning only
s = Search().filter('range', value={"gte": 2000, "lte": 30000})


# Number of records per user
# Define aggregation
agg = A('terms', field='user_id', include='user_id')
# init search
s = Search()
# Size 0
s = s[0:0]
# Add aggregation
s.aggs.bucket('group_by_user', agg)
# Dict representation
s.to_dict()



######################
# Average time by segment
s = Search()

# Set size to 0, we only want aggregations
s = s[0:0]

# Queries
s = s.filter('term', metric_type='time')
q = Q('term', metadata__resource_type='segment')
s = s.filter('nested', path='metadata', query=q)

# Aggregations (read it down-top)
a = A('avg', field='value')
a = A('reverse_nested', aggs={'avg_time': a})
a = A('terms', field='metadata.resource_id', aggs={'average': a})
a = A('nested', path='metadata', aggs={'segments': a})
s.aggs.bucket('by_segment_id', a)

s.to_dict()

resp = s.execute()
print(resp.aggregations.by_segment_id.segments.buckets[0])


###########################3
# Best time for a given segment

s = Search()

# We only want the first result
s = s[0:1]

s = s.source(['user_id', 'value'])

# Sorting
s = s.sort('-value')

# Filter it
s = s.filter('term', metric_type='time')
q = Q('term', metadata__resource_type='segment')
q &= Q('term', metadata__resource_id='segment-id')
s = s.filter('nested', path='metadata', query=q)

s.to_dict()


###########################
# Best time in a given segment for a given user

q1 = {'term': {"metadata__resource_type": 'segment'}}
q2 = {'term': {"metadata__resource_id": 'segment-id'}}
q = Q('bool', filter=[q1,q2])

s = Search()[0:1]\
        .source(['user_id', 'value'])\
        .sort('-value')\
        .filter('term', metric_type='time')\
        .filter('term', user_id='user-id')\
        .filter('nested', path='metadata', query=q)

s.to_dict()

