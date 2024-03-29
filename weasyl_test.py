import os,sys
from Weasyl import Weasyl

if __name__ == '__main__':
	try:
		creds = os.getenv("WEASYL_CREDENTIALS")
	except:
		print "Set WEASYL_CREDENTIALS to your API key and try again."
		sys.exit(1)

	x = Weasyl()

	# Use the API key to log in
	print "login[apikey]: ", x.login(creds)

	if not x.is_logged_in():
		print "ERROR LOGGING IN :("
		sys.exit(1)
	print "is logged in: ", x.is_logged_in()

	## upload something
	token,categories,folders,ratings = x.submit_prepare('visual')
	subm = x.submit_visual(token, 'img_1875_v2.jpg', 'img_1875_v2.jpg', 'Eye of the Snowleopard', 'Eye of the Snowleopard\n\nN: 1875_V2', 1050, '', 10, 'photo snowleopard eye closeup')

	with open('logdata.subm', 'wt') as f:
		f.write(subm.content)

	x.logout()
	print "logged out"
