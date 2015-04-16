
Pingdom-like webapp and uptime checker
--------------------------------------

Author: Miguel Ferreira
Date: 15-04-2015

Requirements:
  - Python 3.4
  - python3.4-dev (Ubuntu package name, header files for compiling libyaml)

Installation:
  - checkout this repo
  - create a virtualenv with Python34 (optional)
  - pip install -r requirements.txt (make sure you're installing with right python version)
  - start with: python app.py

Design considerations:

  - Plot using google charts, only plots last 200 samples, so the plots converge to the same time period, and also limit the extent of the plots.
  - Pickling/unpicking site object data to disk to achieve data persistence (solutions requiring a database or cache where not considered due to added complexity). This is done at application exit but also periodically in a separate thread.
  - Threads are daemonized so as soon as user CTRL+Cs to exit all threads terminate
  - If connection fails to a site, retry after a longer period of time (e.g. 10x check rate). The url could be bad but there's also a possibility of intermittent failures, so we shouldn't stop checking the url.

Issues:

  - On some sites, the requests library detects wrong encoding type (if not in headers) and seems not to match strings correctly
  - Possible issue, as checks progress and application runs, the whole site data including response times is kept in memory, this may lead to memory growing out of bounds for long running instances, or when the cache on disk is already large - a method should be considered to dump memory to disk, at the moment it keeps both in disk and in system memory

