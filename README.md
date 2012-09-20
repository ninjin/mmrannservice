# MMRannService #

An example rapid annotation web service for [brat][brat] using the [National
Library of Medicine MetaMap tool][metamap].

[brat]: http://brat.nlplab.org
[metamap]: http://metamap.nlm.nih.gov/

## Instructions ##

This tool depends on several additional tools:

* Python 2.6 or newer
* [The Python flup library][flup]
* Jython
* MetaMap
* MetaMap Java bindings

Once you have the above installed, change `config.py` to suit your
environment. Then test the connection to MetaMap:

    echo 'Brucella abortus' | ./mmrannservice.py

You should now be ready to start the web service, a configuration for LigHTTPD
is included (`lighttpd.conf`). Edit it to match your set-up and then start the
server:

    lighttpd -D -f lighttpd.conf

You should now be able to test your service:

    curl 'http://localhost:47111/?classify=Brucella+abortus'

Now all you need to do is jump over to your brat installation and add the
service to your `tools.conf` and you are good to annotate!

[flup]: http://pypi.python.org/pypi/flup
