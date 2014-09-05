#!python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import os
import subprocess
import unittest


class TestFourPoints(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.abspath(os.path.split(__file__)[0])
        self.input_file = os.path.join(self.test_dir, 'testpoints.txt')
        self.script_dir = os.path.split(self.test_dir)[0]
        self.script_path = os.path.join(self.script_dir, 'guessproj.py')

    def test_help(self):
        """Tests short help message"""
        cmd = 'python "{0}" --help'.format(self.script_path)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, err = p.communicate()
        exit_code = p.wait()
        self.assertEqual(exit_code, 0)
        self.assertFalse(err)
        self.assertIn('Usage', output.decode('utf-8'))

    def test_proj(self):
        """Tests projstring output"""
        cmd = ('python "{0}" --proj +to +proj=tmerc +ellps=krass '
               '+lat_0=0 +lon_0=39 +x_0~0 +y_0~0 +no_defs '
               ' "{1}"'.format(
                   self.script_path, self.input_file))
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, err = p.communicate()
        exit_code = p.wait()
        self.assertEqual(exit_code, 0)
        self.assertFalse(err)
        splitted = output.decode('utf-8').split()
        params = dict((p.split('=') + [None])[:2] for p in splitted)
        self.assertEqual(params['+proj'], 'tmerc')
        self.assertEqual(params['+ellps'], 'krass')
        self.assertIsNone(params['+no_defs'])
        self.assertAlmostEqual(float(params['+lat_0']), 0, places=8)
        self.assertAlmostEqual(float(params['+lon_0']), 39, places=8)
        self.assertAlmostEqual(float(params['+x_0']), 3e5, places=2)
        self.assertAlmostEqual(float(params['+y_0']), -5e6, places=2)


if __name__ == '__main__':
    unittest.main()
    
