py-httpdo
=========

scriptable httpd

### api

        hdo=HttpDo(int(port))
        while True:
            request=hdo.catch(timeout_sec=1)
            if request['method']=='GET':
                hdo.reply(status=200, body='OH HAI\n')

A program can launch an httpd and control its responses.
This can be handy for testing an http proxy.


### http request dumping

       httpdo.py catch 8888 | jq -M .
       # in other terminal: curl -s 'http://localhost:8888/free?foo=42'
       {
         "method": "GET",
         "full_url": "http://localhost:8888/free?foo=42",
         "query": {
           "foo": "42"
         },
         "url": "/free?foo=42",
         "path": "/free",
         "headers": {
           "User-Agent": "curl/7.21.0",
           "Accept": "*/*",
           "Host": "localhost:8888"
         }
       }


### A quick web server to export files 
Similar to python -m SimpleHTTPServer

        httpdo.py export

        curl http://localhost:8888/README.md
        py-httpdo
        =========


### execute command and reply with output

	somehost$ ./httpdo.py execute \
		--installed-packages 'dpkg-query -f "$${{Package}}=$${{Version}}\n" -W {0}' \
		--top "top -b -n1" \
		--free 'free -m'


       $ curl http://somehost:8888/top
         % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
         ....


       $ curl -s http://somehost:8888/free | grep buffers/ | awk '{ print $3, $4 }'
       1846 1032


       $ curl http://somehost:8888/installed-packages+python-\*
       executing: ['dpkg-query', '-f', '${Package}=${Version}\\n', '-W', 'python-*']
       python-appindicator=0.2.9-0ubuntu1.1
       python-apport=1.14.1-0ubuntu8.1
       ..
