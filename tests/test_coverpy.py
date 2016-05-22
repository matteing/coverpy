import unittest
import coverpy
import httpretty
import os

class TestCoverpy(unittest.TestCase):
	def setUp(self):
		self.coverpy = coverpy.CoverPy()
		# Set up paths...
		self.ok_computer = os.path.join(os.path.dirname(__file__), 'mocks/OKComputer.json')
		self.empty_response = os.path.join(os.path.dirname(__file__), 'mocks/SuchFakeAlbumPls.json')

	@httpretty.activate
	def test_get_cover_parse_result(self):
		# OK Computer response
		httpretty.register_uri(httpretty.GET, 
					"https://itunes.apple.com/search/?limit=1&entity=musicArtist%2CmusicTrack%2Calbum%2Cmix%2Csong&term=OK+Computer&media=music",
					body=open(self.ok_computer).read(),
					content_type="application/json")

		# Request the content from the mock
		result = self.coverpy.get_cover("OK Computer")

		# Begin assertions
		self.assertEquals(result.name, "OK Computer")
		self.assertEquals(result.type, "album")

	@httpretty.activate
	def test_get_cover_no_results(self):
		# No results response
		httpretty.register_uri(httpretty.GET,
					"https://itunes.apple.com/search/?limit=1&entity=musicArtist%2CmusicTrack%2Calbum%2Cmix%2Csong&term=Such+Fake+Album+Pls&media=music",
					body=open(self.empty_response).read(),
					content_type="application/json")

		# Assert a NoResultsException
		with self.assertRaises(coverpy.exceptions.NoResultsException):
			self.coverpy.get_cover("Such Fake Album Pls")
		
if __name__ == '__main__':
    unittest.main()