#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
* todo
  * add proxy
"""
import sys,os
import json
import urlparse
import urllib
import shlex
from subprocess import Popen, PIPE
import tornado.web
import tornado.httpserver
import tornado.ioloop
import baker

def request_val(r):
    full_url=r.full_url()
    up=urlparse.urlparse(full_url)
    return dict(
        full_url=full_url,
        url=r.uri,
        method=r.method,
        headers=dict(r.headers),
        query=dict(urlparse.parse_qsl(r.query)),
        path=up.path,
        body=r.body,
        )

class HelloHandler(tornado.web.RequestHandler):
    vpath="/hello"
    def get(self):
        self.write("OH HAI\n")

class CatchHandler(tornado.web.RequestHandler):

    vpath=r"(.*)"

#    def __init__(self, app, req, **opt):
#        super(CatchHandler, self).__init__(app, req)

    @tornado.web.asynchronous
    def get(self, path):
        self.got_request()
        # todo: switch control back to main. have it reply.
        # may be auto-reply mode is needed..
        #self._reply()

    @tornado.web.asynchronous
    def post(self, path):
        self.got_request()
        #self._reply()

    def _reply(self, status, body=None, content_type=None, headers=None):
        self.set_status(status)
        if content_type:
            self.set_header('Content-Type', content_type)
        if body is not None:
            self.write(body)
        # xx headers
        self.finish()

    def got_request(self):
        print json.dumps(request_val(self.request))
        # xxx not used.. make this an echo server
        self._reply(200, 'OH HAI\n', content_type='text/plain')

class Requst(object):
    """class to encapsulate the request.
    instance could stand for tornado.web.RequestHandler or pseudo request objects.
    """
    pass
class RequestTornado(object):
    def __init__(self, handler):
        self.handler=handler
        self.val=request_val(handler.request)
class RequestPseudo(object):
    def __init__(self, val):
        self.val=val

class HttpDo(object):
    """scriptable httpd

* usage    
    hdo=HttpDo(8888)
    while True:
        print hdo.catch(timeout_sec=2)

"""

    def __init__(self, port=8888, loop=None):
        self.loop=loop or tornado.ioloop.IOLoop.instance()
        self.timer=None
        # xx document lifetime
        self.requests=[]
        self.current_request=None

        class HttpDoHandler(CatchHandler):
            def got_request(me):
                self.switch(RequestTornado(me))

        svr=server([(HttpDoHandler.vpath, HttpDoHandler)])
        svr.listen(port)

    def stop(self):
        self.loop.stop()

    def switch(self, val):
        """transfer control back to the main thread by yielding the val like in greenlet. 
        """
        self.requests.append(val)
        self.loop.stop()        # switch to loop.start()

    def got_timeout(self):
        self.switch(RequestPseudo(dict(method='_ctl', timeout=True)))

    def catch(self, timeout_sec=None):
        """block until next request and return it"""

        # set timer and start
        if timeout_sec:
            if self.timer:
                self.timer.stop()
                self.timer=None
            self.timer=tornado.ioloop.PeriodicCallback(self.got_timeout, 
                                                       timeout_sec*1000, 
                                                       self.loop)
            self.timer.start()

        self.loop.start()

        # return the request that has been caught to the main context.
        if self.requests:
            # xxx need to flush all requests. make this a generator?
            # a request that has been yielded to the main thread is the current-request.
            self.current_request=self.requests.pop(0)
            return self.current_request.val
        return None                 # timed out

    def reply(self, status, body=None, content_type='text/plain', headers=None):
        # precond: loop is in stopped state.
        # stash response, and start, so that the latter half of the handler can finish it.
        assert self.current_request
        if isinstance(self.current_request, RequestPseudo):
            pass                # dont replay to pseudo requests
        else:
            self.current_request.handler._reply(status, body, content_type=content_type)

def server(handlers):
    """
    handlers: [(HelloHandler.vpath, HelloHandler, {}), .. ]
    """
    app=tornado.web.Application(handlers)
    svr=tornado.httpserver.HTTPServer(app)
    return svr

@baker.command
def execute(port=8888, **command_map):
    """Execute commands given by command_map and reply with output.
WARNING: Use at your own risk. This invites shell in jection.
note: Command output is buffered. Large output will exhaust memory.

commands are specified as

     --<name> '<commadline>'

requests are made as /<name>[+arg1[+arg2]]

    {0},{1}..in commandline are replaced by words following the command name in request path.
    commands with {} must be escaped with {{}}.

example    
        httpdo.py execute \
		--installed-packages 'dpkg-query -f "${{Package}}=${{Version}}\n" -W {0}' \
		--top "top -b -n1" \
		--free "free -m"

$ curl http://localhost:8888/top
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
  ....

$ curl -s http://localhost:8888/free | grep buffers/ | awk '{ print $3, $4 }'
1846 1032

$ curl http://localhost:8888/installed-packages+python-\*
executing: ['dpkg-query', '-f', '${Package}=${Version}\\n', '-W', 'python-*']
python-appindicator=0.2.9-0ubuntu1.1
python-apport=1.14.1-0ubuntu8.1
..
    """
    # todo: 
    #    map querystring to named args.
    #    control output formatting 
    #    map exit status to http-code

    print 'command_map:', command_map

    hdo=HttpDo(int(port))
    while True:
        request=hdo.catch()
        #print request
        if request['method'].upper()=='GET':
            if request['path']=='/':
                listing='\n'.join(["/{name}\t{cmdline}".format(name=k,cmdline=v)
                                   for k,v in command_map.items()])+'\n'
                hdo.reply(status=200, 
                          content_type='text/plain', 
                          body=listing)
            else:
                cmdreq=urllib.unquote_plus(request['path'].lstrip('/'))
                cmdtuple=shlex.split(cmdreq)
                which=cmdtuple.pop(0)
                cmdlinet=command_map.get(which)
                if not cmdlinet:
                    raise tornado.web.HTTPError(404, 'unknown command '+which)

                cmdline=cmdlinet.format(*cmdtuple)
                cmdtoks=shlex.split(cmdline)

                # xx how to get status with communicate?
                # xx how to pass stdout and stderr?
                print >>sys.stderr, 'executing:', cmdtoks
                out,err=Popen(cmdtoks, stdout=PIPE, stderr=PIPE).communicate()
                if err:
                    print >>sys.stderr, err
                hdo.reply(status=200, 
                          content_type='application/octet-stream', 
                          body=out)
    

@baker.command
def hello(port=8888):
    """say hello"""
    svr=server([(HelloHandler.vpath, HelloHandler)])
    svr.listen(port)
    loop=tornado.ioloop.IOLoop.instance()
    loop.start()

@baker.command
def export(port=8888):
    """export files under cwd"""
    # todo: support directory indexing
    root=os.getcwd()
    svr=server([(r'/(.*)', tornado.web.StaticFileHandler, dict(path=root))])
    svr.listen(int(port))
    loop=tornado.ioloop.IOLoop.instance()
    loop.start()

@baker.command
def catch(port=8888, timeout_sec=None):
    """capture and dump http requests"""
    
    hdo=HttpDo(int(port))
    while True:
        request=hdo.catch(timeout_sec=timeout_sec)
        # dump request
        request_json=json.dumps(request)
        print request_json
        sys.stdout.flush()
        # reply
        if request['method'].upper() in ['GET', 'POST']:
            hdo.reply(status=200, 
                      content_type='text/json', 
                      # you requested ..
                      body=request_json+'\n')
        # terminate on timeout
        if request.get('timeout'):
            break
    
@baker.command
def test(port=8888):
    """demonstrate the HttpDo class usage
    """
    
    hdo=HttpDo(int(port))
    for i in range(5):
        request=hdo.catch(timeout_sec=1)
        print request
        # examine the request and reply to the client.
        if request['method'].upper() in ['GET', 'POST']:
            hdo.reply(status=200, 
                      content_type='text/plain', 
                      body='OH HAI {path}\n'.format(**request))

if __name__=='__main__':

    baker.run()
