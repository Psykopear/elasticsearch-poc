########################################################
# Pieces of code rewritten while reading documentation #
########################################################



# Default connection

from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=['localhost'], timeout=20)

###############################################
# Multiple clusters
connections.configure(
        default={'hosts': 'localhost'},
        dev={
            'hosts': ['esdev1.example.com:9200'],
            'sniff_on_start': True
            }
        )

# We can also add them later using aliases...
connections.create_connection('qa', hosts=['esqa1.example.com'], sniff_on_start=True)

connections.add_connection('qa', my_client)

# When searching we can refer to a specific connection by using aliases
s = Search(using='qa')

###############################################
# The api is chainable
s = Search().using(client).query('match', title='python')
# Send the request
response = s.execute()

# Requests are cached by default by the python client,
# subsequent calls to execute will not trigger additional
# requests being sent to Elasticsearch
# To force a request specify `ignore_cache=True` when sending
# a request


# Much like the Django orm we are familiar with, we can delete
# the documents matching a search by calling delete
s = Search().query('match', title='python')
response = s.delete()


#####################################
# QUERIES

# Query objects are a one-to-one mapping to ES quey DSL:
from elasticsearch_dsl.query import MultiMatch, Match

MultiMatch(query='python django', fields=['title', 'body'])
# {"mutli_match": {"query": "python django", "fields": ["title", "body"]}}

Match(title={'query': 'web framework', 'type': 'phrase'})
# {"match": {"title": {"query": "web framwork", "type": "phrase"})


# We can use the Q shortcut to construct the query
from elasticsearch_dsl.query import Q

q = Q('multi_match', query='python django', fields=['title', 'body'])
# Same as
Q({'multi_match': {'query': 'python django', 'fields': ['title', 'body']}})

# add the query to the searach object
s = s.query(q)


# We can also override the query used

s.query = Q('bool', must=[Q('match', title='python'), Q('match', body='best')])


# Query can be combined using logical operators:

Q('match', title='python') | Q('match', title='django')
# {'bool': {'should': [...]}}

Q('match', title='python') & Q('match', title='django')
# {'bool': {'must': [...]}}

~Q('match', title='python')
# {'bool': {'most_not': [..]}}


# Q can be used to have better control over the query form
q = Q('bool',
        must=[Q('match', title='python')],
        should=[Q(...), Q(...)],
        minimum_should_match=1
)
s = Search().query(q)


##################################################
# FILTERS

s = Search()
s = s.filter('terms', tags=['search', 'python'])
# Same as
s = s.query('bool', filter=[Q('terms', tags=['search', 'python'])])

# We can use exclude too
s = s.exclude('terms', tags=['search', 'python'])



#####################################################
# AGGREGATIONS

from elasticsearch_dsl.aggs import A

a = A('terms', field='category')


a.metric('clicks_per_category', 'sum', field='clicks')\
        .bucket('tags_per_category', 'terms', field='tags')

# This is how you add aggregations to the search object
s = Search()
a = A('terms', field='category')
s.aggs.bucket('category_terms', a)


s.aggs.bucket('per_category', 'terms', field='category')
s.aggs['per_category'].metric('clicks_per_category', 'sum', field='clicks')
s.aggs['per_category'].bucket('tags_per_category', 'terms', fireld='tags')



#########################################
# SORTING

s = Search().sort(
        'category',
        '-title',
        {'lines': {'order': 'asc', 'mode': 'avg'}})
)


#########################################3
# PAGINATION

# listslike

s = s[10:20]

for hit in s.scan():
    print(hit.title)


#########################################
# Extra properties

s = s.params(search_type='count')

s = s.source(['title', 'body'])
# Return only metadata
s = s.source(False)
#Explicit
s = s.source(include=['title'], exclude=['user.*'])
# Reset
s = s.source(None)


############################################
# Response

response = s.execute()

print(response.success())

print(response.took)
print(response.hits.total)
print(response.suggest.my_suggestions)


# Hits
response = s.execute()
for h in response:
    print(h.title, h.body)

# Result
h = response.hits[0]
print('/%s/%s/%s returned with score %f' % (
    h.meta.index, h.meta.doc_type, h.meta.id, h.meta.score))

# Aggregations
for tag in response.aggregations.per_tag.buckets:
    print(tag.key, tag.mex_lines.value)

# Multisearch

from elasticsearch_dsl import MultiSearch, Search
ms = MultiSearch(index='blogs')
ms = ms.add(Search().filter('term', tags='python'))
ms = ms.add(Search().filter('term', tags='elasticsearch'))

responses = ms.execute()

for response in responses:
    print("result for query %r." % response.search.query)
    for hit in response:
        print(hit.title)



##################################
# PERSISTENCE

# Mappings

from elasticsearch_dsl import Keyword, Mapping, Nested, Text

m = Mapping('my-type')
m.field('title', 'text')
m.field('category', 'text', fields={'raw': Keyword()})

comment = Nested()
comment.field('author', Text())
comment.field('created_at', Date())
m.field('comments', comment)
m.meta('_all', enabled=False)
m.save('my-index')

# We can also get the mapping from our production cluster
m = Mapping.from_es('my-index', 'my-type', using='prod')

m.update_from_es('my-index', using='qa')

m.save('my-index', using='prod')


#################################################
# DOCTYPE

from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
        analyzer, InnerObjectWrapper, Completion, Keyword, Text

html_strip = analyzer('html_strip',
        tokenizer='standard',
        filter=['standar', 'lowercase', 'stop', 'snowball'],
        char_filter=['html_strip'])

class Comment(InnerObjectWrapper):
    def age(self):
        return datetime.now() - self.created_at

class Post(DocType):
    title = Text()
    title_suggest = Completion()
    created_at = Date()
    published = Boolean()
    category = Text(
            analyzer=html_strip,
            fields={'raw': Keyword})

    comments = Nested(
        doc_class=Comment,
        properties={
            'author': Text(fields={'raw': Keyword()}),
            'content': Text(analyzer='snowball'),
            'created_at': Date()
        }
    )

    class Meta:
        index = 'blog'

    def add_comment(self, author, content):
        self.comments.append(
                {'author': author, 'content': content})

        def save(self, **kwargs):
            self.created_at = datetime.now()
            return super().save(**kwargs)


# To create a mapping in ES we can call the init method

Post.init()

# Create a new Post document
first = Post(title='my first blog post, yay!', published=True)
first.category = ['evereything', 'nothing']
first.meta.id = 47
#save into the cluster
first.save()



# Meta fields can be accessed and set vie the `meta` attribute

post = Post(meta={'id': 42})
print(post.meta.id)
post.meta.index = 'my-blog'

# Retrieve documentfirst = Post.get(id=42
first.add_comment('me', 'This is nice')
first.save()

# Avoid exception if document not found
p = Post.get(id='not-in-es', ignore=404)
p is None

# Retrieve multiple documents
posts = Post.mget([42, 47, 256])

# Search limied to a specific index and doc_type:
s = Post.search()
s = s.filter('term', published=True).query('match', title='first')
result = s.execute()
# Results are wrapper in the document's class
for post in results:
    print(post.meta.score, post.title)


#########################################
# INDEX

# indexe's metadata

from elasticsearch_dsl import Index, DocType, Text, analyzer

blogs = Index('blogs')

blogs.settings(
    number_of_shard=1,
    number_of_replicas=0
)

blogs.aliases(
    old_blogs={}
)

# Register a doc_type with the index
blogs.doc_type(Post)


#Also used as a class decorator
@blogs.doc_type
class Post(DocType):
    title = Text()


# Atatch a custom analyzer
html_strip = analyzer('html_strip',
        tokenizer='standard',
        filter=['standard', 'lowercase', 'stop', 'snowball'],
            char_filter(['html_strip']))

blogs.analyzer(html_strip)

# Delete index, ignor if it doesn't exist
blogs.delete(ignore=404)
blogs.create()
