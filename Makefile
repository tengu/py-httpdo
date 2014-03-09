
all:

clean:
	rm -fr *.egg-info dist build

register:
	python setup.py sdist register

upload:
	python setup.py sdist upload

h:
	./httpdo.py hello
c:
	./httpdo.py catch 8888 5 | jq -M .

cc:
	./httpdo.py catch 8888

e:
	./httpdo.py export

a:
	./httpdo.py api

u:
	./httpdo.py 

x:
	./httpdo.py execute \
		--installed-packages 'dpkg-query -f "$${{Package}}=$${{Version}}\n" -W {0}' \
		--top "top -b -n1" \
		--free 'free -m'

xh:
	./httpdo.py execute -h

