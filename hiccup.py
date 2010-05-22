from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from django.utils import simplejson

class MainPage(webapp.RequestHandler):
    def post(self):
        self.get()
        
    def get(self):
        print "test"
        config = []
        if 'Hiccup-Config' in self.request.headers and len(self.request.headers['Hiccup-Config']) > 0:
            config = simplejson.loads(self.request.headers['Hiccup-Config'])

        if not config:
            self.response.out.write('No Hiccup-Config headers found')
            self.response.headers['Content-Type'] = 'text/plain'
            return

        if config['type'] == 'rest':
            return self.rest(config)
            
        if config['type'] == 'webhook':
            return self.webhook(config)


    def webhook(self, config):
        # Lets assume test succeeded otherwise spit fire in the form of 500s
        succeeded = True
        if 'url' not in config:
            self.error(500)
            return self.response.out.write('No webhook url provided')

        if 'method' not in config:
            config['method'] = "GET"

        if 'headers' not in config:
            config['headers'] = {}
        
        response = urlfetch.fetch(url = config['url'],
                                  method = config['method'],
                                  headers = config['headers']
                                  )

        if 'http-status' in config:
            self.response.headers['http-status-matches'] = True
            if config['http-status'] != response.status_code:
                self.response.headers['http-status-matches'] = False
                self.response.headers['http-status-expected'] = config['http-status']
                self.response.headers['http-status-received'] = response.status_code
                succeeded = False

        if 'response' in config:
            self.response.headers['response-matches'] = True
            if config['response'] == response.content:
                self.response.headers['response-matches'] = False
                self.response.headers['response-expected'] = config['response']
                self.response.headers['response-received'] = response.content
                succeeded = False

        if not succeeded:
            return self.error(500)

        return self.response.out.write('OK')

            
    def rest(self, config):
        headers = []
        if 'headers' in config:
            for name, val in config['headers']:
                print name, val

        if 'request-body' in config:
            self.response.headers['request-body-matches'] = True
            if self.request.body() != config['request-body']:
                self.response.headers['request-body-matches'] = False
                self.response.headers['request-body-expected'] = config['request-body']
                self.response.headers['request-body-received'] = self.request.query_string

        if 'query-string' in config:
            self.response.headers['query-string-matches'] = True
            if self.request.query_string != config['query-string']:
                self.response.headers['query-string-matches'] = False
                self.response.headers['query-string-expected'] = config['query-string']
                self.response.headers['query-string-received'] = self.request.query_string

        if 'response' in config:
            self.response.out.write(config['response'])
    
        if 'http-status' in config:
            self.response.set_status(config['http-status'])
        else:
            # default to 404
            self.response.set_status(404)

application = webapp.WSGIApplication(
    [('/.*', MainPage)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
