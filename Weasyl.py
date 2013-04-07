"""
Weasyl interface class for Python

Powered by Requests - Fueled by Caffeine - Driven by Furries
"""

##
# TODO
##
# - Submit music, SWF files, textual content
# - Create/list folders

import pickle, requests, re, sys, os

class Weasyl:
	WEASYL_URL = "https://www.weasyl.com"

	def __init__(self, useragent=None, apikey=None):
		"""
		Default constructor

		useragent --> User Agent (optional -- intended to allow Weasyl admins to identify robots)
		"""

		# Initialise Requests and set a sensible user-agent so Weasyl admins can track Libfurator usage
		self.session = requests.Session()

		# 
		if useragent is None:
			self.session.headers.update({'User-Agent': 'Libfurator/0.1 (http://www.bitbucket.org/philpem/libfurator)'})
		else:
			self.session.headers.update({'User-Agent': useragent})

		# if an API key has been specified, use it to log in
		if apikey is not None:
			self.login(apikey)
		else:
			self.__logged_in = False


	def __request(self, url, data=None, files=None):
		# TODO - If we want to add rate limiting, it should probably go here
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

			with open("dump.txt", "wt") as f:
				f.write(r.content.encode('utf8'))

			if r.content.find('<div id="header-user">') != -1:
				# No login banner match, we're logged in!
				self.__logged_in = True
				return True
			else:
				# Matched the login banner, we're logged out ;(
				self.__logged_in = False
				return False


	def login(self, api_key):
		"""
		Log in using an API key

		Returns True on success, False on failure
		"""
		if self.__logged_in:
			# Log out before trying to log in again
			self.logout()

		# Save API key and check that we've successfully logged in
		self.session.headers.update({'X-Weasyl-API-Key': api_key})
		if self.is_logged_in(force=True):
			# Login succeeded
			return True
		else:
			# Login failed
			del self.session.headers['X-Weasyl-API-Key']
			return False


	def logout(self):
		"""
		Log out

		Has no return value, alas.
		"""
		del self.session.headers['X-Weasyl-API-Key']
		self.__logged_in = False


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
		submit_id = re.search(r'https?://www.weasyl.com/manage/thumbnail\?submitid=([0-9]*)', upload_resp.headers['location']).group(1)
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

