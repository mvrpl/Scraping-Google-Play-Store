import urllib2, json, re, sys, os
from bs4 import BeautifulSoup

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


urls = open( "urls.txt", "r" )
lines = []
for line in urls:
    lines.append(line.replace("\n", ''))

for url in lines:
    file_name = url.split("id=")[1].replace(".", "-")
    if os.path.isfile("apps_info_json/%s.json" % file_name) == False:
        print("generating %s.json" % file_name)
        try:
            response = urllib2.urlopen(url)
        except:
            response = False
        if response != False:
            html = response.read()

            soup = BeautifulSoup(html, 'html.parser')

            datePublished 	= soup.find('div', {'itemprop': 'datePublished'}).text
            try:
                fileSize 	= soup.find('div', {'itemprop': 'fileSize'}).text.rstrip().lstrip()
            except:
                fileSize	= ''
            numDownloads 	= soup.find('div', {'itemprop': 'numDownloads'}).text.split('-')
            appName 		= soup.select(".document-title")[0].text.rstrip().lstrip()
            category        = soup.find('span', {'itemprop': 'genre'}).text
            offered_by 		= soup.find('div', text='Oferecido por').findNext('div').text

            devInfo = soup.find('div', {'class': 'content contains-text-link'})

            site_array = [find_between(link['href'], '?q=', '&') for link in soup.findAll('a', href=True, text='Acesse o site')]
            site = site_array[0] if len(site_array) > 0 else ''
            email = re.search('(?=mailto:).*?(?=")', str(devInfo)).group(0).replace('mailto:', '')

            score_total = soup.select(".score")[0].text

            one_star 	= int(soup.select("div.rating-bar-container.one")[0].text.lstrip()[1:].rstrip().lstrip().replace('.',''))
            two_stars 	= int(soup.select("div.rating-bar-container.two")[0].text.lstrip()[1:].rstrip().lstrip().replace('.',''))
            three_stars = int(soup.select("div.rating-bar-container.three")[0].text.lstrip()[1:].rstrip().lstrip().replace('.',''))
            four_stars 	= int(soup.select("div.rating-bar-container.four")[0].text.lstrip()[1:].rstrip().lstrip().replace('.',''))
            five_stars 	= int(soup.select("div.rating-bar-container.five")[0].text.lstrip()[1:].rstrip().lstrip().replace('.',''))
            sum_stars 	= one_star+two_stars+three_stars+four_stars+five_stars

            app_info = {'AppName': appName,
                        'url': url,
                        'category': category,
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
                author 	= review.find('span', {'class': 'author-name'}).text.rstrip().lstrip()
                authorId = find_between(str(review.find('span', {'class': 'author-name'})), '?id=', '"')
                date 	= review.find('span', {'class': 'review-date'}).text
                message = review.find('div', {'class': 'review-body'}).text.replace('Resenha completa', '').rstrip().lstrip()
                app_info['reviews']['comments'].append({'author': author, 'authorId': authorId, 'date': date, 'message': message.encode('utf-8')})

            # print json.dumps(app_info, indent=4), quit()

            json.dump(app_info, open('apps_info_json/%s.json' % file_name, 'w'))
