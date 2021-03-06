import urllib2, json, re, sys, locale, datetime
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse, parse_qs
try:
	from bs4 import BeautifulSoup
except ImportError:
	import pip
	pip.main(['install', 'beautifulsoup4'])
	from bs4 import BeautifulSoup

#sudo apt-get install language-pack-pt-base -y && sudo locale-gen pt_BR pt_BR.UTF-8 && sudo dpkg-reconfigure locales
locale.setlocale(locale.LC_ALL, 'pt_BR')

def find_between(s, first, last):
	try:
		start = s.index(first) + len(first)
		end = s.index(last, start)
		return s[start:end]
	except ValueError:
		return ""

def format_stars(value):
	return int(value.lstrip()[1:].rstrip().lstrip().replace('.',''))

def get_num(x):
	return int(''.join(ele for ele in x if ele.isdigit()))

class Handler(BaseHTTPRequestHandler):

	def do_GET(self):
		now = datetime.datetime.now()
		query_components = parse_qs(urlparse(self.path).query)
		json_out = {}
		self.send_response(200)
		self.send_header('Access-Control-Allow-Headers', '*')
		self.send_header('Access-Control-Allow-Origin', '*')
		self.send_header('Access-Control-Allow-Methods', 'GET')
		self.send_header("Content-type", "application/json")
		self.end_headers()

		print query_components['app'][0]
		headers = { "Accept-Language" : "pt_BR" }
		req = urllib2.Request(query_components['app'][0], None, headers)
		response = urllib2.urlopen(req)
		encoding = response.headers['content-type'].split('charset=')[1]
		html = response.read()

		content = unicode(html, encoding)

		soup = BeautifulSoup(content, 'html.parser')

		date_scraped	= soup.find('div', {'itemprop': 'datePublished'}).text
		datePublished	= datetime.datetime.strptime(date_scraped, '%d de %B de %Y').isoformat()
		try:
			fileSize 	= soup.find('div', {'itemprop': 'fileSize'}).text.rstrip().lstrip()
		except:
			fileSize	= None
		numDownloads 	= soup.find('div', {'itemprop': 'numDownloads'}).text.split('-')
		appName 		= soup.select(".document-title")[0].text.rstrip().lstrip()
		offered_by 		= soup.select('.document-subtitle.primary span')[0].text

		devInfo = soup.find('div', {'class': 'content contains-text-link'})

		try:
			site = [find_between(str(result.attrs['href']), '?q=', '&sa=D') for result in soup.findAll('a', href=True, text=re.compile('Acesse o site'))][0]
		except IndexError:
			site = ''

		email = re.search('(?=mailto:).*?(?=")', str(devInfo)).group(0).replace('mailto:', '')

		try:
			score_total = float(soup.select(".score")[0].text.replace(',', '.'))

			one_star 	= format_stars(soup.select("div.rating-bar-container.one")[0].text)
			two_stars 	= format_stars(soup.select("div.rating-bar-container.two")[0].text)
			three_stars = format_stars(soup.select("div.rating-bar-container.three")[0].text)
			four_stars 	= format_stars(soup.select("div.rating-bar-container.four")[0].text)
			five_stars 	= format_stars(soup.select("div.rating-bar-container.five")[0].text)
			sum_stars 	= one_star+two_stars+three_stars+four_stars+five_stars
		except:
			score_total = 0

			one_star 	= 0
			two_stars 	= 0
			three_stars = 0
			four_stars 	= 0
			five_stars 	= 0
			sum_stars 	= one_star+two_stars+three_stars+four_stars+five_stars

		app_info = {'AppName': appName,
					'url': query_components['app'][0],
					'datePublished': datePublished,
					'fileSize': fileSize,
					'numDownloads': [int(numDownloads[0].rstrip().lstrip().replace('.','')), int(numDownloads[1].rstrip().lstrip().replace('.',''))],
					'devInfo': {'author': offered_by,'site': site, 'email': email},
					'reviews': {'scores': {
											'1_star': one_star,
											'2_stars': two_stars,
											'3_stars': three_stars,
											'4_stars': four_stars,
											'5_stars': five_stars,
											'total': score_total,
											'ratingCount': sum_stars
											}, 'comments': [] }
					}

		for review in soup.findAll('div', {'class': 'single-review'}):
			author 		= review.find('span', {'class': 'author-name'}).text.rstrip().lstrip()
			authorId 	= find_between(str(review.find('span', {'class': 'author-name'})), '?id=', '"')
			authorStars = get_num(review.find('div', {'class': 'review-info-star-rating'}).find('div', {'class': 'tiny-star star-rating-non-editable-container'}).get('aria-label'))
			date 		= datetime.datetime.strptime(review.find('span', {'class': 'review-date'}).text, '%d de %B de %Y').isoformat()
			message 	= review.find('div', {'class': 'review-body'}).text.replace('Resenha completa', '').rstrip().lstrip()
			app_info['reviews']['comments'].append({'author': author, 'authorId': authorId, 'authorStars': authorStars, 'date': date, 'message': message})

		# print json.dumps(app_info, indent=4), quit()

# 		json.dump(app_info, open('apps_info_json/%s.json' % ''.join(l for l in re.findall('([A-Za-z])' ,appName)), 'w'))

		self.wfile.write(json.dumps(app_info))
		return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass

if __name__ == '__main__':
	server = ThreadedHTTPServer(('', 8081), Handler)
	print 'Starting server, use <Ctrl-C> to stop'
	server.serve_forever()