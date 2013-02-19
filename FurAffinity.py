"""
FurAffinity interface class for Python

Powered by Requests - Fueled by Caffeine - Driven by Furries
"""

import pickle, requests, re
from utils import html_unescape

class FurAffinity:
	FA_URL = "https://www.furaffinity.net"

	def __init__(self, useragent=None, save_cookies=True):
		"""
		Default constructor

		useragent     --> User Agent (optional, defaults to IE5.5)
		save_cookies  --> True to enable caching of cookies
		"""
		self.session = requests.Session()
		if useragent is None:
			self.session.headers.update({'User-Agent': 'Libfurator/0.1 (http://www.bitbucket.org/philpem/libfurator)'})
		else:
			self.session.headers.update({'User-Agent': useragent})

		self.save_cookies = save_cookies
		if save_cookies:
			try:
				self.session.cookies = pickle.load(open("furaffinity_cookies.p", "rb"))
			except IOError:
				# If the file doesn't exist, we should use the existing cookie jar
				pass

		if useragent is not None:
			self.useragent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
		else:
			self.useragent = useragent

		# forcibly update logged-in status
		self.is_logged_in(force=True)

	def __del__(self):
		# save cookies
		if self.save_cookies:
			pickle.dump(self.session.cookies, open("furaffinity_cookies.p", "wb"))

	def __request(self, url, data=None, files=None):
		# TODO - Add rate limiting here
		if data is None:
			r = self.session.get(self.FA_URL + url)
		else:
			if files is None:
				r = self.session.post(self.FA_URL + url, data=data)
			else:
				r = self.session.post(self.FA_URL + url, data=data, files=files)
		return r

	def is_logged_in(self, force=False):
		"""
		Returns True if a user is logged in
		"""
		if not force:
			return self.__logged_in
		else:
			r = self.__request('/')
			res = re.search(r'<li class="noblock"><a href="/register/">Register</a> | <a href="https://www.furaffinity.net/login/">Log in</a></li>', r.content)
			if res is not None:
				# Matched the login banner, we're logged out ;(
				self.__logged_in = False
				return False
			else:
				# No login banner match, we're logged in!
				self.__logged_in = True
				return True

	def login(self, username, password):
		"""
		Log a user in

		Returns True on success, False on failure
		"""
		if self.__logged_in:
			raise ValueError  # FIXME - throw something better

		parms = {'action':'login', 'retard_protection':1, 'name':username, 'pass':password}
		r = self.__request('/login', data=parms)
		if r.content.find("You have typed in an erroneous username or password") != -1:
			return False
		else:
			self.__logged_in = True
			self.__username = username
			return True

	def logout(self):
		"""
		Log out

		Has no return value, alas.
		"""
		r = self.__request('/logout')
		self.__logged_in = False
		self.__username = None

	class submission:
		def __init__(self, sid, thumb, full, title, description, keywords, rating):
			self.sid      = sid
			self.thumb    = thumb
			self.full     = full
			self.title    = title
			self.keywords = keywords
			self.rating   = rating
			self.description = description

		def __repr__(self):
			return "(%d) '%s' thn %s act %s keywords [%s] rating [%s]\n%s" % (self.sid, self.title, self.thumb, self.full, self.keywords, self.rating, self.description)

	def get_submission_list(self, user=None, zone='gallery', page=1, perpage=60, limit=1):
		"""
		Get a list of submissions

		user = username (defaults to local logged in user)
		zone = gallery or scraps
		page = starting page
		perpage = number of submissions per page
		limit = max number of pages
		"""
		if zone != 'gallery' and zone != 'scraps':
			raise ValueError # you naughty furry, gallery or scraps only!
		if user is None:
			if self.__logged_in:
				user = self.__username
			else:
				raise ValueError # FIXME raise something sane

		# grab a submission page
		ids = list()

		if limit is not None:
			n = limit
		else:
			n = -1

		download_re = re.compile(r'<a href="([^"]*)"> Download </a>')
		rating_re = re.compile(r'<img alt="[^ ]* rating" src="/img/labels/([^\.]*?)\.gif" />')

		title_re = re.compile(r'<textarea name="keywords" id="keywords" rows="3" cols="85" class="textarea">(.*?)</textarea>', re.DOTALL)
		description_re = re.compile(r'<textarea id="JSMessage" name="message" rows="6" cols="85" class="textarea">(.*?)</textarea>', re.DOTALL)
		keywords_re = re.compile(r'<textarea name="keywords" id="keywords" rows="3" cols="85" class="textarea">(.*?)</textarea>', re.DOTALL)

		pagenum = page
		while True:
			# Gallery url format: gallery/{username}/{pagenumber}
			r = self.__request('/gallery/%s/%d/' % (user, pagenum), data={'perpage':perpage})
			for i in re.findall(r'<b id="sid_([0-9]*)" class="r-[a-z]* t-image"><u><s><a href="/view/[0-9]*/"><img alt="" src="([^"]*)"/>', r.content):
				# get submission ID and thumbnail URL
				s_id = int(i[0])
				thn_url = "http:" + i[1]

				# request the submission itself
				s = self.__request('/full/%s' % (i[0],))

				# parse the submission page to get the 'full' image url
				fullimg_url = html_unescape("http:" + download_re.search(s.content).group(1))
				rating      = html_unescape(rating_re.search(s.content).group(1))

				# grab the description with BBcode in place (this requires a third request!)
				s = self.__request('/controls/submissions/changeinfo/%s/' % (i[0],))
				title       = html_unescape(title_re.search(s.content).group(1))
				description = html_unescape(description_re.search(s.content).group(1))
				keywords    = [x.strip() for x in html_unescape(keywords_re.search(s.content).group(1)).split(' ')]

				# create a submission object and append it to our little list
				sub = self.submission(sid=s_id, thumb=thn_url, full=fullimg_url, title=title, description=description, keywords=keywords, rating=rating)
				ids.append(sub)

			n = n - 1
			pagenum = pagenum + 1
			if (n <= 0 and limit is not None) or len(t_ids) == 0:
				break

		return ids

