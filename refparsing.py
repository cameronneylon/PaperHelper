from pyparsing import *
import urllib
from waveapi import simplejson as json
import logging

leftdelim = Literal('(').suppress()
rightdelim = Literal(')').suppress()
andword = Literal('and').suppress()
etal = Literal('et al'). suppress()
comma = Literal(',').suppress()
authorname = Regex('[a-zA-Z]{1,14}').setResultsName('authorname')
authornameinlist = authorname + (Optional(comma) & 
                                 Optional(etal) & Optional(andword))
authorlist = OneOrMore(authornameinlist).setResultsName('authorlist')

# years, between 1980 and 2012, four-digit format
lowest_year = 1980
highest_year = 2013
years = " ".join([("%d" % x) for x in xrange(lowest_year, highest_year)])
year = oneOf(years).setResultsName('year')

citation = leftdelim + authorlist + Optional(etal) + year + rightdelim

def refParse(text):
    results = citation.parseString(text)
    dict = {'authors' : results.authorlist,
            'year'    : results.year}

    return dict


def getRef(authorlist, year):
    """Returns a dictionary parsed from citeulike via YQL with title, reference etc"""

    querydict = {"format":"json"}

    querystring = "select item from xml where url='http://www.citeulike.org/rss/user/CameronNeylon/'"
    querystring = querystring + ' and item.date LIKE "%s%%"' % year
    for author in authorlist:
        querystring = querystring + ' and item.creator LIKE "%%%s%%"' % author

    querydict['q'] = querystring
    query = urllib.urlencode(querydict)
    result = urllib.urlopen('http://query.yahooapis.com/v1/public/yql?%s'
                                           % query)
    jsonresult = json.load(result)

    # The following will break if there is more than one result returned but will do for moment

    try: 
        jsonitem = jsonresult.get('query', None).get('results', None
                                  ).get('RDF', None).get('item', None)
    except:
        return
    citation = { 'authors'  : jsonitem.get('creator', None),
                 'title'    : jsonitem.get('title', None)[0],
                 'journal'  : jsonitem.get('publicationName', None),
                 'volume'   : jsonitem.get('volume', None),
                 'page'     : jsonitem.get('startingPage', None),
                 'year'     : year,
                 'link'     : jsonitem.get('about', None)}

    return citation
    
def formatReference(citation):
    """Return a simple formatted reference"""

    authorstring = ''
    cite = ''
    logging.debug(citation)
   
    if len(citation['authors']) == 1:
        cite = "(" + citation['authors'][0] + ", " + citation['year'] + ")"
    elif len(citation['authors']) == 2:
        cite = "(" + citation['authors'][0] + " and " + citation['authors'][1] + ", " + citation['year'] + ")"
    elif len(citation['authors']) >= 3:
        cite = "(" + citation['authors'][0] + " et al, " + citation['year'] + ")"

    for author in citation['authors']:
        authorstring = authorstring + author + ', '

    citation['authors'] = authorstring

    reference = "%(authors)s(%(year)s) %(title)s, %(journal)s, %(volume)s:%(page)s" % citation

    return reference, cite
    

# tests

if __name__ == '__main__':

    tests = [ "(Badge, 2010)",
              "(Badge, Cann, and Neylon, 2010)", 
              "(Badge, Cann and Neylon, 2010)",
              "(Bergstrom, 2009)",
              "(Savage and Vickers, 2009)" ]

    for t in tests:
      try:
        results = refParse(t)
        print t, results, "\n\n"
        
        print formatReference(getRef(results['authors'], results['year'])), "\n\n"
        
        
      except ParseException, pe:
        print pe
