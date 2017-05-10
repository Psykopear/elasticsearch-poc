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

Create the metrics mapping:
(investigate the possible use of `eager_global_ordinals` setting for keywords)

    $ curl -XPUT 'localhost:9200/metrics' -H 'Content-Type: application/json' -d'
      {
        "mappings": {
          "basic_metric": {
            "properties": {
              "metric_type": {
                "type": "keyword"
              },
              "user_id": {
                "type": "keyword"
              },
              "timestamp": {
                "type": "date"
              },
              "metadata": {
                "type": "nested",
                "properties": {
                  "resource_type": {
                    "type": "keyword"
                  },
                  "resource_id": {
                    "type": "keyword"
                  }
                }
              },
              "value": {
                "type": "scaled_float",
                "scaling_factor": 1000
              }
            }
          }
        }
      }
      '


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

Get only `user_id`, `value` and `metadata`:

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "query": { "match_all": {} },
        "_source": ["user_id", "value", "metadata"]
      }
      '

Get all records with a time metric value between 2000 and 30000, returning only
`user_id`, `value` and `metadata`:

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
        "_source": ["user_id", "value", "metadata"]
      }
      '

Number of records per user (sorted by count by default):

    $ curl -XGET 'localhost:9200/metrics/_search?pretty' -H 'Content-Type: application/json' -d'
      {
        "size": 0,
        "aggs": {
          "group_by_user": {
            "terms": {
              "field": "user_id",
              "include": ["2ad6c6ed-d475-498c-94e7-9daa7cba13a4"]
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
            "filter": [
              {
                "term": {"metric_type": "time"}
              },
              {
                "nested": {
                  "path": "metadata",
                  "query": {
                    "term": {
                      "metadata.resource_type": "segment"
                    }
                  }
                }
              }
            ]
          }
        },
        "aggs" : {
          "by_segment_id": {
            "nested": {
              "path": "metadata"
            },
            "aggs": {
              "segments": {
                "terms": {
                  "field": "metadata.resource_id"
                },
                "aggs": {
                  "average": {
                    "reverse_nested": {},
                    "aggs": {
                      "avg_time": {
                        "avg": {
                          "field": "value"
                        }
                      }
                    }
                  }
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
            "filter": [
              {
                "term": {"metric_type": "time"}
              },
              {
                "nested": {
                  "path": "metadata",
                  "query": {
                    "bool": {
                      "filter": [
                        {
                          "term": {"metadata.resource_type": "segment"}
                        },
                        {
                          "term": {"metadata.resource_id": "63a4a9a1-0775-4772-95db-8580801ded8f"}
                        }
                      ]
                    }
                  }
                }
              }
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
            "filter": [
              { "term": { "metric_type": "time" } },
              { "term": { "user_id": "ac6cfc73-4044-4cf1-9ad4-5544090a6803" } },
              {
                "nested": {
                  "path": "metadata",
                  "query": {
                    "bool": {
                      "filter": [
                        {
                          "term": {"metadata.resource_type": "segment"}
                        },
                        {
                          "term": {"metadata.resource_id": "63a4a9a1-0775-4772-95db-8580801ded8f"}
                        }
                      ]
                    }
                  }
                }
              }
            ]
          }
        }
      }
      '
