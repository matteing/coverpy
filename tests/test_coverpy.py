import unittest
import coverpy
import httpretty
import os
import requests

class TestCoverpy(unittest.TestCase):
	def setUp(self):
		self.coverpy = coverpy.CoverPy()
		# Set up paths...
		self.ok_computer = os.path.join(os.path.dirname(__file__), 'mocks/OKComputer.json')
		self.sugar = os.path.join(os.path.dirname(__file__), 'mocks/Maroon5Sugar.json')
		self.no_kind = os.path.join(os.path.dirname(__file__), 'mocks/SugarNoKindType.json')
		self.empty_response = os.path.join(os.path.dirname(__file__), 'mocks/SuchFakeAlbumPls.json')

	@httpretty.activate
	def test_get_cover_parse_album_result(self):
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
	def test_get_cover_parse_song_result(self):
		# Maroon 5 Sugar Response
		httpretty.register_uri(httpretty.GET, 
					"https://itunes.apple.com/search/?limit=1&entity=musicArtist%2CmusicTrack%2Calbum%2Cmix%2Csong&term=Sugar Maroon 5&media=music",
					body=open(self.sugar).read(),
					content_type="application/json")

		# Request the content from the mock
		result = self.coverpy.get_cover("Sugar Maroon 5")

		# Begin assertions
		self.assertEquals(result.name, "Sugar")
		self.assertEquals(result.type, "song")

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

	@httpretty.activate
	def test_get_cover_unknown_kind(self):
		# No results response
		httpretty.register_uri(httpretty.GET,
					"https://itunes.apple.com/search/?limit=1&entity=musicArtist%2CmusicTrack%2Calbum%2Cmix%2Csong&term=Sugar&media=music",
					body=open(self.no_kind).read(),
					content_type="application/json")

		# Assert if type is returned unknown
		result = self.coverpy.get_cover("Sugar")
		self.assertEquals(result.type, 'unknown')

	@httpretty.activate
	def test_for_http_status(self):
		# Test for a 500 Internal Server Error
		httpretty.register_uri(httpretty.GET, 
					"https://itunes.apple.com/search/?limit=1&entity=musicArtist%2CmusicTrack%2Calbum%2Cmix%2Csong&term=OK+Computer&media=music",
					body="501 Internal Server Error",
					status=500)

		with self.assertRaises(requests.exceptions.HTTPError):
			self.coverpy.get_cover("OK Computer")
		
	@httpretty.activate
	def test_result_artwork_generator(self):
		# OK Computer response
		httpretty.register_uri(httpretty.GET, 
					"https://itunes.apple.com/search/?limit=1&entity=musicArtist%2CmusicTrack%2Calbum%2Cmix%2Csong&term=OK+Computer&media=music",
					body=open(self.ok_computer).read(),
					content_type="application/json")

		# Request the content from the mock
		result = self.coverpy.get_cover("OK Computer")

		# Begin assertions
		self.assertTrue("600x600" in result.artwork(600))

if __name__ == '__main__':
    unittest.main()