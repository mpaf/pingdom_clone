import time
import threading
import pickle
import logging

# Sets up logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# File where to save Site data
SAVED_SITES_FILE = 'saved_sites.pkl'
# Frequency at which Site data is saved to disk
DUMP_RATE = 30

# This variable keeps the list of Site objects
# and their all-time response times in memory
# during the application run.

class Site(object):

  def __repr__(self):
    return "<site url:'{0}' content_str '{1}'>".format(self.url, self.content_str)
  def __eq__(self, other):
    return self.url == other.url
  # hash of object to allow creation of sets
  def __hash__(self):
     return hash(self.url)

  def __init__(self, url, content_str):
    self.url = url
    self.content_str = content_str
    self.resp_time=[]
    self.last_http_code = None
    self.string_matched = False
    self.encoding = None

  def dump_site_for_inspection(self):
    ''' dump the html for a site '''
    import requests
    r = requests.get(self.url)
    # remove http and .com, .net etc. from file name
    with open(self.url.split('//')[1].lstrip('www.')[:-3] + '.html', 'w') as f:
      f.write(r.text)

  def add_time(self, response_time):
    if type(response_time) != float:
      raise TypeError("response time must be a float")
    self.resp_time.append([time.time(), response_time*1000.0])

def pickle_to_file(sites):
  if sites:
    if type(sites) == list:
      if type(sites[0]) == Site:
        with open(SAVED_SITES_FILE, 'wb') as output:

          pickle.dump(sites, output, pickle.HIGHEST_PROTOCOL)
          return
  raise TypeError("Site list empty or of incorrect type")

# No worries passing variables referencing large
# data to functions, as Python passes it by reference
def dump_sites(sites, dump_rate=DUMP_RATE):
    ''' pickle Site objects to the filesystem
        ran periodically at dump_rate, or when
        app exits '''

    logger.debug("saving all site data to disk")
    pickle_to_file(sites)
    t = threading.Timer(dump_rate, dump_sites, [sites])
    t.daemon=True
    t.start()
    return

def get_pickled_sites():

  # Try to get list of Site models
  try:
    with open(SAVED_SITES_FILE, 'rb') as input:
      saved_sites = pickle.load(input)
      for site in saved_sites:
        logger.debug('found saved site {0} in {1}'.format(site.url, SAVED_SITES_FILE))
  except:
    logger.debug("File {0} doesn't exist yet".format(SAVED_SITES_FILE))
    saved_sites = []

  return saved_sites

def configed_sites(sites_dict):
  cfg_sites = []

  for site in sites_dict:
    site_obj = Site(site['url'], site['content'])
    if site_obj in cfg_sites:  # this works thanks to equality and hash
                               # functions defined in class
        logger.debug('Found duplicate site {0}'.format(site_obj.url))
    else:
        cfg_sites.append(site_obj)
        logger.debug('found site {0} in config file'.format(site_obj.url))

  return cfg_sites

def get_sites(cfg_sites_dict):
  ''' change cfg_sites to add possible data series saved
      to disk '''

  cfg_sites = configed_sites(cfg_sites_dict)
  saved_sites = get_pickled_sites()
  for cfg_site in cfg_sites:
    logger.debug('process cfg site {0}'.format(cfg_site))
    found_saved = next((x for x in saved_sites if x.url == cfg_site.url), None)
    if found_saved:
      logger.debug('found saved site, copy response time series {0}'.format(found_saved.resp_time))
      cfg_site.resp_time = found_saved.resp_time
    else:
      logger.debug('saved site not in cfg, discard')

  return cfg_sites
