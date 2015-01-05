#!python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import os
import subprocess
try:
    import unittest2 as unittest
except:
    import unittest

import guessproj

class TestFunctions(unittest.TestCase):

    def setUp(self):
        """Setup test case"""

    def test_to_str(self):
        """to_str() function converts byte or Unicode string to str type"""
        self.assertIsNone(guessproj.to_str(None))
        self.assertIsInstance(guessproj.to_str(b'+lon_0=39.0'), str)
        self.assertIsInstance(guessproj.to_str(u'+lon_0=39.0'), str)
        self.assertIsInstance(
            guessproj.to_str(b'\xef', encoding='cp1251'), str)
        self.assertIsInstance(
            guessproj.to_str(u'\u043f', encoding='cp1251'), str)
        self.assertEqual(
            guessproj.to_str(u'\u043f', encoding='cp1251'),
            guessproj.to_str(b'\xef', encoding='cp1251')
            )
        self.assertRaises(ValueError, lambda: guessproj.to_str(True))
        
    def test_to_unicode(self):
        """to_unicode() function converts byte or Unicode string to Unicode"""
        utype = type(u'a')
        self.assertIsNone(guessproj.to_unicode(None))
        self.assertIsInstance(guessproj.to_unicode(b'+lon_0=39.0'), utype)
        self.assertIsInstance(guessproj.to_unicode(u'+lon_0=39.0'), utype)
        self.assertIsInstance(
            guessproj.to_unicode(b'\xef', encoding='cp1251'), utype)
        self.assertIsInstance(
            guessproj.to_unicode(u'\u043f', encoding='cp1251'), utype)
        self.assertEqual(
            guessproj.to_unicode(u'\u043f', encoding='cp1251'),
            guessproj.to_unicode(b'\xef', encoding='cp1251')
            )
        self.assertRaises(ValueError, lambda: guessproj.to_unicode(True))
        
    def test_parse_coord(self):
        """Test parse_coord() function"""
        self.assertEqual(guessproj.parse_coord(u'12.15'), 12.15)
        self.assertEqual(guessproj.parse_coord(b'12.15'), 12.15)
        self.assertEqual(guessproj.parse_coord(u'-13'), -13)
        self.assertEqual(guessproj.parse_coord(b'-13'), -13)
        self.assertEqual(guessproj.parse_coord(u'56,25'), 56.25)
        self.assertEqual(guessproj.parse_coord(b'56,25'), 56.25)
        self.assertEqual(guessproj.parse_coord(b'0'), 0)
        self.assertEqual(guessproj.parse_coord(u'150d7\'30"'), 150.125)
        self.assertEqual(guessproj.parse_coord(u'+150d7\'30"'), 150.125)
        self.assertEqual(guessproj.parse_coord(u'-150d7\'30"'), -150.125)
        self.assertEqual(guessproj.parse_coord(u'-0d'), 0)
        self.assertEqual(guessproj.parse_coord(u'-7\'30"'), -0.125)
        self.assertEqual(guessproj.parse_coord(u'-30"'), -1 / 120.0)
        self.assertEqual(guessproj.parse_coord(b'-123,456d'), -123.456)
        self.assertEqual(guessproj.parse_coord(b'+175d07.5\''), 175.125)
        self.assertEqual(guessproj.parse_coord(b'-7,5\''), -0.125)
        self.assertRaises(TypeError, lambda: guessproj.parse_coord(None))
        self.assertRaises(ValueError, lambda: guessproj.parse_coord(u''))
        self.assertRaises(ValueError, lambda: guessproj.parse_coord(u'1d2m3s'))
        self.assertRaises(ValueError, lambda: guessproj.parse_coord(u'-'))
        self.assertRaises(ValueError, lambda: guessproj.parse_coord(u'--2d'))
        self.assertRaises(ValueError, lambda: guessproj.parse_coord(u'6-1'))
        self.assertRaises(
            ValueError, lambda: guessproj.parse_coord(b'1d60\'0"'))
        self.assertRaises(
            ValueError, lambda: guessproj.parse_coord(b'-140d09\'60.5"'))

    def test_read_points(self):
        """Test read_points() function"""
        # TODO: Implement test that covers all features
        filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'four_points.txt'
            )
        points = guessproj.read_points(filename, 'cp1251')
        self.assertEqual(len(points), 4)
        pt0 = points[0]
        self.assertEqual(len(pt0), 3)
        pair1, pair2, name = pt0
        self.assertEqual(len(pair1), 2)
        self.assertEqual(len(pair2), 2)
        self.assertAlmostEqual(pair1[0], 39, places=8)
        self.assertAlmostEqual(pair1[1], 47, places=8)
        self.assertAlmostEqual(pair2[0], 3e5, places=3)
        self.assertAlmostEqual(pair2[1], 207338.73, places=3)
        self.assertEqual(name, 'pt1')

    def test_refine_projstring(self):
        """refine_projstring(projstring) returns normalized projstring"""
        self.assertTrue(guessproj.osr)
        test_data = [
            ('+proj=longlat +no_defs',
             '+proj=longlat +ellps=WGS84 +no_defs'),
            # It is strange that osr.SpatialReference replaces +k_0 with +k
            ('+k_0=0.9996 +proj=tmerc +lon_0=39 +no_defs',
             '+proj=tmerc +lat_0=0 +lon_0=39 +k=0.9996 +x_0=0 +y_0=0 '
             '+ellps=WGS84 +units=m +no_defs'),
            ]
        for orig, ctrl in test_data:
            refined = guessproj.refine_projstring(orig).strip()
            self.assertEqual(refined, ctrl)
            
    def test_find_residuals(self):
        """find_residuals() transforms the points and calculates residuals"""
        src_proj = '+proj=longlat +ellps=WGS84 +no_defs'
        tgt_proj = '+proj=tmerc +ellps=krass +lon_0=39 +x_0=3e5 +y_0=-5e6'
        filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'four_points.txt')
        points = guessproj.read_points(filename, 'cp1251')
        residuals = guessproj.find_residuals(src_proj, tgt_proj, points)
        self.assertEqual(len(residuals), 4)
        for p in residuals:
            self.assertEqual(len(p), 2)
            for r in p:
                self.assertLess(abs(r), 0.01)


if __name__ == '__main__':
    unittest.main()
    
