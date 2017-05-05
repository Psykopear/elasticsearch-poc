# Elasticsearch proof of concept

Toy project to test ES functionalities

## Usage

Clone the repo:

    $ git clone git@github.com:Psykopear/elasticsearch-poc.git

cd into the repo dir:

    $ cd elasticsearch-poc

Run elasticsearch with docker-compose:

    $ docker-compose up -d

Check ES is up and reachable:

    $ curl -XGET 'localhost:9200/_cat/health?v&pretty'

Create ES index:

    $ curl -XPUT 'localhost:9200/metrics?pretty'

Check the index:

    $ curl -XGET 'localhost:9200/_cat/indices?v&pretty'


Optional: generate test data (a sample is available in the repo, and will be overwritten)

    $ python gen_data.py

This will write 10000 records into a file named test-data.json, edit the script to change the data generated

Send test data to ES:

    $ curl -H "Content-Type: application/json" -XPOST "localhost:9200/metrics/basic_metric/_bulk?pretty&refresh" --data-binary "@test-data.json"



### Querying ES

Retrieve all records (paginated by 10 by default):

    $ curl -XGET 'localhost:9200/metrics/_search?q=*&sort=timestamp:asc&pretty'


Get only `user_id`, `value` and `resource_id`:

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
        {
          "query": { "match_all": {} },
          "_source": ["user_id", "value", "resource_id"]
        }
        '

Get all records with a time metric value between 2000 and 30000, returning only
`user_id`, `value` and `resource_id`:

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "query": {
          "bool": {
            "must": {
              "match": {"metric_type": "time"}
            },
            "filter": {
              "range": {
                "value": {
                  "gte": 2000,
                  "lte": 30000
                }
              }
            }
          }
        },
        "_source": ["user_id", "value", "resource_id"]
      }
      '


Number of records per user (sorted by count by default):

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "size": 0,
        "query": { "match": {"metric_type": "time"} },
        "aggs": {
          "group_by_user": {
            "terms": {
              "field": "user_id.keyword"
            }
          }
        }
      }
      '

Average time by segment:

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "size": 0,
        "query": {
          "bool": {
            "must": [
              { "match": { "metric_type": "time" } },
              { "match": { "resource_type": "segment" } }
            ]
          }
        },
        "aggs": {
          "group_by_segment": {
            "terms": {
              "field": "resource_id.keyword"
            },
            "aggs": {
              "average_time": {
                "avg": {
                  "field": "value"
                }
              }
            }
          }
        }
      }
      '

Overall best time for a given segment:

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "size": 1,
        "_source": ["user_id", "value"],
        "sort": {"value": "desc"},
        "query": {
          "bool": {
            "must": [
              { "match": { "metric_type": "time" } },
              { "match": { "resource_type": "segment" } },
              { "match": { "resource_id": "122705c5-ee08-4109-b130-8d53501363b8" } }
            ]
          }
        }
      }
      '


Best time in a segment for a given user:

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "size": 1,
        "_source": ["user_id", "value"],
        "sort": {"value": "desc"},
        "query": {
          "bool": {
            "must": [
              { "match": { "metric_type": "time" } },
              { "match": { "resource_type": "segment" } },
              { "match": { "resource_id": "122705c5-ee08-4109-b130-8d53501363b8" } },
              { "match": { "user_id": "f039f293-9211-48a6-baf3-8c835ae95d68" } }
            ]
          }
        }
      }
      '
