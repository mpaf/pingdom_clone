import atexit
import threading, time
import pickle
import requests
from getchar import getch
import models
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

repeat_rate = 2 # How often will a site be 'pinged'

sites = models.get_sites()

def input_thread(stop_flag):
    print("Press a key to quit...")
    input()
    stop_flag.append(None)
    return

def check_site(site):
    ''' This function pings the site['url'] and attempts
        to find site['content']. It will run every x secs
        in a thread '''

    logger.info("Checking site: {0}".format(site))
    r = requests.get(site.url)

    # add response time to time-series
    site.add_time(r.elapsed.total_seconds())
    
    logger.info(r.elapsed.total_seconds())
    logger.info(r.headers['content-type'])
    logger.info(r.encoding)
    logger.info(r.url)
    logger.info(site.content_str in r.text)
    t = threading.Timer(repeat_rate, check_site, [site])
    # set the daemon flag to exit the application, once the main
    # process stops
    t.daemon=True
    t.start()

def dump_sites():
    global sites
    models.pickle_to_file(sites)
    return

def main():
    atexit.register(dump_sites)
    #stop_flag = []
    #thread = threading.Thread(target=input_thread, args=(stop_flag,))
    #thread.start()
    #print("Processing {0} sites".format(len(sites['Sites'])))
    global repeat_rate
    global sites

    for site in sites:
        threading.Thread(target=check_site, args=(site,), daemon=True).start()

    input()

if __name__ == '__main__':

    main()
