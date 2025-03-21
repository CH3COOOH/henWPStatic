# -*- coding: UTF-8 -*-
import re
import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def convert_absolute_to_relative(content, base_domain, base_url):
	if base_url.endswith(('.js', '.css')):
		lines = content.splitlines()
		for i, line in enumerate(lines):
			if base_domain in line:
				lines[i] = line.replace(f"https://{base_domain}/", '/').replace(f"http://{base_domain}/", '/')
		return '\n'.join(lines)
	else:
		print(f"CA2R: Analyzing {base_url}, seems like a HTML")
		soup = BeautifulSoup(content, 'html.parser')

		href_tags = soup.find_all(['a', 'link'], href=True)
		src_tags = soup.find_all(['img', 'script'], src=True)
		all_tags = href_tags + src_tags

		for tag in all_tags:
			if tag.name == 'a' or tag.name == 'link':
				attr = 'href'
			elif tag.name == 'img' or tag.name == 'script':
				attr = 'src'
			else:
				continue

			resource_url = urljoin(base_url, tag[attr])
			uri = urlparse(resource_url).path
			if uri == '':
				uri = '/'

			if urlparse(resource_url).netloc == base_domain:
				# print(f"CA2R: Translate ({attr}){resource_url} -> {uri}")
				tag[attr] = uri
				if tag.has_attr('srcset'):
					tag.attrs.pop('srcset')
					print(f" + CA2R: Remove srcset attr for {resource_url}")
		return str(soup)
	return content

def is_match_list(t, lst):
	for p in lst:
		match = re.match(p, t)
		if match:
			return True
	return False

def search_pattern(rtext, full_text):
	matches = re.findall(rtext, full_text)
	return matches


class HWPSTC:
	def __init__(self, homepage, sitemap, saveto=None, dig=False):
		self.url_home = homepage
		self.url_sitemap = urljoin(homepage, sitemap)
		self.dig = dig
		self.known_urls = []

		self.this_base_domain = urlparse(homepage).netloc
		self.known_fname = self.__known_fname(self.this_base_domain)
		self.known_exclude_list = self.__known_exclude_list()

		if saveto == None:
			self.saveto = self.this_base_domain.replace(':', '_')
		else:
			self.saveto = saveto

	def __known_exclude_list(self):
		url_pages = r'^%s/\d+/$' % urljoin(self.url_home, 'page')
		url_home = r'^%s$' %  self.url_home
		return [url_pages, url_home]

	def __known_fname(self, base_name):
		return base_name.replace(':', '_') + '.known'

	def dump_known_urls(self):
		known_urls_dump = list(filter(lambda u: is_match_list(u, self.known_exclude_list) == False, self.known_urls))
		with open(self.known_fname, 'w') as o:
			o.write('\n'.join(known_urls_dump))
		return 0

	def load_known_urls(self):
		if os.path.exists(self.known_fname) == False:
			return -1
		print('Try to load [%s]...' % self.known_fname)
		with open(self.known_fname, 'r') as o:
			_buf = o.read()
		for u in _buf.split('\n'):
			if u == '':
				continue
			self.known_urls.append(u)
		print('%d known URLs loaded!' % len(self.known_urls))
		return 0

	def __url_parse(self, u):
		if '?' in u:
			return -1
		parsed_url = urlparse(u)
		path = parsed_url.path.lstrip('/')

		## Create resource save path ----->>
		_, ext = os.path.splitext(path)
		if bool(ext) == True:
			## It is a file, like "xxx.css"
			file_name = os.path.basename(path)
		else:
		## It is just a path, like "xxx/xxx" or "xxx/xxx/"
			file_name = ('index.html')
			if len(path) > 0 and path[-1] != '/':
			## "xxx/xxx", but web page
				path += '/'
		# <<-----

		return {
			'base': parsed_url.netloc,
			'path': path,
			'fname': file_name
		}

	def __mkdir_by_path(self, path):
		## Create folders ----->>
		folder_path = os.path.dirname(path)
		local_folder = os.path.join(self.saveto, folder_path)
		os.makedirs(local_folder, exist_ok=True)
		# <<-----
		return local_folder	


	# -----------
	# name: get(url)
	# function: get html sorce code from "url"
	# -----------
	def get(self, url, isText=True):
		try:
			response = requests.get(url)
			response.raise_for_status()
			if isText == True:
				return response.text
			else:
				return response.content
		except requests.exceptions.RequestException as e:
			print(f"Error fetching HTML from {url}: {e}")
			return None


	# -----------
	# name: get_urls_from_sitemap(sitemap_html)
	# function: parse "sitemap_html", find url in "<loc>xxx</loc>", save "xxx" to a list
	# -----------
	def get_urls_from_sitemap(self, sitemap_url):
		sitemap_html = self.get(sitemap_url)
		if sitemap_html == None:
			print('**HWPSTC::get_urls_from_sitemap failed...')
			return []
		soup = BeautifulSoup(sitemap_html, 'html.parser')
		loc_tags = soup.find_all('loc')
		urls = [loc.get_text() for loc in loc_tags]
		return urls


	# -----------
	# name: get_res_urls(url)
	# function:
	#  1. parse html of "url", look for urls in the html page
	#  2. check each of the url. if it points to the resource of current site, save it into a list
	# -----------
	def get_res_urls(self, url, ext_filter=None):
		response_text = self.get(url)
		if response_text == None:
			return None

		soup = BeautifulSoup(response_text, 'html.parser')
		# parsed_url = urlparse(url)
		# base_domain = parsed_url.netloc
		res_urls = []

		for tag in soup.find_all(href=True):
			resource_url = urljoin(url, tag['href'])
			if urlparse(resource_url).netloc == self.this_base_domain:
				res_urls.append(resource_url)
		
		for tag in soup.find_all(src=True):
			resource_url = urljoin(url, tag['src'])
			if urlparse(resource_url).netloc == self.this_base_domain:
				res_urls.append(resource_url)
		
		for tag in soup.find_all('meta', content=True):
			if 'url' in tag.get('property', '').lower() or 'url' in tag.get('name', '').lower():
				resource_url = urljoin(url, tag['content'])
				if urlparse(resource_url).netloc == self.this_base_domain:
					res_urls.append(resource_url)

		res_urls = list(set(res_urls))
		if ext_filter != None:
			res_urls = list(filter(lambda u: u.lower().endswith(ext_filter), res_urls))
		return list(set(res_urls))


	def __is_this_src(self, src_url):
		return urlparse(src_url).netloc == self.this_base_domain


	def __url_2Abs(self, u):
		if is_match_list(u, [r'%s/.+' % self.url_home]) == False:
			return urljoin(self.url_home, u)
		return u


	def get_res_urls_css(self, css_url):
		response_text = self.get(css_url)
		if response_text == None:
			return None
		found_urls = []
		lines = response_text.splitlines()
		for line in lines:
			found_urls.extend(search_pattern(r'url\((.*?\/wp-content\/.+?)\)', line))
		# for i, line in enumerate(lines):
		# 	found_urls.extend(search_pattern(r'src:url\((.+?)\)', line[i]))
		return list(map(self.__url_2Abs, found_urls))


	def save_res_from_url(self, u, dig=False):
		print(f"Save {u}")
		parsed_url = self.__url_parse(u)
		if parsed_url == -1:
			print(f"Skip URL: {u}")
			return -1
		base_domain = parsed_url['base']
		path = parsed_url['path']
		save_name = parsed_url['fname']

		local_folder = self.__mkdir_by_path(path)
		local_file_path = os.path.join(local_folder, save_name)
		print(f" -> {local_file_path}")

		# Save the content of "u" into path that same as its URI
		filter_list = ('.html', '.js', '.htm', '.css')

		if save_name.endswith(filter_list):
			_buf = self.get(u, isText=True)
			if _buf == None:
				print(f"Error downloading {u}")
				return -1

			## Fetch URLs in CSS files, like *.woff
			if save_name.endswith('.css'):
				src_in_css = self.get_res_urls_css(u)
				self.save_res_from_urls(src_in_css)

			content = convert_absolute_to_relative(_buf, base_domain, u)
			with open(local_file_path, 'w', encoding='utf-8') as file:
				file.write(content)
		else:
		## Save as bin, such as images
			_buf = self.get(u, isText=False)
			if _buf == None:
				print(f"Error downloading {u}")
				return -1
			with open(local_file_path, 'wb') as file:
				file.write(_buf)
		if dig == True and save_name.endswith(('.html', '.htm')):
			print(f"+ Now dig into {u}")
			self.save_res_from_urls(self.get_res_urls(u, ext_filter=('.jpg', '.gif', '.png')))
		return 0


	def save_res_from_urls(self, urls, add_as_known=True, dig=False):
		for u in urls:
			if u in self.known_urls:
				print(f"Skip known: {u}")
				continue
			self.save_res_from_url(u, dig=dig)
			if add_as_known:
				self.known_urls.append(u)


	def save_homepage(self):
		print(f"Save homepage")
		self.save_res_from_url(self.url_home)

		urls_in_home = self.get_res_urls(self.url_home)
		print(f"Found {len(urls_in_home)} URL(s) in Home")
		self.save_res_from_urls(urls_in_home, dig=self.dig)


	def save_urls_in_sitemap(self):
		## Save sitemap itself
		self.save_res_from_url(self.url_sitemap)
		self.save_res_from_url(urljoin(self.url_home, '/main-sitemap.xsl'))
		## ^ Style file of the sitemap XML

		## Save urls in sitemap
		urls_in_sitemap = self.get_urls_from_sitemap(self.url_sitemap)
		print(f"Found {len(urls_in_sitemap)} URL(s) in Sitemap.")
		self.save_res_from_urls(urls_in_sitemap, dig=self.dig)


	def save_pages(self):
		p = 2
		while True:
			u = urljoin(self.url_home, '/page/%d/'%p)
			# print(u)
			if self.save_res_from_url(u) == -1:
				break
				p += 1
			p += 1


	def start(self):
		self.load_known_urls()
		self.save_homepage()
		self.save_urls_in_sitemap()
		self.save_pages()
		self.dump_known_urls()

