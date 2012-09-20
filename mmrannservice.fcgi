#!/usr/bin/env python

'''
FastCGI wrapper for our rapid annotation service.

Note: This module may seem weird to you, why am I not working from within
Jython to do FastCGI? Well, it turns out that Java-land really hates FastCGI
(and loves their bloody Servlets to death). The one straight-forward
implementation I found breaks with LigHTTPD, which is a bit of a bummer.
Furthermore, all standard Python libraries break for Jython since you can't
easily pass a file-descriptor to a nother process and pick it up as a socket.
All-in-all, it is easier to do a simple wrapper script and stay in CPython,
but do tell me if you find a nice way to work around this and actually use
Jython. In the end, I regret not just wrapping the MetaMap binary from the
start.

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2012-09-20
'''

from cgi import parse_qs
from json import dumps as json_dumps
from os.path import dirname, join as path_join
from subprocess import Popen, PIPE

from flup.server.fcgi import WSGIServer

### Constants
SERVICE_SCRIPT = path_join(dirname(__file__), 'mmrannservice.py')
###

def __query_service_process(query):
    global SERVICE_PROCESS
    SERVICE_PROCESS.stdin.write(query + '\n')
    SERVICE_PROCESS.stdin.flush()
    _, res_str = SERVICE_PROCESS.stdout.readline().split('\t')
  
    # Handle the slightly ugly conversion from text to result, it is not nice
    # to rely on the Python printing style for parsing
    return eval(res_str)

def _serve(query):
    resp_dict = {}

    try:
        to_classify = set(query['classify'])
    except KeyError:
        resp_dict['error'] = 'noClassifyArgument'
        return resp_dict

    res_dict = {}
    for s in to_classify:
        res_dict[s] = __query_service_process(s)
    resp_dict['result'] = res_dict

    return resp_dict

def mmrannservice_app(environ, start_response):
    query = parse_qs(environ['QUERY_STRING'])

    resp_dict = _serve(query)
    resp_json = json_dumps(resp_dict)

    start_response('200 OK', [('Content-Type', 'application/json'), ])
    yield resp_json

if __name__ == '__main__':
    # Pre-start the slow-started service process
    global SERVICE_PROCESS
    SERVICE_PROCESS = Popen(SERVICE_SCRIPT, stdin=PIPE, stdout=PIPE)
    WSGIServer(mmrannservice_app).run()
