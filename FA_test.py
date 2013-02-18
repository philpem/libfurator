from FurAffinity import FurAffinity

if __name__ == '__main__':
	try:
		creds = os.getenv("FA_CREDENTIALS").partition(':')
	except:
		print "Set FA_CREDENTIALS to user:pass and try again."
		sys.exit(1)

	x = Weasyl()
	print "login: ", x.login(creds[0], creds[2])

	fa = FurAffinity()
	if not fa.is_logged_in():
		print "logging in --> ", fa.login(creds[0], creds[2])
		print "I HAZ LOG IN?  ", fa.is_logged_in()

	# turn off safe for work
	if 'sfw' in fa.cookiejar:
		del(fa.cookiejar['sfw'])

	# get me sum shuggar
	subm = fa.get_submission_list(user=creds[0], page=1, perpage=10, limit=1)
	print subm
	#print len(fa.get_submission_list(user='suburbanfox', page=1, limit=None))

	#print print fa.logout()
	#print fa.cookiejar
	#print fa.is_logged_in(force=True)


