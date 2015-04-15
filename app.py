import threading, time
import yaml
import requests
from getchar import getch

sites = yaml.load(open('config.yml', 'r'))
repeat_rate = 2 # How often will a site be 'pinged'

def input_thread(stop_flag):
    print("Press a key to quit...")
    input()
    stop_flag.append(None)
    return

def check_site(site):
    ''' This function pings the site['url'] and attempts
        to find site['content']. It will run every x secs
        in a thread '''

    print("Checking site:", site)
    r = requests.get(site['url'])
    print(r.elapsed.total_seconds())
    print(r.headers['content-type'])
    print(r.encoding)
    print(r.url)
    print(site['content'] in r.text)
    t = threading.Timer(repeat_rate, check_site, [site])
    # set the daemon flag to exit the application, once the main
    # process stops
    t.daemon=True
    t.start()

def main():
    #stop_flag = []
    #thread = threading.Thread(target=input_thread, args=(stop_flag,))
    #thread.start()
    print("Processing {0} sites".format(len(sites['Sites'])))
    global repeat_rate 
    repeat_rate = 5
    for site in sites['Sites']:
        threading.Thread(target=check_site, args=(site,), daemon=True).start()

    input()

if __name__ == '__main__':

    main()
