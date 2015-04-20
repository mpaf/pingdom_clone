#!/usr/bin/env python3
#
# Pingdom-like site content checker, logs results to file
# and runs a webserver that shows the results of the different
# checks as plots, and status indicator for up/down. Just install
# the requirements and run python app.py (with Python v3.4)
#
# You can configure the checks via yaml in CONFIG_FILE, a
# description of the configuration options is provided in
# the file
#
# Author: Miguel Ferreira
# Date: 15 April 2015
#
# Version: 1.0
#

import atexit
import threading
import requests
import models
import logging
from logging.handlers import RotatingFileHandler
import yaml
from optparse import OptionParser
from flask import Flask, render_template

VERSION = 1.0
# Frequency at which checks are run
# (except if overriden by config file
#  or command-line)
DEFAULT_RATE = 2
# Frequency at which Site data is saved to disk
DUMP_RATE = 30
# Config file to get site information
# and general app parameters
CONFIG_FILE = 'config.yml'
# Web listening port
SERVER_PORT = 8080
# file where site check info will be logged
LOG_FILE = 'site_results.log'

logger = logging.getLogger(__name__)

# One check_site thread will run periodically per
# site monitored. This app will consist of the main
# process + number of sites thread + thread for dumping
# site data to disk

def check_site(site, repeat_rate, timeout):
    """ This function pings the site['url'] and attempts
        to find site['content']. It will run every repeat_rate secs
        in a thread, and sets a timeout for the web request, which is
        typically slightly less than the repeat_rate """

    logger.debug("Checking site: {0} with timeout {1}".format(site, timeout))
    try:
        # Set a timeout that is smaller than the next refresh of the site
        # and add response time to time-series
        r = requests.get(site.url, timeout=timeout)
        site.add_time(r.elapsed.total_seconds())
        site.last_http_code = r.status_code
        site.encoding = r.encoding
        site.string_matched = site.content_str.lower() in r.text.lower()
        if site.string_matched:
            content_string = '"{0}" Found!'.format(site.content_str)
        else:
            content_string = '"{0}" NOT found!'.format(site.content_str)
        logger.info(
            "{0} returned HTTP code {1} in {2}ms, {3} ({4})"
            .format(site.url, r.status_code, r.elapsed.total_seconds()*1000.0,
                    content_string, r.encoding)
        )
        # set the daemon flag to exit the application, once the main
        # process stops
        t = threading.Timer(repeat_rate, check_site, [site, repeat_rate, timeout])
        t.daemon=True
        t.start()
    except requests.exceptions.Timeout:
        # timeout exception, try again in next iteration of the checks
        logger.warning("Timed out (>{1}) checking for {0}, will keep trying".
                        format(site.url, timeout))
        t = threading.Timer(repeat_rate, check_site, [site, repeat_rate, timeout])
        t.daemon=True
        t.start()

    except Exception as e:
        # exception requesting site (could not connect) log warning and
        # wait some time before attempting to request site again
        # wait 5x the normal check repeat rate
        logger.warning("{0} EXCEPTION: {1}, will try again after a while".
                        format(site.url, e))
        t = threading.Timer(5*repeat_rate, check_site, [site, repeat_rate, timeout])
        t.daemon=True
        t.start()

# Set up a flask server
webapp = Flask(__name__)

# The main view of the website, showing all check info
@webapp.route('/')
def http_index():
  global sites

  # render a webpage with all the site information collected so far
  # limit to 200 last samples
  limited_sites = []
  for site in sites:
    new_site = site
    new_site.resp_time = site.resp_time[-200:]
    limited_sites.append(new_site)

  return render_template('index.html', sites=limited_sites)

# route to serve an HTTP 500 error, to test the app
@webapp.route('/500')
def error_page():
  # Always generate a server error, for testing pingdom-clone
  return "This is a page returning a HTTP 500 error", 500

# page not found is redirected here
@webapp.errorhandler(404)
def pageNotFound(error):
    return "What did you want to see here?", 404

# errors are redirected here
@webapp.errorhandler(500)
def pageError(error):
    return "Wow, you crashed our server! :'("

def check_loop(repeat_rate, sites):
  """ This function will start two daemon thread loops repeating
      every repeat_rate and DUMP_RATE to check url response and
      dump current Site model information to disk respectively. """
  # dump all sites and response times to a pickled file
  # in the current directory if application exits
  atexit.register(models.dump_sites, sites)
  # set a recurring thread to dump all site info to disk
  t=threading.Timer(DUMP_RATE, models.dump_sites, [sites, DUMP_RATE])
  t.daemon=True
  t.start()

  for site in sites:
    # adjust timeout to be slightly smaller than refresh rate of thread
    t=threading.Timer(repeat_rate, check_site, [site, repeat_rate, repeat_rate-0.01])
    t.daemon=True
    t.start()

def main():
  """ Process config file and command-line options, start main function and
  a web server listening on localhost:SERVER_PORT based on the Flask web
  microframework. To stop the script from running just type CTRL+C from
  the terminal which will immediately exit the webserver and the threads. """

  parser = OptionParser(description="Pingdom-like site checker, and webapp",
                        version="%prog {0}".format(VERSION))
  parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO",
                    help="Set logging level")
  parser.add_option("--nohistory", dest="nohistory", action="store_true",
                    help="erase pickled site data history from disk")
  parser.add_option("-r", "--refresh_rate", dest="rate",
                    help="Set ping refresh rate")
  parser.add_option("-o", "--logfile", dest="logfile", default=LOG_FILE,
                    help="Set file where to log site data")

  (options, args) = parser.parse_args()
  config = yaml.load(open(CONFIG_FILE, 'r'))

  # Set up logging, two handlers, one for the
  # file to disk with level INFO that will
  # capture the information about the checks
  # the other handler will have a level set
  # by the command-line (default INFO) and outputs
  # to stdout
  formatter = logging.Formatter(
    '%(asctime)s: %(message)s'
  )

  logger.setLevel(logging.DEBUG)
  streamhandler = logging.StreamHandler()
  filehandler = RotatingFileHandler(
    options.logfile, maxBytes=10*1024*1024, backupCount=5
  )
  filehandler.setFormatter(formatter)
  filehandler.setLevel(logging.INFO)
  logger.addHandler(streamhandler)
  logger.addHandler(filehandler)

  # Change logging level in the streamhandler
  streamhandler.setLevel(getattr(logging, options.loglevel))

  if options.nohistory:
    import os
    try:
      os.remove(os.path.abspath(models.SAVED_SITES_FILE))
      logger.debug("Removed {0} cache file".format(models.SAVED_SITES_FILE))
    except:
      logger.debug("Could not remove {0} cache file".format(os.path.abspath(models.SAVED_SITES_FILE)))

  if options.rate:
    repeat_rate = int(options.rate)
  elif 'refresh_rate' in config.keys():
    repeat_rate = int(config['refresh_rate'])
  else:
    repeat_rate = DEFAULT_RATE # How often will a site be 'pinged'
  logger.debug("Site refresh rate set to {0}".format(repeat_rate))

  # define that sites will be a global variable also used by the
  # web app for displaying the content
  global sites

  # store reference to list of sites in models
  # namespace to retrieve it in webserver views.
  sites = models.get_sites(config['sites'])

  # and use it for the check loop
  check_loop(repeat_rate, sites)

  webapp.run(host='0.0.0.0', port=SERVER_PORT)

if __name__ == '__main__':
  """ Application entry point """
  main()
