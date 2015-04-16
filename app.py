import atexit
import threading, time
import pickle
import requests
import models
import logging
import yaml
from optparse import OptionParser
from flask import Flask, render_template

webapp = Flask(__name__)

@webapp.route('/')
def http_index():
  global sites

  return render_template('index.html', sites=sites)
 
DEFAULT_RATE = 2

# Sets up logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

config_file = 'config.yml'

def check_site(site):
    ''' This function pings the site['url'] and attempts
        to find site['content']. It will run every x secs
        in a thread '''

    logger.debug("Checking site: {0}".format(site))
    r = requests.get(site.url)
    logger.info("Site {0} returned code {1}".format(site.url, r.status_code))
    # add response time to time-series
    site.add_time(r.elapsed.total_seconds())
    
    logger.debug(r.elapsed.total_seconds())
    logger.debug(r.headers['content-type'])
    logger.debug(r.encoding)
    logger.debug(r.url)
    logger.info('Found string in site {0}: {1}'.format(site.url, site.content_str in r.text))
    t = threading.Timer(repeat_rate, check_site, [site])
    # set the daemon flag to exit the application, once the main
    # process stops
    t.daemon=True
    t.start()

def dump_sites():
    global sites
    models.pickle_to_file(sites)
    return

def main(repeat_rate, sites):
    atexit.register(dump_sites)

    for site in sites:
        threading.Thread(target=check_site, args=(site,), daemon=True).start()

    webapp.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':

  parser = OptionParser()
  parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO",
                    help="Set logging level")
  parser.add_option("-r", "--refresh_rate", dest="rate",
                    help="Set ping refresh rate")

  (options, args) = parser.parse_args()  
  config = yaml.load(open(config_file, 'r'))  
  sites = models.get_sites(config['Sites'])
  
  logger.setLevel(getattr(logging, options.loglevel))
  
  if options.rate:
    repeat_rate = int(options.rate)
  elif 'refresh_rate' in config.keys():
    repeat_rate = int(config['refresh_rate'])
  else:
    repeat_rate = DEFAULT_RATE # How often will a site be 'pinged'
  
  logger.info("Site refresh rate set to {0}".format(repeat_rate))
  main(repeat_rate, sites)
