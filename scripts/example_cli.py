import coverpy

print("CoverPy console:")
c = coverpy.CoverPy()
while True:
	i = input("> ")
	if i == 'exit':
		exit()

	try:
		query = c.get_cover(i)
		print("Name: %s" % query.name)
		print("EntityType: %s" % query.type)
		print("Artist: %s" % query.artist)
		print("Album: %s" % query.album)
		print(query.artwork())
		print("QueryUrl: %s" % query.url)
	except coverpy.exceptions.NoResultsException as e:
		print("Nothing found.")