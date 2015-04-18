#Pingdom-like webapp and uptime checker

Author: Miguel Ferreira  
Date: 15-04-2015

##Requirements:

  - Python >=3
  - python3-dev (Ubuntu package name, header files for compiling libyaml)

##Installation:

  - checkout this repo
  - create a virtualenv with Python34 (optional)
  - install package requirements (make sure you're using right Python version)
```sh
      pip install -r requirements.txt
```
  - start with:
```sh
      python app.py [-r check_rate] [-l LOGLEVEL] [--nohistory]
```

## Running from docker

If you have docker installed, you can run this application simply by running the following commands:
```sh
  (sudo) docker build -t pingdom_clone .
  (sudo) docker run -d -p 8080:8080 pingdom_clone
```
And visit:
http://localhost:8080/

If you want to change command-line parameters for the application, you can either change the CMD parameter in the Dockerfile, or run (example):
```sh
  docker run -d -p 8080:8080 pingdom_clone python app.py -r 1 --nohistory -l DEBUG
```

## Testing

All tests are in the tests/ folder and use Python's standard unittest module.
To find all the tests and run them, simply run from the project top folder:
```sh
  python tests.py
```

## Design considerations

  - Plot using google charts, only plots last 200 samples, to limit the extent of the plots.
  - Check rate is in full seconds, minimum is 1s check rate.
  - Pickling/unpicking site object data to disk to achieve data persistence. This is done at application exit but also periodically in a separate thread.
  - Threads are daemonized so as soon as user breaks with CTRL+Cs all threads terminate
  - If connection fails to a site, retry after a longer period of time (e.g. 10x check rate). The url could be bad but there's also a possibility of intermittent failures, so we shouldn't stop checking the url.
  - Check results are logged with a rotating file handler to prevent size of file in disk to grow out of bounds.

### Distributed checks

  - Content might be different when accessing from different regions
  - Centralized data repository (database) used to synchronize the times from every checking server
  - Separate web server from check loops.
  - Sync site data across time-zones.
  - Use encrypted SSL connections to database make sure data is not tampered with

## Known Issues:

  - This app launches one thread per site which can quickly overwhelm a less powerful system for hundreds of monitored sites. To prevent this, we should use a ThreadPool, or a list of 'workers' running in separate threads and listening from a queue.
  - On some sites, the requests library detects wrong encoding type (if not in headers) and seems not to match strings correctly
  - As checks progress and application runs, the whole site data including response times are kept in memory which  may lead to memory growing out of bounds for long running instances with many checks.

## License

The source code in this repo is distributed under the MIT License.
