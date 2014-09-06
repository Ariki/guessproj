#!python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import os
import subprocess
import unittest

import guessproj

class TestFunctions(unittest.TestCase):

    def setUp(self):
        """Setup test case"""

    def test_to_str(self):
        """Test to_str() function"""
        self.assertIsNone(guessproj.to_str(None))
        self.assertTrue(isinstance(guessproj.to_str(b'+lon_0=39.0'), str))
        self.assertTrue(isinstance(guessproj.to_str(u'+lon_0=39.0'), str))
        self.assertRaises(ValueError, lambda: guessproj.to_str(True))

    def test_parse_coord(self):
        """Test parse_coord() function"""
        self.assertEqual(guessproj.parse_coord(u'12.15'), 12.15)
        self.assertEqual(guessproj.parse_coord(b'12.15'), 12.15)
        self.assertEqual(guessproj.parse_coord(u'-13'), -13)
        self.assertEqual(guessproj.parse_coord(b'-13'), -13)
        self.assertEqual(guessproj.parse_coord(u'56,25'), 56.25)
        self.assertEqual(guessproj.parse_coord(b'56,25'), 56.25)

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


if __name__ == '__main__':
    unittest.main()
    
