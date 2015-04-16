import models
import unittest
import logging

# disable logging from app and modules
logging.disable(logging.CRITICAL)

class TestSiteModel(unittest.TestCase):
  ''' Check that sites with same url are considered equal '''

  site1 = models.Site(url='www.url.com', content_str='anything')
  site2 = models.Site(url='www.url.com', content_str='anotheranything')
  site3 = models.Site(url='www.url2.com', content_str='anotheranything')
  
  def test_equal_urls(self):

    self.assertEqual(self.site1, self.site2)

  def test_different_urls(self):
    
    self.assertNotEqual(self.site1, self.site3)

  def test_add_response_time(self):
    
     self.assertEqual(self.site1.resp_time, [])
     self.site1.add_time(1.0)
     self.assertEqual(self.site1.resp_time.pop()[1], 1.0)
     
  def test_must_be_a_float(self):
     with self.assertRaises(TypeError):
       self.site1.add_time(1)
     with self.assertRaises(TypeError):
       self.site1.add_time('string')
     self.assertEqual(self.site1.resp_time, [])

class TestDumpingToDisk(unittest.TestCase):
  
  site1 = models.Site(url='www.url.com', content_str='anything')
  site2 = models.Site(url='www.url.com', content_str='anotheranything')

  def test_dumping_to_disk(self):
    pass
  

if __name__ == '__main__':

  unittest.main()

