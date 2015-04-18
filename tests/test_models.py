import models
import unittest
import os
import io
import yaml

class TestSiteModel(unittest.TestCase):
  ''' Check that sites with same url are considered equal '''

  def setUp(self):
    self.site1 = models.Site(url='www.url.com', content_str='anything')
    self.site2 = models.Site(url='www.url.com', content_str='anotheranything')
    self.site3 = models.Site(url='www.url2.com', content_str='anotheranything')

  def test_equal_urls(self):

    self.assertEqual(self.site1, self.site2)

  def test_different_urls(self):

    self.assertNotEqual(self.site1, self.site3)

  def test_add_response_time(self):

     self.assertEqual(self.site1.resp_time, [])
     self.site1.add_time(1.0) # will be converted to ms
     self.assertEqual(self.site1.resp_time.pop()[1], 1000.0)

  def test_must_be_a_float(self):

     with self.assertRaises(TypeError):
       self.site1.add_time(1)
     with self.assertRaises(TypeError):
       self.site1.add_time('string')
     self.assertEqual(self.site1.resp_time, [])

  def test_dump_site_to_html(self):
     self.site1.url = "http://www.publico.pt"
     self.site1.dump_site_for_inspection()
     assertTrue(os.path.exists(os.path.abspath('publico.html')))

class TestSitePersistence(unittest.TestCase):

  site1 = models.Site(url='www.url.com', content_str='anything')
  site2 = models.Site(url='www.url2.com', content_str='anotheranything')

  def setUp(self):
      site1 = models.Site(url='www.url.com', content_str='anything')
      site2 = models.Site(url='www.url2.com', content_str='anotheranything')
      models.SAVED_SITES_FILE=('test.pkl')
      try:
          os.remove(models.SAVED_SITES_FILE)
      except:
          pass
      self.assertFalse(os.path.exists(os.path.abspath('test.pkl')))

  def test_dumping_to_disk(self):

      models.dump_sites([self.site1, self.site2])
      self.assertTrue(os.path.exists(os.path.abspath('test.pkl')))
      os.remove(os.path.abspath('test.pkl'))

  def test_loading_from_disk(self):
      models.dump_sites([self.site1, self.site2])
      self.site1.url='www.newurl.com'
      models_file=models.get_pickled_sites()
      self.assertNotIn(self.site1, models_file)
      self.site1.url='www.url.com'
      self.assertIn(self.site1, models_file)

class TestConfigFileLoad(unittest.TestCase):

  def setUp(self):
    self.cfg_file_str = "refresh_rate: 10\n"\
      "sites:\n"\
      "  - url: https://www.publico.pt\n"\
      "    content: CLASSIFICADOS\n"\
      "  - url: https://www.publico.pt\n"\
      "    content: NOTINPAGE\n"\
      "  - url: https://www.anotherurl.com\n"\
      "    content: content\n"
    self.config = yaml.load(self.cfg_file_str)

  def test_config_loading(self):
   self.assertEqual(self.config['sites'][0],
     {'url': 'https://www.publico.pt', 'content': 'CLASSIFICADOS'})

  def test_no_duplicates(self):
    sites = models.get_sites(self.config['sites'])
    # excludes middle entry
    self.assertEqual(len(sites), 2)
    self.assertEqual(sites[0].content_str, 'CLASSIFICADOS')
    self.assertEqual(sites[0].url, 'https://www.publico.pt')
    self.assertEqual(sites[1].url, 'https://www.anotherurl.com')

if __name__ == '__main__':

  unittest.main()
