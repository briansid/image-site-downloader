#! python3
#! image-site-downloader.py - Downloads all images from Google.
#  Requirements: python3, requests, bs4, selenium, geckodriver
#  Usage: image-site-downloader.py <search requests>

import requests, logging, sys, os, time, signal
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup as BS
logging.basicConfig(level=logging.INFO, format=\
' %(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.INFO)

# Timout settings (you may need to increase it for slow internet connection)
myTimeout = 10

# Catching CTRL+C
def sigint_handler(signal, frame):
	print('Interrupted')
	try:
		browser.close()
	except:
		pass
	sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# Get search request from command line argument
if len(sys.argv) < 2:
	print('Usage: image-site-downloader.py <search_request>')
	sys.exit()
search = ' '.join(sys.argv[1:])
dirName = ('images/' + search)
os.makedirs(dirName, exist_ok=True)
print('Creating folder %s...' % os.path.abspath(dirName))

# Open site with selenium, fill forms&submit, get URL
print('Opening browser...')
browser = webdriver.Firefox()
browser.set_page_load_timeout(myTimeout)
try:
	browser.get('https://www.google.com/search?tbm=isch&q=' + str(search))
except WebDriverException:
	print('Internet connection problem.')
	browser.close()
	sys.exit()
content = browser.page_source
url = browser.current_url
logging.info('contentLen=%s' % len(content))

# Get site with requests, make soup and find elements
soup = BS(content, "lxml")
nameElems = soup.select('a.rg_l img[name]')

# Loop thrue the elements and create soup for each
imgLinks = []
print('Googling...')
botCount = 0
for i in range(len(nameElems)):
	imgUrl = url + '&imgrc=' + nameElems[i].get('name')
	try:
		browser.get(imgUrl)
	except TimeoutException:
		print('Connect timeout: %s' % imgUrl)
		continue
	time.sleep(myTimeout/10)
	content = browser.page_source
	soup = BS(content, "lxml")	

	# Select element with photo and make requests
	imgElems = soup.select('.irc_mi') 
	for elem in imgElems:
		try:	
			imgLink = elem.get('src')
		except IndexError as err:
			if botCount == 3:
				print('\nAnti-Bot Triggered: Stopping...')
				break
			print(err)
			botCount +=1
			continue		
		if imgLink != None and (imgLink.lower().endswith('.jpg') or \
		imgLink.lower().endswith('.png') or \
		imgLink.lower().endswith('.jpeg')):	 			
			imgLinks.append(imgLink)
			print('Found images: %i' % len(imgLinks), end="\r")
			break
browser.close()
logging.info('Links=%s' % imgLinks)

# Save images
print('\nDownloading...')
imgCount = len(imgLinks)
for img in imgLinks:
	try:
		res = requests.get(img, timeout=myTimeout/2)
	except:
		print('Timeout: %s' % img)
		continue
	try:
		res.raise_for_status()
	except:
		print('Problem loading page: %s' % img)
		continue
	imgFile = open(os.path.join(dirName, os.path.basename(img)), 'wb')
	for chunk in res.iter_content(100000):
		imgFile.write(chunk)
	imgFile.close()
	imgCount -= 1
	print('Images left: %i' % imgCount, end="\r")
print('\nDone.')


