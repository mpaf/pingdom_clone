import unittest
import tests
from tests import *
import logging

# disable logging from app and modules
logging.disable(logging.CRITICAL)

if __name__ == '__main__':

  testloader = unittest.TestLoader()
  suite=testloader.discover('tests')
  testrunner = unittest.TextTestRunner(verbosity=3)
  testrunner.run(suite)
