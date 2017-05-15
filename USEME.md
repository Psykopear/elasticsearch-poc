# Elasticsearch as a metrics aggregation

With LiveX we will have to collect metadata about users'
activites in our system, and to use those data to give users
some insights about their performances both from a personal
and a "global" perspective.

We need a system to rapidly retrieve both single records and
aggregations made on the whole dataset, with the possibility
to redefine them after the system is running.

"Elasticsearch is a distrbuited, RESTful search and
analytics engine capable of solving a growing number
of use cases"

Es is a great tool when it comes to filtering and aggregations
of data, but it shouldn't be used as a data storage systems due
to some known problems.
