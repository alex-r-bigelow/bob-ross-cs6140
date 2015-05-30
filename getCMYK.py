#!/usr/bin/env python
'''
This script extracts all the CMYK paint colors in Bob Ross's available sets on art-paints.com

Some colors are listed more than once (in different sets), and actually are listed with different
values; to handle this, the script averages each channel if there is more than one listing with
the same name.
'''


import requests, re

colorNames = {
	"Floral" : [
	"Alizarin Crimson",
	"Cadmium Red Medium",
	"Cadmium Red Light",
	"Cadmium Orange",
	"Cadmium Yellow Light",
	"Sap Green",
	"Viridian Green",
	"Turquoise",
	"Ultramarine Blue",
	"Flower Pink",
	"Dusty Rose",
	"Magenta",
	"Ivory Black",
	"Mauve",
	"Titanium White",
	"Warm White"
	],
	"Landscape" : [
	"Alizarin Crimson",
	"Bright Red",
	"Yellow Ochre",
	"Cadmium Yellow Hue",
	"Indian Yellow",
	"Phthalo Green",
	"Sap Green",
	"Phthalo Blue",
	"Prussian Blue",
	"Dark Sienna",
	"Van Dyke Brown",
	"Midnight Black",
	"Mountain Mixture",
	"Titanium White"
	],
	"Master" : [
	"Alizarin Crimson",
	"Bright Red",
	"Cadmium Yellow",
	"Sap Green",
	"Phthalo Blue",
	"Van Dyke Brown",
	"Midnight Black",
	"Titanium White"
	],
	"Soft" : [
	"Cadmium Red Light",
	"Cadmium Red Medium",
	"Cadmium Orange",
	"Indian Yellow",
	"Yellow Ochre",
	"Cadmium Yellow Light",
	"Sap Green",
	"Viridian Green",
	"Ultramarine Blue",
	"Ivory Black",
	"Alizarin Crimson",
	"Burnt Sienna",
	"Burnt Umber",
	"Mauve",
	"Magenta",
	"Flower Pink",
	"Dusty Rose",
	"Transparent Black",
	"Raw Umber",
	"Warm White",
	"Titanium White"
	],
	"Wildlife" : [
	"Yellow Ochre",
	"Indian Yellow",
	"Transparent Black",
	"Burnt Umber",
	"Raw Umber",
	"Burnt Sienna",
	"Warm White"
	]
}

results = {}

cmykPattern = re.compile('\d+, \d+, \d+, \d+')
for setName,paints in colorNames.iteritems():
	for p in paints:
		p = '-'.join(p.split())
		page = requests.get("http://www.art-paints.com/Paints/Oil/Bob-Ross/" + setName + "/" + p + "/" + p + ".html")
		if page.ok:
			values = cmykPattern.findall(page.content)
			if len(values) == 1:
				values = values[0].split(', ')
				print p, values
				if not results.has_key(p):
					results[p] = dict(zip(['c','m','y','k'],values))
					results[p]['count'] = 1
				else:
					for i,c in enumerate(['c','m','y','k']):
						results[p][c] = float(results[p][c]) + float(values[i])
					results[p]['count'] += 1
			else:
				print 'empty result for', setName, p, values
		else:
			print 'no page for', setName, p

outfile = open('bobRossColors.csv','wb')
outfile.write('color,c,m,y,k\n')

for p,v in results.iteritems():
	outfile.write(p + ',')
	for c in ['c','m','y','k']:
		v[c] = float(v[c]) / float(100 * v['count'])
		outfile.write(str(v[c]))
		if c != 'k':
			outfile.write(',')
		else:
			outfile.write('\n')
outfile.close()