import app
import models
import unittest

class TestSiteChecking(unittest.TestCase):

  def setUp(self):
    self.site1 = models.Site(url='http://www.publico.pt', content_str='CLASSIFICADOS')

  def test_check_site_resp_times(self):
    self.assertEqual(self.site1.resp_time, [])
    app.check_site(self.site1, 10, 9)
    self.assertEqual(len(self.site1.resp_time), 1)
    self.site1.url='www.publico.pt' # remove schema (http)
    app.check_site(self.site1, 10, 9)
    # no new data point (no schema)
    self.assertEqual(len(self.site1.resp_time), 1)
    self.site1.url='http://www.publico.pt'
    app.check_site(self.site1, 10, 9)
    # new data point
    self.assertEqual(len(self.site1.resp_time), 2)
    app.check_site(self.site1, 10, 0.0001)
    # no new data point (timed out)
    self.assertEqual(len(self.site1.resp_time), 2)

  def test_check_http_code_and_encoding(self):
    app.check_site(self.site1, 10, 9)
    self.assertEqual(self.site1.last_http_code, 200)
    self.assertTrue(self.site1.string_matched)
    self.site1.content_str="SOMETHINGWEIRD"
    app.check_site(self.site1, 10, 9)
    self.assertFalse(self.site1.string_matched)
    self.assertEqual(self.site1.encoding.lower(), "utf-8")

  def test_check_wrong_site(self):
    self.site1.url='http://totallybadsite.not.good.com'
    self.site1.content_str='somestring'
    app.check_site(self.site1, 10, 9)
    self.assertListEqual(self.site1.resp_time, [])
    self.assertFalse(self.site1.string_matched)
    self.assertIsNone(self.site1.last_http_code)

  def test_good_site_wrong_content(self):
    self.site1.url='http://www.f-secure.com'
    self.site1.content_str='this is google'
    app.check_site(self.site1, 10, 9)
    self.assertEqual(self.site1.last_http_code, 200)
    self.assertFalse(self.site1.string_matched)
    self.site1.content_str='fsecure'
    app.check_site(self.site1, 10, 9)
    self.assertTrue(self.site1.string_matched)
