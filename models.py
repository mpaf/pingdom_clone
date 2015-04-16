import yaml
import time
import pickle
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

saved_sites_file = 'saved_sites.pkl'
config_file = 'config.yml'

class Site(object):
  
  resp_time = []  
  def __repr__(self):
    return "<site url:'{0}' content_str '{1}'>".format(self.url, self.content_str)
  def __eq__(self, other):
    return self.url == other.url

  def __init__(self, url, content_str):
    self.url = url
    self.content_str = content_str

  def add_time(self, response_time):
    if type(response_time) != float:
      raise TypeError("response time must be a float")
 
    self.resp_time.append([time.time(), response_time])

def pickle_to_file(sites):
  
  if sites:
    if type(sites) == list:
      if type(sites[0]) == Site:
        with open(saved_sites_file, 'wb') as output:
          pickle.dump(sites, output, pickle.HIGHEST_PROTOCOL)
          return 
  raise TypeError("Site list empty or of incorrect type")

def pickled_sites():

  # Try to get list of Site models
  try:
    with open(saved_sites_file, 'rb') as input:
      saved_sites = pickle.load(input)
      for site in saved_sites:
        logger.debug('found saved site {0} in {1}'.format(site.url, saved_sites_file))
  except:
    logger.debug("File {0} doesn't exist yet".format(saved_sites_file))
    saved_sites = []

  return saved_sites

def configed_sites():
  cfg_sites = []
  sites = yaml.load(open(config_file, 'r'))  
  
  for site in sites['Sites']:
    site_obj = Site(site['url'], site['content'])
    cfg_sites.append(site_obj)
    logger.debug('found site {0} in config file'.format(site_obj))
  
  return cfg_sites

def get_sites():
  ''' change cfg_sites to add possible data series saved
      to disk '''

  cfg_sites = configed_sites()
  saved_sites = pickled_sites()  
  for cfg_site in cfg_sites:
    logger.debug('process cfg site {0}'.format(cfg_site)) 
    found_saved = next((x for x in saved_sites if x.url == cfg_site.url), None)
    if found_saved:
      logger.debug('found saved site, copy response time series {0}'.format(found_saved.resp_time))
      cfg_site.resp_time = found_saved.resp_time
    else:
      logger.debug('saved site not in cfg, discard')
  
  return cfg_sites
