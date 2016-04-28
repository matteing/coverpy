import coverpy

print "CoverPy console:"
c = main.CoverPy()
while True:
	i = raw_input("> ")
	if i == 'exit':
		exit()

	try:
		query = c.get_cover(i)
		print "Name: %s" % query.name
		print "EntityType: %s" % query.type
		print "Artist: %s" % query.artist
		print "Album: %s" % query.album
		print query.artwork()
		print "QueryUrl: %s" % query.url
	except main.NoResultsError as e:
		print "Nothing found."
