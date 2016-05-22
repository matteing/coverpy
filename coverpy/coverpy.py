import os
import requests
from . import exceptions

class Result:
	def __init__(self, item):
		self.artworkThumb = item['artworkUrl100']
		self.artist = item['artistName']
		self.album = item['collectionName']
		self.url = item['url']

		# Take some measures to detect whether it is a song or album
		if 'kind' in item:
			self.type = item['kind'].lower()
		elif 'wrapperType' in item:
			if item['wrapperType'].lower() == 'track':
				self.type = 'song'
			elif item['wrapperType'].lower() == 'collection':
				self.type = 'album'
		elif 'collectionType' in item:
			self.type = 'album'
		else:
			# Assuming edge case of the API
			self.type = 'unknown'

		if self.type == 'song':
			self.name = item['trackName']
		elif self.type == 'album':
			self.name = item['collectionName']
		else:
			self.name = 'unknown'

	def artwork(self, size = 625):
		# Replace size because API doesn't hand links to full res. It only gives 60x60 and 100x100.
		# However, I found a way to circumvent it.
		return self.artworkThumb.replace('100x100bb', "%sx%s" % (size, size))

class CoverPy: 
	def __init__(self):
		self.base_url = "https://itunes.apple.com/search/"

	def _get(self, payload, override = False, entities = False):
		if override:
			data = requests.get("%s%s" % (self.base_url, override))
		else:
			payload['entity'] = "musicArtist,musicTrack,album,mix,song"
			payload['media'] = 'music'
			data = requests.get(self.base_url, params = payload)

		if data.status_code != 200:
			raise requests.HTTPError
		else:
			return data

	def _search(self, term, limit = 1):
		payload = {
			'term': term,
			'limit': limit
		}

		req = self._get(payload)
		return req

	def get_cover(self, term, limit = 1, debug = False):
		search = self._search(term, limit)
		parsed = search.json()

		if parsed['resultCount'] == 0:
			raise exceptions.NoResultsException

		result = parsed['results'][0]
		result['url'] = search.url

		return Result(result)
