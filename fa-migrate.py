#!/usr/bin/env python

import urllib
import urllib2
import cookielib
import re

cookiejar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
urllib2.install_opener(opener)

FA_USER_OLD="YOUR_OLD_ACCT_USERNAME"
FA_PASS_OLD="YOUR_OLD_ACCT_PASSWORD"
FA_USER_NEW="YOUR_NEW_ACCT_USERNAME"
FA_PASS_NEW="YOUR_NEW_ACCT_PASSWORD"

DEBUG_REQS = False

USER_AGENT='Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

def requ(url, params = {}):
	if DEBUG_REQS:
		print "\tREQUEST: %s "%url,params
	# generate urlencoded request
	data = urllib.urlencode(params)
	# fake a user agent (furaffinity doesn't seem to mind, but it's better to be safe than sorry)
	txdata = {'User-agent' : USER_AGENT}
	# make the request
	if url == 'login':
		FA_HOST="https://www.furaffinity.net"
	else:
		FA_HOST="http://www.furaffinity.net"
	req = urllib2.Request("%s/%s" % (FA_HOST, url), data,  {'User-agent' : USER_AGENT})
	resp = urllib2.urlopen(req)
	# return the page data
	return resp.read()

# log in to furaffinity
def login(user, pw):
	resp = requ("login", {"action":"login", "retard_protection":1, "name":user, "pass":pw})
	if resp.find("You have typed in an erroneous username or password") != -1:
		print "Login failed!"
		return False
	else:
		return True

# log out of furaffinity
def logout():
	requ("logout")

# get the number of buddy list pages
def buddy_num_pages():
	resp = requ("controls/buddylist")
	r = re.search('Pages [(]([0-9]+)[)]:', resp)
	return int(r.group(1))

# get a page of buddies from FurAffinity
def buddy_get(page = 1):
	# request the specified buddy list page
	resp = requ("controls/buddylist/%d" % page)

	# build a regex to find all the users on the page by looking for avatar
	# images and scraping the userid from the alt text
	r = re.compile("alt=\"Avatar \[ ([^ ]+) \]\"/>")

	# find all our buddies by repeatedly applying the regex using a python
	# iterator
	buddies = []
	for i in r.finditer(resp):
		buddies.append(i.group(1))
	return buddies

# get a page of favourites from FurAffinity
def fav_get(page = 0):
	# request the specified favs page
	resp = requ("controls/favorites/%d" % page)

	# build a regex to find all the users on the page by looking for avatar
	# images and scraping the userid from the alt text
	r = re.compile('<a href="/view/([0-9]+)">')

	# find all our buddies by repeatedly applying the regex using a python
	# iterator
	favs = []
	for i in r.finditer(resp):
		favs.append(i.group(1))
	return favs

# watch a user
def do_watch(user):
	# FurAffinity sends an ID tag with every watch page (I guess to hinder
	# XSRF attacks). So we need to do two requests: one to get the ID tag,
	# and one to initiate the watch. Fun.
	resp = requ("user/%s" % user)
	m = re.search('href="/watch/'+user+'/\?key=([0-9a-fA-F]+)"><font', resp)
	if m == None:
		return False
	key = m.group(1)

	# we have the magic key, now watch the user :3
	resp = requ("watch/%s/?key=%s" % (user,key))
	m = re.search('has been added to your watch list!', resp)
	if m != None:
		return True
	else:
		return False

# favourite a submission
def do_fav(idnum):
	# FurAffinity sends an ID tag with every watch page (I guess to hinder
	# XSRF attacks). So we need to do two requests: one to get the ID tag,
	# and one to initiate the watch. Fun.
	resp = requ("view/%s" % idnum)
	m = re.search('<a href="/fav/'+idnum+'/\?key=([0-9a-fA-F]+)">\+Add to Favorites</a>', resp)
	if m == None:
		return False
	key = m.group(1)

	# we have the magic key, now watch the user :3
	resp = requ("fav/%s/?key=%s" % (idnum,key))
	m = re.search('-Remove from Favorites', resp)
	if m != None:
		return True
	else:
		return False

# convert a boolean to a human-readable success/failure message
def hu(bo):
	if bo:
		return "Success!"
	else:
		return "ERROR!"

def main():
	print "--- Mooching info from old user account ---"
	print "Logging in as '%s'... " % FA_USER_OLD,
	print hu(login(FA_USER_OLD, FA_PASS_OLD))
	print "Magic Cookies: ", cookiejar
	print

	migrate_buddies = False
	migrate_favs = True

	if migrate_buddies:
		print "Grabbing length of buddy list... ",
		bl = buddy_num_pages()
		print "Buddy list is %d pages long." % bl

		buddies = []
		for i in range(1, bl+1):
			print "Grabbing page %d..." % i
			bl = buddy_get(i)
			for x in bl:
				buddies.append(x)

		print "Buddy list: ", buddies
		print "Buddy count: %d", len(buddies)
		print

	if migrate_favs:
		print "Getting favs list..."
		# Furaffinity doesn't tell us how long the +fav list is, so we iterate
		# until we get a "no submissions to list" alarm
		i = 0
		favs = []
		while True:
			print "Getting favs list page %d" % (i+1),
			favtmp = fav_get(i)
			if favtmp != []:
				for x in favtmp:
					favs.append(x)
				i = i + 1
				print "... OK"
			else:
				print "... no favs on this page!"
				break
		print "%d pages of favs" % i
		print "%d favourites" % len(favs)
		favs.reverse()
		print "Rfavs: ",favs
		print

	# switch to 'new' user account
	print "--- Switching to new user account ---"
	logout()
	print "Post-logout Magic Cookies: ", cookiejar
	print "Logging in as '%s'... " % FA_USER_NEW, login(FA_USER_NEW, FA_PASS_NEW)
	print "Fresh Magic Cookies: ", cookiejar

	if migrate_buddies:
		for usr in buddies:
			print "Watching %s... "%usr,
			print hu(do_watch(usr))

	if migrate_favs:
		for fav in favs:
			print "Adding %s to Favourites..." % fav,
			print hu(do_fav(fav))

main()
