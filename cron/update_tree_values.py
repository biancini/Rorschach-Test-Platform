from __future__ import with_statement

from google.appengine.api import files
from google.appengine.ext import db

from utils import conf
import datetime

conf = conf.Config()
TABWIDTH = 16

cols = [{'order':  1, 'name': 'nodes',          'buckets': ['0-250', '251-500', '501-750', '751-1000', '>1000']  },
        {'order':  2, 'name': 'density',        'buckets': ['0-2', '2-4', '4-7', '>7']                           },
        {'order':  3, 'name': 'geodesic',       'buckets': ['<4', '4-6', '6-10', '>10']                          },
        {'order':  4, 'name': 'fragmentation',  'buckets': ['<10', '10-20', '20-30', '30-40', '>40']             },
        {'order':  5, 'name': 'diameter',       'buckets': ['<5', '5-8', '8-12', '12-16', '>16']                 },
        {'order':  6, 'name': 'degree',         'buckets': ['0-2', '2-4', '4-6', '>6']                           },
        {'order':  7, 'name': 'centralization', 'buckets': ['<7', '7-13', '13-20', '20-30', '>30']               },
        {'order':  8, 'name': 'closeness',      'buckets': ['<15', '15-30', '30-50', '>50']                      },
        {'order':  9, 'name': 'eigenvector',    'buckets': ['<2', '2-4', '4-6', '>6']                            },
        {'order': 10, 'name': 'betweenness',    'buckets': ['0-1', '1-2', '2-3', '>3']                           },
        {'order': 11, 'name': 'cliques',        'buckets': ['<200', '200-500', '500-800', '>800']                },
        {'order': 12, 'name': 'comembership',   'buckets': ['0-0.5', '0.5-1', '1-1.5', '1.5-2', '>2']            },
        {'order': 13, 'name': 'components',     'buckets': ['<4', '4-6', '6-8', '8-10', '>10']                   }]

dict_cols = dict((item['name'], item['buckets']) for item in cols)

def read_values():
    all_networks, all_indexes = [], []
    
    q = db.GqlQuery("SELECT * FROM Network")
    for network in q: all_networks += [network]
    
    q = db.GqlQuery("SELECT * FROM Index")
    for index in q: all_indexes += [index]
    
    return all_networks, all_indexes

def get_bucket(value, buckets):
    for bucket in buckets:
        if '<' in bucket:
            if value < eval(bucket.replace('<', '')): return bucket
        elif '>' in bucket:
            if value > eval(bucket.replace('>', '')): return bucket
        else:
            if '-' in bucket:
                margins = bucket.split('-')
                if value >= eval(margins[0]) and value <= eval(margins[1]): return bucket
            else:
                if value == eval(bucket): return bucket
        
    return 'Err'

def write_value(value_name, indexes):
    strToWrite = ''
    
    if value_name in indexes:
        strToWrite += "%-10s\t" % get_bucket(indexes[value_name].value, dict_cols[value_name])
    else: strToWrite += "%-10s\t" % 'NaN'
    
    return strToWrite

def create_files(all_networks, all_indexes, filesdata):
    for curfile in filesdata:
        strToWrite  = "Class names: %s\n\n" % ' '.join(curfile['classes'])
        strToWrite += "Feature names and their values:\n"
        for item in cols:
            if item['name'] in curfile['needed_cols']: strToWrite += "    %s => %s\n" % (item['name'], ' '.join(item['buckets']))
        strToWrite += "\n\n"
    
        strToWrite += "Training Data:\n\n\n"
        strToWrite += ("%-10s\t" * 2) % ('sample', 'class')
        for col in curfile['needed_cols']:
            strToWrite += "%-10s\t" % col
        strToWrite += "\n"
        
        strToWrite += "=" * TABWIDTH * (2 + len(curfile['needed_cols'])) +"\n\n"
        
        i = 0
        for network in all_networks:
            strToWrite += "%-10s_%s\t" % (network.uid, i)
            strToWrite += "%-10s\t" % '???' # unknown class (to be specified by hand)
            strToWrite += "%-10s\t" % dict_cols['nodes'][len(network.getnodes()) / 250]
            
            indexes = {}
            for index in all_indexes:
                if index.uid == network.uid: indexes[index.name] = index
    
            for item in cols:
                if item['name'] != 'nodes' and item['name'] in curfile['needed_cols']: strToWrite += write_value(item['name'], indexes)
            
            i += 1
            strToWrite += "\n"
    
        #print strToWrite.expandtabs(TABWIDTH)
        file_name = 'tree_%s_%s.dat' % (curfile['filename'], datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        blob_name = files.blobstore.create(mime_type='text/plain', _blobinfo_uploaded_filename=file_name)
        with files.open(blob_name, 'a', exclusive_lock=True) as f:
            f.write(strToWrite.expandtabs(TABWIDTH))
            f.close(finalize=True)

def run():
    cols.sort((lambda x,y: cmp(x['order'], y['order'])))
    all_networks, all_indexes = read_values()
    
    create_files(all_networks, all_indexes,
                 [{'filename': 'all_data',
                  'classes': ('???'),
                  'needed_cols': ('nodes', 'density', 'geodesic', 'fragmentation', 'diameter', 'degree', 'centralization' 'closeness', 'eigenvector', 'betweenness', 'cliques', 'comembership', 'components')},
                  {'filename': 'net_connection',
                  'classes': ('strong', 'loose'),
                  'needed_cols': ('nodes', 'density', 'geodesic', 'diameter', 'components')}])
    