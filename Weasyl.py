"""
Weasyl interface class for Python

Powered by Requests - Fueled by Caffeine - Driven by Furries
"""

import pickle, requests, re, sys, os

class Weasyl:
	WEASYL_URL = "https://www.weasyl.com"

	def __init__(self, useragent=None):
		"""
		Default constructor

		useragent --> User Agent (optional, defaults to IE5.5)
		"""
		self.session = requests.Session()
		if useragent is None:
			self.session.headers.update({'User-Agent': 'Libfurator/0.1 (http://www.bitbucket.org/philpem/libfurator)'})
		else:
			self.session.headers.update({'User-Agent': useragent})

		# forcibly update logged-in status
		self.is_logged_in(force=True)

	def __request(self, url, data=None, files=None):
		# TODO - Add rate limiting here
		if data is None:
			r = self.session.get(self.WEASYL_URL + url)
		else:
			if files is None:
				r = self.session.post(self.WEASYL_URL + url, data=data)
			else:
				r = self.session.post(self.WEASYL_URL + url, data=data, files=files)
		return r

	def __decode_options(self, data):
		listdata = dict()
		for i in re.finditer(r'<option value="(.*?)".*?>(.*?)</option>', data):
			if i.group(1).strip() == '':
				continue
			listdata[int(i.group(1))] = i.group(2)
		return listdata

	def is_logged_in(self, force=False):
		"""
		Returns True if a user is logged in
		"""
		if not force:
			return self.__logged_in
		else:
			r = self.__request('/')
			res = r.content.find('<h3 id="header-guest">')
			if res != -1:
				# Matched the login banner, we're logged out ;(
				self.__logged_in = False
				return False
			else:
				# No login banner match, we're logged in!
				self.__logged_in = True
				self.signout_token = re.search(r'<a href="/signout\?token=([^"]*)">', r.content).group(1)
				print "signout token is ",self.signout_token
				return True

	def login(self, username, password):
		"""
		Log a user in

		Returns True on success, False on failure
		"""
		if self.__logged_in:
			raise ValueError  # FIXME - throw something better

		parms = {'username': username, 'password': password}
		r = self.__request('/signin', data=parms)
		with open("log.login", "wt") as f:
			f.write(r.content)
		if r.content.find("<strong>Whoops!</strong> The login information you entered was not correct.") != -1:
			return False
		else:
			self.__logged_in = True
			self.__username = username
			self.is_logged_in(force=True)
			return True

	def logout(self):
		"""
		Log out

		Has no return value, alas.
		"""
		if not self.signout_token:
			raise ValueError # need a signout token! - FIXME throw something better
		r = self.__request('/signout?token=%s' % self.signout_token)
		self.__logged_in = False
		self.__username = None

	def submit_prepare(self, submittype):
		"""
		Fetches upload token, category, folder and ratings option data for a given submission type

		submittype: 'visual'
		Returns: Tuple -- token, categories, folders, ratings
		"""
		resp = self.__request(("/submit/%s" % submittype))
		ra = re.search(r'<input type="hidden" name="token" value="(.*)"', resp.content)
		token = ra.group(1)

		categories = self.__decode_options(re.search(r'<select name="subtype" class="input" id="submissioncat">(.*?)</select>', resp.content, re.DOTALL).group(1))
		folders = self.__decode_options(re.search(r'<select name="folderid" class="input" id="submissionfolder">(.*?)</select>', resp.content, re.DOTALL).group(1))
		ratings = self.__decode_options(re.search(r'<select name="rating" class="input" id="submissionrating">(.*?)</select>', resp.content, re.DOTALL).group(1))

		return token, categories, folders, ratings

	def submit_visual(self, token, submissionfilename, submissiondata, title, description, category, folder, rating, tags, critique = False, friendsonly = False):
		# TODO - thumbnail file
		# TODO - fish token out of self.signout_token
		fields = {
				'token': token,
				'title': title,
				'subtype': str(category),
				'folderid': str(folder),
				'rating': str(rating),
				'content': description,
				'tags': tags
				}
		files = {'submitfile': (submissionfilename, open(submissiondata, 'rb'))}

		if critique:
			fields['critique'] = ''
		if friendsonly:
			fields['friends'] = ''

		upload_resp = self.__request('/submit/visual', data=fields, files=files)

		# Upload page sends us to the manage thumbnail page with the submission ID attached
		submit_id = re.search(r'http://www.weasyl.com/manage/thumbnail\?submitid=([0-9]*)', upload_resp.headers['location']).group(1)
		print "Submission ID %s" % submit_id

		# thumbnail submission (default mode)
		fields = {
				'token': token,
				'submitid': submit_id,
				'x1': 0,
				'y1': 0,
				'x2': 0,
				'y2': 0
				}
		resp = self.__request('/manage/thumbnail', data=fields)

		return resp

