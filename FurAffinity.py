"""
FurAffinity interface class for Python

Powered by Requests - Fueled by Caffeine - Driven by Furries
"""

import pickle, requests, re

FA_URL = "https://www.furaffinity.net"

class FurAffinity:
	def __init__(self, useragent=None):
		"""
		Default constructor

		useragent --> User Agent (optional, defaults to IE5.5)
		"""
		# load cookies if they're present
		try:
			self.cookiejar = pickle.load(open("cookies.p", "rb"))
		except:
			self.cookiejar = dict()

		if useragent is not None:
			self.useragent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
		else:
			self.useragent = useragent

		# forcibly update logged-in status
		self.is_logged_in(force=True)

	def __del__(self):
		# save cookies
		pickle.dump(self.cookiejar, open("cookies.p", "wb"))

	def is_logged_in(self, force=False):
		"""
		Returns True if a user is logged in
		"""
		if not force:
			return self.__logged_in
		else:
			r = requests.get(FA_URL, cookies=self.cookiejar)
			self.cookiejar.update(r.cookies)
			res = re.search(r'<li class="noblock"><a href="/register/">Register</a> | <a href="https://www.furaffinity.net/login/">Log in</a></li>', r.content)
			if res is None:
				# Matched the login banner, we're logged out ;(
				self.__logged_in = False
				return False
			else:
				# No login banner match, we're logged in!
				self.__logged_in = True
				return True

	def login(self, username, password):
		"""
		Log a user into FA

		Returns True on success, False on failure
		"""
		if self.__logged_in:
			raise ValueError  # FIXME - throw something better

		parms = {'action':'login', 'retard_protection':1, 'name':username, 'pass':password}
		r = requests.get(FA_URL + "/login", data=parms)
		self.cookiejar.update(r.cookies)
		if r.content.find("You have typed in an erroneous username or password") != -1:
			return False
		else:
			self.__logged_in = True
			self.__username = username
			return True

	def logout(self):
		"""
		Log out of FA

		Has no return value, alas.
		"""
		r = requests.get(FA_URL + "/logout", cookies=self.cookiejar)
		self.cookiejar.update(r.cookies)
		print "logout cookiejar", r.cookies
		self.__logged_in = False
		self.__username = None

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

		pagenum = page
		while True:
			r = requests.get("%s/gallery/%s/%d/" % (FA_URL, user, pagenum), data={'perpage':perpage})
			t_ids = [int(i) for i in re.findall(r'<b id="sid_([0-9]*)" class="r-[a-z]* t-image">', r.content)]
			ids.extend(t_ids)
			n = n - 1
			pagenum = pagenum + 1
			if (n <= 0 and limit is not None) or len(t_ids) == 0:
				break

		return ids

