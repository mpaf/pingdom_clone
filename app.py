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
global sites

sites = []

@webapp.route('/')
def http_index():
  global sites

  return render_template('index.html', sites=sites)

# Frequency at which checks are run
# (except if overriden by config file
#  or command-line)
DEFAULT_RATE = 2
# Frequency at which Site data is saved to disk
DUMP_RATE = 30

# Sets up logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

config_file = 'config.yml'

def check_site(site, timeout):
    ''' This function pings the site['url'] and attempts
        to find site['content']. It will run every x secs
        in a thread '''

    logger.debug("Checking site: {0} with timeout {1}".format(site, timeout))
    try:
        # Set a timeout that is smaller than the next refresh of the site
        r = requests.get(site.url, timeout=timeout)
        logger.info("Site {0} returned code {1}".format(site.url, r.status_code))
        # add response time to time-series
        site.add_time(r.elapsed.total_seconds())
        site.last_http_code = r.status_code
        site.string_matched = site.content_str in r.text
        logger.debug(r.elapsed.total_seconds())
        logger.debug(r.headers['content-type'])
        logger.debug(r.encoding)
        logger.debug(r.url)
        logger.info('Found string in site {0}: {1}'.format(site.url, site.string_matched))
        t = threading.Timer(repeat_rate, check_site, [site, timeout])
        # set the daemon flag to exit the application, once the main
        # process stops
        t.daemon=True
        t.start()
    except requests.exceptions.Timeout:
        logger.warning("Timed out checking for {0}, will try again".format(site.url))
        t = threading.Timer(repeat_rate, check_site, [site, timeout])
        t.daemon=True
        t.start()

    except Exception as e:
        # exception requesting site, log warning and wait some time
        # before attempting to request site again
        logger.warning("Error requesting {0}: {1}".format(site.url, e))
        # wait 5x the normal check repeat rate
        t = threading.Timer(5*repeat_rate, check_site, [site, timeout])
        t.daemon=True
        t.start()

def dump_sites(dump_rate=DUMP_RATE):
    ''' pickle Site objects to the filesystem
        ran periodically at dump_rate, or when
        app exits '''
    global sites
    logger.info("saving all site data to disk")
    models.pickle_to_file(sites)
    t = threading.Timer(dump_rate, dump_sites)
    t.daemon=True
    t.start()
    return

def main(repeat_rate, sites):

    # dump all sites and response times to a pickled file
    # in the current directory
    atexit.register(dump_sites)

    # set a recurring thread to dump all site info to disk
    threading.Thread(target=dump_sites, daemon=True).start()

    for site in sites:
        # adjust timeout to be slightly smaller than refresh rate of thread
        threading.Thread(target=check_site, args=(site, repeat_rate-0.01), daemon=True).start()

if __name__ == '__main__':

  parser = OptionParser()
  parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO",
                    help="Set logging level")
  parser.add_option("--nohistory", dest="nohistory", action="store_true")
  parser.add_option("-r", "--refresh_rate", dest="rate",
                    help="Set ping refresh rate")

  (options, args) = parser.parse_args()
  config = yaml.load(open(config_file, 'r'))
  sites = models.get_sites(config['sites'])

  logger.setLevel(getattr(logging, options.loglevel))

  if options.nohistory:
    import os
    try:
      os.remove(os.path.abspath(models.saved_sites_file))
      logger.info("Removed {0} cache file".format(models.saved_sites_file))
    except:
      logger.info("Could not remove {0} cache file".format(os.path.abspath(models.saved_sites_file)))

  if options.rate:
    repeat_rate = int(options.rate)
  elif 'refresh_rate' in config.keys():
    repeat_rate = int(config['refresh_rate'])
  else:
    repeat_rate = DEFAULT_RATE # How often will a site be 'pinged'

  logger.info("Site refresh rate set to {0}".format(repeat_rate))
  main(repeat_rate, sites)
  webapp.run(debug=True, host='0.0.0.0', port=8080)
