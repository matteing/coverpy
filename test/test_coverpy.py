import unittest
import coverpy

class TestCoverPy(unittest.TestCase):
	def setUp(self):
		self.coverpy = coverpy.CoverPy()
	def test_get_cover(self):
		""" Test retrieving a sample cover, OK Computer by Radiohead. """
		result = self.coverpy.get_cover("OK Computer")
		# Test if result is returned correctly.
		self.assertEqual(result.album, 'OK Computer')
		self.assertEqual(result.artist, 'Radiohead')

if __name__ == '__main__':
    unittest.main()
