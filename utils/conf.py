import os

class Config(object):
    try:
        DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')
    except KeyError:
        DEBUG = True
        
    TESTING = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    FBAPI_SCOPE = ['email', 'user_about_me', 'user_activities', 'user_birthday',
                   'user_education_history', 'user_hometown', 'user_interests', 'user_likes',
                   'user_relationships', 'user_relationship_details', 'user_religion_politics',
                   'publish_actions', 'publish_stream', 'status_update', 'read_friendlists']
    
    #COOKIE_KEY = os.urandom(64)
    COOKIE_KEY = os.environ['SERVER_SOFTWARE'] + 'LTZ1loUSkfoFBdUlOGsjXn1Op1hnpGlnjq9zPXSOHlOd3mWlqh0hP5iZeeszXHV/MZyxPqlxzYAbz9OWuuL2JQ=='
    
    INDEX_GROUPS = [
                    {'order' : 1,
                     'name': 'basic', 
                     'indexes': ['density', 'geodesic', 'fragmentation', 'diameter']},
                    {'order' : 2,
                     'name': 'centrality',
                     'indexes': ['degree', 'centralization', 'closeness', 'eigenvector', 'betweenness']},
                    {'order' : 3,
                     'name': 'subgroups', 
                     'indexes': ['cliques', 'comembership', 'components']}
                    ]
    
    INDEX_FORMULAS = {'density': ('density(G) = \n\\frac{\\left | E \\right |} \n{\\left | N \\right | * \\left ( \\left | N \\right | %2B 1 \\right )}', ''),
                      'geodesic': ('distance(v_{1}, v_{2}) = min\\left ( d(v_{1}, v_{k}) %2B d(v_{k}, v_{2}) \\right )\n\\textrm{, } \\forall v_{k} \\in V',
                                   '\\textrm{ where }\nd(v_{i}, v_{j})=\\left \\{\n\\begin{matrix}\n0 \\textrm{ if } v_{i} = v_{j} \\\\\n1 \\textrm{ if } v_{i}, v_{j} \\in E \\\\\n%2B\\infty \\textrm{ otherwise}\n\\end{matrix}\n\\right.',
                                   'geodesic(G) = \\frac{\\sum_{v_{1}, v_{2}\\in V}{distance(v_{1}, v_{2})}}{\\left | E \\right |}', ''),
                      'fragmentation': ('fragmentation(G) = count(n_{1}, n_{2}) \\textrm{, } \\forall n_{1}\\in V, n_{2} \\in V\\\\\n\\textrm{where } distance(n_{1}, n_{2}) = %2B\\infty', ''),
                      'diameter': ('diameter(G) = max\\left ( distance(v_{1}, v_{2}) \\right )\n\\textrm {, } \\forall v_{1} \\in V, v_{2} \\in V \\\\\n\\textrm{ where }\ndistance(v_{1}, v_{2}) \\neq  %2B\\infty', ''),
                      'degree': ('centralization(v) = \\frac{\\left | (v, j) \\in V \\right |}{\\left | E \\right |}\n\\textrm{, } \\forall j \\in V \\\\\ndegree(G) = \\overline{centralization(v)}\n\\textrm{, } \\forall v \\in V', ''),
                      'centralization': ('centr(v) = \\frac{\\left | (v, j) \\in V \\right |}{\\left | E \\right |}\n\\textrm{, } \\forall j \\in V \\\\\nmaxval = max(centralization(v | V) \\\\\ncentralization(G) = \\overline{maxval - centr(v | V)}',''),
                      'closeness': ('close(v) = \\frac{1}{\\overline{distance(v, w | V)}} \\\\\ncloseness(G) = \\overline{close(v | V)}', ''),
                      'eigenvector': ('Av = \\lambda v \\Rightarrow eigen(v) = \\lambda \\textrm{, with } v \\neq 0 \\\\\n\\textrm{and A = square matrix } \\left | N \\right |*\\left | N \\right |\n\\textrm{with edge weights} \\\\\n\\quad & eigenvector(G) = \\overline{eigen(v | V)}', ''),
                      'betweenness': ('between(v) =\\sum_{v_{1},v_{2} \\in V} \\frac{\\sigma(v_{1}, v_{2}|V)}{\\sigma(v_{1}, v_{2})} \\\\\nbetweenness(G) = \\overline{between(v | V)}', ''),
                      'cliques': ('cliques(G) = \\left | (v_{1}, v_{2}, ..., v_{n} \\right | \\\\\n\\textrm{ with } v_{1} \\in V, v_{2} \\in V, ..., v_{n} \\in V \\\\\n\\textrm{ and } (v_{i}, v_{j}) \\in E \\textrm{, } \\forall i, j \\textrm{ in } 1...n', ''),
                      'comembership': ('cliqueset(G) = (v_{1}, v_{2}, ..., v_{n} \\\\\n\\textrm{ with } v_{1} \\in V, v_{2} \\in V, ..., v_{n} \\in V \\\\\n\\textrm{ and } (v_{i}, v_{j}) \\in E \\textrm{, } \\forall i, j \\textrm{ in } 1...n', 'comembership(G) = \\left | \\left ( S | cliqueset(G) \\right ) \\right | \\\\\n\\textrm{where } v_{1} \\in S \\textrm{ and } v_{2} \\in S', ''),
                      'components': ('components(G) = \\left | (v_{1}, v_{2}, ..., v_{n}) \\right |', '\\textrm{ with } v_{1} \\in V, v_{2} \\in V, ..., v_{n} \\in V \\\\\n\\textrm{ and } distance(v_{i}, v_{j}) \\neq %2B\\infty \\textrm{, }\n \\forall i, j \\textrm{ in } 1...n', '')}
    
    INDEX_TYPES = {'density': '%.2f%%',
                   'geodesic': '%.2f',
                   'fragmentation': '%.2f%%',
                   'diameter': '%.0f',
                   'degree': '%.2f%%',
                   'centralization': '%.2f%%',
                   'closeness': '%.2f%%',
                   'eigenvector': '%.2f%%',
                   'betweenness': '%.2f%%',
                   'cliques': '%.0f',
                   'comembership': '%.2f',
                   'components': '%.0f'}
    
    INDEXES = {'density': '''
                   This index measures the density of the network. The density of the network is the ratio of edges present in the network in respect
                   to the total number of possible edges of the network. A network of N nodes can have a maximum of N * (N-1) edges. This index
                   is computed from the number of edges divided by N * (N-1). Facebook networks are usually very sparse, so very low values of this
                   index are expected. Networks very sparse have a this index with a value between 1% and 2%, more dense networks have this index
                   with values around 5%, 6% or even more.''',
               'geodesic': '''
                   The geodesic distance is the smaller path length between two nodes. This index measure the mean of all the geodesic distances between
                   all connected nodes in the network. This value represents the number of connections each of your nodes have to contact to reach every
                   other person in your network. Very strongly connected networks have low levels for this index (between 4-6), more loosely connected
                   networks have higher values (10 or more).''',
               'fragmentation': '''
                   The fragmentation index shows how much the network is fragmented, that is how many nodes of the network cannot reach other nodes
                   in the network. This index is the ration of the nodes that are not accessible from any other node in respect to the total number
                   of nodes of the network. This index has low values, usually, a network with 10% or 20% on this index has very few unconnected nodes,
                   networks with more unconnected nodes have higher values for this index (30% or 40% are quite high values).''',
               'diameter': '''
                   The diameter of a network is the longest geodesic between two nodes randomly choosen inside the network. This index measure the
                   longest path that can be followed inside the network between its nodes without starting a circle. The lower this value, the more
                   interconnected the network is. Typical values may be around 10, networks with values smaller than that are networks more 
                   connected.''',
               'degree': '''
                   The centrality of a node in the network is an index of its level of participation and involvement. The "degree" index measures 
                   the average of the centralization of each node of the network. This index is computed by counting the edges each nodes participate
                   to. The degree centrality for a node v is the fraction of nodes it is connected to. The degree centrality values are normalized
                   by dividing by the maximum possible degree in a simple graph n-1 where n is the number of nodes in the network. This value in
                   Facebook networks is usually very low. Well connected networks has this index with values around 4% or 5%.''',
               'centralization': '''
                   This index measures the inequality of degree centrality for all the nodes in the network. It can be seen as an index fornetwork
                   hierarchy. The degree centrality for a node v is the fraction of nodes it is connected to. The degree centrality values are normalized
                   by dividing by the maximum possible degree in a simple graph n-1 where n is the number of nodes in the network. This value in
                   Facebook network si very far from 100%, networks with all nodes very similar in terms of number of connections have this value
                   around 20% or 30%.''',
               'closeness': '''
                   This index measures the average closeness for the nodes of the network. The closeness is measured from the geodesic distance of
                   the node with all other nodes in the network. Closeness centrality at a node is 1/average distance to all other nodes. In usual
                   Facebook networks, which are very sparse, this values are very far from 100%. Well connected networks have this have this
                   value around 40% or 50%.''',
               'eigenvector': '''
                   This index measures the average of the centrality for the nodes of the network. The eigenvector is used to compute this
                   centrality index. Eigenvector centrality is a measure of the influence of a node in a network. It assigns relative scores to all
                   nodes in the network based on the concept that connections to high-scoring nodes contribute more to the score of the node in
                   question than equal connections to low-scoring nodes. Usual values of this index, in Facebook networks, are very low. Well
                   connected networks have calues around 5% or 6%, while more loosely coupled networks have values around 2% or 3%.''',
               'betweenness': '''
                   This index measures the average of the betweenness centrality for the nodes of the network. The betweenness centrality is the
                   frequency in which a node is on the geodesic between all the nodes of the network. Betweenness centrality of a node v is the
                   sum of the fraction of all-pairs shortest paths that pass through v. Facebook networks which have this value high (around 10% or
                   even more) are networks in which few nodes are the key elements that keeps all the network connected.''',
               'cliques': '''
                   This index measures the number of cliques in the network. A clique is a subset of the graph with at least three nodes and
                   having every node connected with every other node in the subgraph. A well connected Facebook network has usually a high
                   number of cliques. This index value vary sensitively in respect to the network size. More large networks have naturally more
                   probability of having a higher number of cliques.''',
               'comembership': '''
                   This index measures for each node pair the number of cliques in which they compare together. From this matrix an average is
                   computed between each possible couple of nodes in the network. Facebook networks which are strongly connected and that present
                   only few sets of strongly connected subgraph, have this value higher than other networks (more loosely connected or with more
                   different sub-groups).''',
               'components': '''
                   This index measures the number of components of the network. A component is a subset of the graph nodes which are highly
                   connected between themselves and weakly connected to other nodes in the graph. This index represents the number of sub-groups
                   present in your Facebook network.'''}
    
    BASE_URL = 'https://rorschach-test-platform.appspot.com/'
    
    GOOGLE_APP_NAME = 'rorschach-test-platform'
    GOOGLE_CONSUMER_KEY = 'rorschach-test-platform.appspot.com'
    GOOGLE_CONSUMER_SECRET = 'vXLmDtq9t5ZC0Rub1DnBd1e4'
    
    if DEBUG:
        #Development FB App id and secret
        APP_NAMESPACE = 'rorschach_test_dev'
        FBAPI_APP_ID = '223295151080625'
        FBAPI_APP_SECRET = 'e4abb721b86a450e2ce866f1a7d8b1ce'
    else:
        #Production FB App id and secret
        APP_NAMESPACE = 'rorschach_test_platf'
        FBAPI_APP_ID = '165208080240405'
        FBAPI_APP_SECRET = '582c76c89b046135ee92231556882d3f'
        
    POST_TO_WALL = ("https://www.facebook.com/dialog/feed?redirect_uri=%s&"
                          "display=popup&app_id=%s" % (BASE_URL + 'static/pages/close.html', FBAPI_APP_ID))

    SEND_TO = ('https://www.facebook.com/dialog/send?'
               'redirect_uri=%s&display=popup&app_id=%s&link=%s'
               % (BASE_URL + 'static/pages/close.html', FBAPI_APP_ID, 'http://apps.facebook.com/' + FBAPI_APP_ID))