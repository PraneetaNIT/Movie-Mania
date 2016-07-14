from django.shortcuts import render
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import render_to_response
from django.db import models
from movies.models import UserProfile, Follow, Message
from django.http import HttpResponse as hr, HttpResponseRedirect
from movies.forms import UserForm, UserProfileForm, LoginForm, Changed
from django.core.mail import send_mail
from django.contrib.sites.models import Site
import sys,platform,json,time,random,urllib2,smtplib,unicodedata,psycopg2
import datetime
from django.utils import timezone
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from urllib2 import Request
from BeautifulSoup import BeautifulSoup
from time import mktime

class MyEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(mktime(obj.timetuple()))
		return json.JSONEncoder.default(self, obj)

def home(request):
	context = RequestContext(request)
	context_dict = {}
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)
		context_dict['profile'] = profile
	con = None
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		cur.execute("SELECT * from movies ORDER BY RANDOM() DESC LIMIT 30")
		ver = cur.fetchall()
		context_dict['ver'] = ver    
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return render_to_response('movies/home.html', context_dict,context)

def change(s):
	for i in range(0,len(s)):
		a = list(s[i])
		a[7] = float(int(a[7]*100))/100
		s[i] = tuple(a) 
	return s
	
def register(request):
	context = RequestContext(request)
	if request.method == 'POST':
		user_form = UserForm(request.POST)
		user_profile = UserProfileForm(request.POST,request.FILES)
		email = request.POST['email']
		name = request.POST['username']
		user_name = User.objects.filter(username = name)
		user_email = User.objects.filter(email = email)
		if (len(user_email)>0 and len(user_name)>0):
			return hr(json.dumps("BOTH"))
		elif (len(user_email)>0):
			return hr(json.dumps("EMAIL"))
		elif (len(user_name)>0):
			return hr(json.dumps("NAME"))
		if user_form.is_valid() and user_profile.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()
			profile = user_profile.save(commit=False)
			profile.user = user
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			else:
				profile.picture = "profile_images/default.jpg"	
			profile.save()
			con = None
			try:
				con = psycopg2.connect(database='project',user='postgres')
				cur = con.cursor()
				cur.execute("INSERT INTO user_profile VALUES(%s,%s,%s,%s)", (profile.age,profile.sex,profile.occupation,profile.zipcode,))
				con.commit()
			except psycopg2.DatabaseError, e:
				if con:
					con.rollback()
				print 'Error %s' %e
				sys.exit(1)
			finally:
				if con:
					con.close()
			return hr(json.dumps("NO"))
		else:
			err = json.dumps(user_form.errors)
			return hr(err)
	else:
		if request.user.is_authenticated():
			return HttpResponseRedirect("/movies/profile/"+request.user.username)
		else:
			user_form = UserForm()
			user_profile = UserProfileForm()
	context_dict = { 'user_form': user_form } 
	context_dict['user_profile'] = user_profile
	return render_to_response("movies/register.html",context_dict,context)

@login_required
def no_picture(request):
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)	
		profile.picture = "profile_images/default.jpg"
		profile.save()		
		return hr(json.dumps("NO"))
		
@login_required
def facebook_profile(request):
	if request.method == 'POST':
		if request.user.is_authenticated():
			url = 'https://www.facebook.com/'
			if request.method == 'POST':
				user_id = request.POST['picture']
				req = Request(url + user_id) 
				response = urllib2.urlopen(req)
				the_page = response.read()
				the_page = the_page.replace("<!--", "")
				the_page = the_page.replace("-->", "")
				parsed_html = BeautifulSoup(the_page)
				parsed_things = parsed_html.find('a', {'class':'profilePicThumb'})    			
				pic_url = parsed_things('img')[0]['src']
				facebook_defined = 'https://fbcdn-profile-a.akamaihd.net/'
				splitted_url = pic_url.split('/')
				picture_id = splitted_url[-1].replace('a.', 'n.')
				pic_url = facebook_defined + picture_id
				response = urllib2.urlopen(pic_url)
				pro = request.user.username
				try:
					f = open("/home/vijender/workspace/DBMS/media/profile_images/"+pro+".jpg","wb")
					try:
						f.write(response.read())
					finally:
						f.close()						    	
				except Exception, e:
					raise e			
				profile = UserProfile.objects.get(user = request.user)	
				profile.picture = "profile_images/"+pro+".jpg"				
				profile.save()
				return hr(json.dumps("NO"))	
	else:
		return HttpResponseRedirect("/movies/changed")

@login_required
def change_profile(request):
	context = RequestContext(request)
	if request.method == 'POST':
		profile = UserProfile.objects.get(user = request.user)	
		user_form = Changed(request.FILES)
		if user_form.is_valid():			
			profile = UserProfile.objects.get(user = request.user)	
			profile.picture = request.FILES['picture']				
			profile.save()
			return hr(json.dumps("NO"))
	else:
		change_form = Changed()
		context_dict = {'login_form': change_form }
		return render_to_response("movies/change.html",context_dict,context)		

dict_interest = {0 : "Comedy",1 : "Drama",2 : "Fantasy",3 : "Horror",4 : "Biography",5 : "Thriller",6 : "Crime",7 : "Western",8 : "Musical",9 : "War",10 : "Sci-Fi",11 : "Action",12 : "Documentary",13 : "Romance",14 : "Animation",15 : "Mystery",16 : "Family",17 : "Adventure"}

def make_list(l):
	u = []
	for i in range(len(l)):
		if (l[i] == "yes"):
			u.append(dict_interest[i])
	return u 
			
@login_required		
def latest_updates(request):
	context = RequestContext(request)
	context_dict = {}
	user_suggestion = []
	movies_suggestion = []
	userid = (request.user.id + 943 - 1)
	if request.user.is_authenticated():
		pic = UserProfile.objects.get(user = request.user).picture
		context_dict['pic'] = pic
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("select interest from movies_userprofile where user_id = %s", (request.user.id,))
			ver = cur.fetchone()
			interest = make_list(ver[0].split(','))
			length = len(interest)
			cur.execute("select count(*) from auth_user");
			count = cur.fetchone()[0]	
			if (length <= 2):
				l = []
				while len(user_suggestion) < 3:
					j = random.randint(2,count-1)
					if (j != 9 and j != request.user.id and j not in l):
						l = l + [j]
						user = User.objects.get(id = j)
						try:
							status = user.follow.follower.filter(username = request.user.username)
						except:
							status = []
						if (len(status) == 0):
							pro = UserProfile.objects.get(user = user)
							user_suggestion.append((pro,user.username,user.first_name,user.last_name))
				l = []
				k = 0
				while len(movies_suggestion) < 3:
					k = k + 1
					j = random.randint(1,1682)
					if (j not in l):
						l = l + [j]
						cur.execute("select count(*) from movies_rated where movieid = %s and userid = %s",(j,userid,))
						current = cur.fetchone()[0]	
						if (current == 0 and k < 50 and length > 0):
							cur.execute("select genre from genre where movieid = %s",(j,))
							res = [row[0] for row in cur.fetchall()]
							if (len(list(set(interest) & set(res))) > 0):
								cur.execute("select title,year,imdbvotes,imdbrating,picture,language,movieid from movies where movieid = %s",(j,))
								result = cur.fetchone()
								a = list(result)
								a[3] = float(int(a[3]*100))/100
								result = tuple(a)
								movies_suggestion.append(result)
								k = 0
						else:
							if (current == 0):
								cur.execute("select title,year,imdbvotes,imdbrating,picture,language,movieid from movies where movieid = %s",(j,))
								result = cur.fetchone()
								a = list(result)
								a[3] = float(int(a[3]*100))/100
								result = tuple(a)
								movies_suggestion.append(result)
								k = 0
			else:
				l = []
				k = 0
				while len(user_suggestion) < 3:
					k = k + 1
					j = random.randint(2,count-1)
					if (j != 9 and j != request.user.id and j not in l):
						l = l + [j]
						cur.execute("select interest from movies_userprofile where user_id = %s", (j,))
						ver = cur.fetchone()
						random_interest = make_list(ver[0].split(','))
						if (k <= 20):
							if (len(list(set(interest) & set(random_interest))) > 2):
								user = User.objects.get(id = j)
								try:
									status = user.follow.follower.filter(username = request.user.username)
								except:
									status = []
								if (len(status) == 0):
									pro = UserProfile.objects.get(user = user)
									user_suggestion.append((pro,user.username,user.first_name,user.last_name))
									k = 0
						else:
							user = User.objects.get(id = j)
							try:
								status = user.follow.follower.filter(username = request.user.username)
							except:
								status = []
							if (len(status) == 0):
								pro = UserProfile.objects.get(user = user)
								user_suggestion.append((pro,user.username,user.first_name,user.last_name))
								k = 0
				l = []
				k = 0
				while len(movies_suggestion) < 3:
					k = k + 1
					j = random.randint(1,1682)
					if (j not in l):
						l = l + [j]
						cur.execute("select genre from genre where movieid = %s",(j,))
						res = [row[0] for row in cur.fetchall()]
						userid = (request.user.id + 943 - 1)
						cur.execute("select count(*) from movies_rated where movieid = %s and userid = %s",(j,userid,))
						current = cur.fetchone()[0]	
						if (len(res) > 1 and current == 0):
							if (k < 40):
								if (len(list(set(interest) & set(res))) > 1):
									cur.execute("select title,year,imdbvotes,imdbrating,picture,language,movieid from movies where movieid = %s",(j,))
									result = cur.fetchone()
									a = list(result)
									a[3] = float(int(a[3]*100))/100
									result = tuple(a)
									movies_suggestion.append(result)
									k = 0
							else:
								cur.execute("select title,year,imdbvotes,imdbrating,picture,language,movieid from movies where movieid = %s",(j,))
								result = cur.fetchone()
								a = list(result)
								a[3] = float(int(a[3]*100))/100
								result = tuple(a)
								movies_suggestion.append(result)
								k = 0
						else:
							if (current == 0 and len(list(set(interest) & set(res))) > 0):
								cur.execute("select title,year,imdbvotes,imdbrating,picture,language,movieid from movies where movieid = %s",(j,))
								result = cur.fetchone()
								a = list(result)
								a[3] = float(int(a[3]*100))/100
								result = tuple(a)
								movies_suggestion.append(result)
			context_dict['movies_suggestion'] = movies_suggestion 
			context_dict['user_suggestion'] = user_suggestion 
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
	return render_to_response('movies/updates.html', context_dict, context)
	
def Profile(request,name):
	context = RequestContext(request)
	context_dict = {}
	is_same = False
	Follow = False
	no_image = False
	user = None
	if request.user.is_authenticated():
		pic = UserProfile.objects.get(user = request.user).picture
		context_dict['pic'] = pic
		context_dict['login'] = request.user.username
		if (name == request.user.username):
			user = request.user
			profile = UserProfile.objects.get(user = user)
			if (profile.picture == 'profile_images/default.jpg'):
				no_image = True
			is_same = True
		else:
			user = User.objects.get(username = name)
			profile = UserProfile.objects.get(user = user)
		context_dict['user'] = user
		follower = None
		try:
			follower = user.follow.follower.all();
			context_dict['follower'] = len(follower)
			follower = follower[:9]
		except:
			follower = []
			context_dict['follower'] = len(follower)
		profiles = []
		for obj in follower:
			user = obj
			if (obj == request.user):
				Follow = True
			pro = UserProfile.objects.get(user = obj)
			profiles.append((pro,user.username))
		profiles1 = []
		context_dict['follow'] = Follow 
		context_dict['profile'] = profile
		context_dict['profiles'] = profiles
		context_dict['same'] = is_same
		context_dict['image'] = no_image
		userid = (profile.user_id + 943 - 1)
		con = None
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("SELECT * from movies,movies_rated where movies_rated.movieid = movies.movieid and userid = %s", (userid,))
			ver = cur.fetchall()
			ver = change(ver)
			context_dict['movie'] = ver
			context_dict['count'] = len(ver)
			cur.execute("select movies_follow.user_id from movies_follow,movies_follow_follower,auth_user where auth_user.username = %s and auth_user.id = movies_follow_follower.user_id and movies_follow_follower.follow_id = movies_follow.id;", (name,))
			ver = cur.fetchall()
			for vers in ver:
				user = User.objects.get(id = vers[0])
				pro = UserProfile.objects.get(user = user)
				profiles1.append((pro,user.username))
			context_dict['profiles1'] = profiles1
			context_dict['following'] = len(profiles1)
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return render_to_response("movies/profile.html",context_dict,context)
	else:
		return hr("SIGN IN IF ALREADY A MEMBER OR REGISTER IF NOT A MEMBER YET TO RATE MOVIES AND SEARCH PEOPLE")

def top100(request,top):
	context = RequestContext(request) 
	context_dict = {}
	con = None
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		if (top == "top100"):
			cur.execute("SELECT * from movies ORDER BY imdbrating DESC LIMIT 100")
			context_dict['top'] = "TOP 100"
		elif (top == "bottom100"):
			cur.execute("SELECT * from movies where imdbrating > 0 ORDER BY imdbrating ASC LIMIT 100")
			context_dict['top'] = "BOTTOM 100"
		ver = cur.fetchall()
		ver = change(ver)
		context_dict['movie'] = ver
		if request.user.is_authenticated():
			profile = UserProfile.objects.get(user = request.user)
			context_dict['profile'] = profile
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return render_to_response("movies/100.html",context_dict,context)

@login_required
def display_follow(request,name,follow):
	context = RequestContext(request)
	user = User.objects.get(username = name)
	context_dict = {}
	profiles = []
	if (follow == "follower"):
		follower = None
		try:
			follower = user.follow.follower.all()
		except:
			follower = []
		for obj in follower:
			status = []
			user = obj
			pro = UserProfile.objects.get(user = obj)
			try:
				status = user.follow.follower.filter(username = request.user.username)
			except:
				status = []
			if (len(status) != 0):
				profiles.append((pro,user.username,user.first_name,user.last_name,"YES"))
			else:
				if (user == request.user):
					profiles.append((pro,user.username,user.first_name,user.last_name,"SAME"))
				else:
					profiles.append((pro,user.username,user.first_name,user.last_name,"NO"))
		context_dict['profiles'] = profiles
		context_dict['follower'] = len(profiles)
	elif (follow == "following"):
		con = None
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("select movies_follow.user_id from movies_follow,movies_follow_follower,auth_user where auth_user.username = %s and auth_user.id = movies_follow_follower.user_id and movies_follow_follower.follow_id = movies_follow.id;", (name,))
			ver = cur.fetchall()
			for vers in ver:
				status = []
				user = User.objects.get(id = vers[0])
				pro = UserProfile.objects.get(user = user)
				try:
					status = user.follow.follower.filter(username = request.user.username)
				except:
					status = []
				if (len(status) != 0):
					profiles.append((pro,user.username,user.first_name,user.last_name,"YES"))
				else:
					profiles.append((pro,user.username,user.first_name,user.last_name,"NO"))
			context_dict['profiles'] = profiles
			context_dict['following'] = len(profiles)
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
	if request.user.is_authenticated():
			profile = UserProfile.objects.get(user = request.user)
			context_dict['profile'] = profile
	context_dict['key'] = follow
	return render_to_response("movies/follow.html",context_dict,context)

def view_all_message(request):
	l = []
	'''
	sent = list(request.user.sent_messages.all());
	recieved = list(request.user.received_messages.all());
	j = len(sent) - 1
	while (j > -1):
		if (sent[j].recipient.id not in l):
			l = l + [sent[j].recipient.id]
		else:
			del sent[j]
		j = j - 1
	j = len(recieved) - 1
	l = []
	while (j > -1):
		if (recieved[j].recipient.id not in l):
			l = l + [recieved[j].recipient.id]
		else:
			del recieved[j]
		j = j - 1
	'''
	
def view_user_message(request,name):
	context = RequestContext(request)
	context_dict = {}
	return render_to_response("movies/message.html",context_dict,context)
	
def save_message(request):
	message = request.GET['message']
	reciever = request.GET['reciever']
	m = Message()
	m.msg = message
	m.sender = request.user
	m.recipient = User.objects.get(id = reciever)  
	m.save()
	return hr("message successfully sent")
	
def movies(request, movieid):
	context = RequestContext(request) 
	con = None
	context_dict = {}
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		cur.execute("SELECT * from movies where movieid=%s",(movieid,))
		ver = cur.fetchall()
		ver = change(ver) 
		context_dict['ver'] = ver
		director = ver[0][4].replace(' ','_')
		context_dict['dir'] = director
		cur.execute("Select * from actors where movieid=%s", (movieid,))
		actor = cur.fetchall()
		context_dict['actor'] = actor
		i = 0
		for var in actor:
			a = list(actor[i])
			a.insert(2,var[1].replace(' ','_')) 
			actor[i] = tuple(a)
			i = i + 1
		cur.execute("Select * from genre where movieid=%s", (movieid,))
		ver = cur.fetchall()
		context_dict['genre'] = ver
		i = random.randint(0,len(ver)-1)
		cur.execute("Select genre.movieid,picture from movies,genre where genre.movieid = movies.movieid and genre = %s and genre.movieid <> %s ORDER BY RANDOM() LIMIT 15",(ver[i][1],ver[0][0]))
		ver = cur.fetchall()
		context_dict['recom'] = ver
		cur.execute("Select comment,date,first_name,last_name,username,picture,comment_id,upvotes from comments,auth_user,movies_userprofile where movieid = %s and site = %s and comments.userid = auth_user.id and auth_user.id = movies_userprofile.user_id ORDER BY comment_id ASC",(movieid,'http://127.0.0.1:8000/movies/'))
		comment = cur.fetchall()
		if request.user.is_authenticated():
			i = 0
			for comments in comment:
				a = list(comments)
				cur.execute("Select count(*) from comment_like where movieid = %s and userid = %s and comment_id = %s",(movieid,request.user.id,comments[6]))
				data = cur.fetchone()[0]
				cur.execute("Select comments,date,first_name,last_name,username,picture,secondary_comment_id,upvotes from secondary_comments,auth_user,movies_userprofile where movieid = %s and comment_id = %s and secondary_comments.userid = auth_user.id and auth_user.id = movies_userprofile.user_id ORDER BY secondary_comment_id ASC",(movieid,comments[6]))
				record = cur.fetchall()
				k = 0
				for records in record:
					l = list(records)
					cur.execute("Select count(*) from secondary_comment_like where movieid = %s and userid = %s and secondary_comment_id = %s",(movieid,request.user.id,records[6]))
					data1 = cur.fetchone()[0]
					if (len(records[0]) > 1):
						l.insert(8,"yes")
					else:
						l.insert(8,"no")
					if (data1 == 1):
						l.insert(9,"liked")
					else:
						l.insert(9,"unliked")
					record[k] = tuple(l)
					k = k+1		
				if (len(comments[0]) > 1):
					a.insert(8,"yes")
				else:
					a.insert(8,"no")
				if (data == 1):
					a.insert(9,"liked")
				else:
					a.insert(9,"unliked")
				a.insert(10,record)
				a.insert(11,len(record))
				comment[i] = tuple(a)
				i = i + 1
			profile = UserProfile.objects.get(user = request.user)
			context_dict['profile'] = profile
			userid = (profile.user_id + 943 - 1)
			cur.execute("select * from movies_rated where userid = %s and movieid = %s",(userid,movieid))
			result = cur.fetchall()
			if (len(result) == 0):
				context_dict['res'] = "no"
			else:
				context_dict['res'] = "yes"
				context_dict['my_rate'] = result[0]
		else:
			i = 0
			for comments in comment:
				cur.execute("Select comments,date,first_name,last_name,username,picture,secondary_comment_id,upvotes from secondary_comments,auth_user,movies_userprofile where movieid = %s and comment_id = %s and secondary_comments.userid = auth_user.id and auth_user.id = movies_userprofile.user_id ORDER BY secondary_comment_id ASC",(movieid,comments[6]))
				record = cur.fetchall()
				a = list(comments)
				a.insert(8,record)
				a.insert(9,len(record))
				comment[i] = tuple(a)
				i = i + 1
		context_dict['length'] = len(comment)
		context_dict['comment'] = comment
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return render_to_response('movies/movies.html', context_dict, context)	

def update(request,movieid):
	context = RequestContext(request)
	if request.method == 'GET':
		rate = request.GET['rate']
		if request.user.is_authenticated():
			profile = UserProfile.objects.get(user = request.user)
			userid = (profile.user_id + 943 - 1)
			con = None
			try:
				con = psycopg2.connect(database='project',user='postgres')
				cur = con.cursor()
				cur.execute("select * from movies_rated where userid = %s and movieid = %s",(userid,movieid))
				result = cur.fetchall()
				if (len(result) == 0):
					cur.execute("INSERT INTO movies_rated values(%s,%s,%s)",(userid,movieid,rate))
					con.commit()
				cur.execute("select imdbvotes,imdbrating from movies where movieid = %s",(movieid,))
				result = cur.fetchone()
				res = str(result[0]) + '\n' + str(result[1]) 
			except psycopg2.DatabaseError, e:
				if con:
					con.rollback()
				print 'Error %s' %e
				sys.exit(1)
			finally:
				if con:
					con.close()
			return hr(res) 

def post_comment(request,movieid):
	if request.method == 'GET':
		comment = request.GET['check']
		localtime = time.asctime( time.localtime(time.time()))
		comment1 = '{'+comment+'}'
		localtime1 = '{' + localtime + '}'
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("INSERT INTO comments values (%s,%s,%s,%s,%s,%s)",(movieid,request.user.id,comment1,localtime1,'http://127.0.0.1:8000/movies/',0,))
			con.commit()
			cur.execute("select comment_id from comments where userid = %s and date = %s",(request.user.id,localtime1));
			comment_id = cur.fetchone()[0]
			dic = { "comment" : comment, "time" : localtime, "first" : request.user.first_name, "last" : request.user.last_name, "id" : comment_id }
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr(json.dumps([dic]))
		
def edit_comment_history(request):
	new = []
	if request.method == 'GET':
		commentid = request.GET['commentid']
		status = request.GET['status']
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if (status == 'primary'):
				cur.execute("Select comment,date from comments where comment_id = %s",(commentid,))
			else:
				cur.execute("Select comments,date from secondary_comments where secondary_comment_id = %s",(commentid,))
			comment = cur.fetchall()
			for comments in comment:
				for j in range(len(comments[0])):
					s = comments[1][j]
					s = json.dumps(s, cls = MyEncoder)
					l = { "comment" : comments[0][j], "date" : s } 
					new = new + [l]
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
	return hr(json.dumps(new))

def show_liked_people(request):
	comment_id = request.GET['commentid']
	stat = request.GET['status']
	status = []
	final = []
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		if (stat == 'primary'):
			cur.execute("select picture,userid from movies_userprofile,comment_like where comment_id = %s and comment_like.userid = movies_userprofile.user_id",(comment_id,))
		else:
			cur.execute("select picture,userid from movies_userprofile,secondary_comment_like where secondary_comment_id = %s and secondary_comment_like.userid = movies_userprofile.user_id",(comment_id,))
		result = cur.fetchall()
		for results in result:
			user = User.objects.get(id = results[1])
			try:
				status = user.follow.follower.filter(username = request.user.username)
			except:
				status = []
			cur.execute("select count(*) from movies_follow where user_id = %s",(results[1],))
			res = cur.fetchone()[0]
			total = 0
			if (res != 0):
				total = user.follow.follower.count()
			if (len(status) != 0):
				l = { "username" : user.username, "first" : user.first_name , "last" : user.last_name, "status" : "YES" , "picture" : results[0] , "total" : total }
			else:
				if (user == request.user):
					l = { "username" : user.username, "first" : user.first_name , "last" : user.last_name, "status" : "SAME" , "picture" : results[0] , "total" : total }
				else:
					l = { "username" : user.username, "first" : user.first_name , "last" : user.last_name, "status" : "NO" , "picture" : results[0] , "total" : total }
			final = final + [l]
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return hr(json.dumps(final)) 		

def do_comment(request):
	if request.method == 'GET':
		comment = request.GET['check']
		movieid = request.GET['movieid']
		comment_id = request.GET['comment_id']
		localtime = time.asctime( time.localtime(time.time()))
		comment1 = '{'+comment+'}'
		localtime1 = '{' + localtime + '}'
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("INSERT INTO secondary_comments values (%s,%s,%s,%s,%s,%s)",(movieid,request.user.id,comment_id,comment1,localtime1,0,))
			con.commit()
			cur.execute("select secondary_comment_id from secondary_comments where userid = %s and date = %s",(request.user.id,localtime1));
			get_id = cur.fetchone()[0]
			dic = { "time" : localtime, "first" : request.user.first_name, "last" : request.user.last_name, "id" : get_id }
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr(json.dumps([dic]))

def delete_comment(request):
	if request.method == 'GET':
		comment_id = request.GET['id']
		status = request.GET['status']
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if (status == 'primary'):
				cur.execute("delete from comments where comment_id = %s" % (comment_id,))
				cur.execute("delete from comment_like where comment_id = %s" % (comment_id,))
				cur.execute("delete from secondary_comments where comment_id = %s" % (comment_id,))
				cur.execute("delete from secondary_comment_like where comment_id = %s" % (comment_id,))
			else:
				cur.execute("delete from secondary_comments where secondary_comment_id = %s" % (comment_id,))
				cur.execute("delete from secondary_comment_like where secondary_comment_id = %s" % (comment_id,))
			con.commit()
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr("done")

def like_comment(request):
	if request.method == 'GET':
		likes = 0
		movie_id = request.GET['movie_id']
		comment_id = request.GET['comment_id']
		status = request.GET['status']
		var_id = request.GET['id']  
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if (status == 'primary'):
				cur.execute("update comments set upvotes = upvotes + 1 where comment_id = %s" % (comment_id,))
				cur.execute("insert into comment_like values (%s,%s,%s)",(movie_id,request.user.id,comment_id))
				con.commit()
				cur.execute("select upvotes from comments where comment_id = %s", (comment_id,))
			else:
				cur.execute("update secondary_comments set upvotes = upvotes + 1 where secondary_comment_id = %s" % (comment_id,))
				cur.execute("insert into secondary_comment_like values (%s,%s,%s,%s)",(movie_id,request.user.id,comment_id,var_id))
				con.commit()
				cur.execute("select upvotes from secondary_comments where secondary_comment_id = %s", (comment_id,))
			likes = cur.fetchone()[0] 
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr(likes);

def unlike_comment(request):
	if request.method == 'GET':
		likes = 0
		movie_id = request.GET['movie_id']
		comment_id = request.GET['comment_id']
		status = request.GET['status']
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if (status == 'primary'):
				cur.execute("update comments set upvotes = upvotes - 1 where comment_id = %s" % (comment_id,))
				cur.execute("delete from comment_like where movieid = %s and userid = %s and comment_id = %s" % (movie_id,request.user.id,comment_id))
				con.commit()
				cur.execute("select upvotes from comments where comment_id = %s", (comment_id,))
			else:
				cur.execute("update secondary_comments set upvotes = upvotes - 1 where secondary_comment_id = %s" % (comment_id,))
				cur.execute("delete from secondary_comment_like where movieid = %s and userid = %s and secondary_comment_id = %s" % (movie_id,request.user.id,comment_id))
				con.commit()
				cur.execute("select upvotes from secondary_comments where secondary_comment_id = %s", (comment_id,))
			likes = cur.fetchone()[0] 
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr(likes)
			
def edit_comment(request):
	if request.method == 'GET':
		comment = request.GET['check']
		comment_id = request.GET['id']
		print comment_id
		status = request.GET['status']
		localtime = time.asctime( time.localtime(time.time()))
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if status == 'primary':
				cur.execute("update comments set comment = array_prepend('%s',comment) where comment_id = %s" % (comment,comment_id,))
				cur.execute("update comments set date = array_prepend('%s',date) where comment_id = %s" % (localtime,comment_id,))
				con.commit()
			else:
				cur.execute("update secondary_comments set comments = array_prepend('%s',comments) where secondary_comment_id = %s" % (comment,comment_id,))
				cur.execute("update secondary_comments set date = array_prepend('%s',date) where secondary_comment_id = %s" % (localtime,comment_id,))
				con.commit()
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr("yo")

def get_movies(act):
	answer = ""
	for acts in act:
		answer = answer + acts[0] + '\n'
	return answer

def suggestion(request):
	context = RequestContext(request)
	movies = ""
	if request.method == 'GET':
		get = request.GET['suggestion']
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("SELECT title from movies where title ~* '%s'" % (get,))
			act = cur.fetchall()
			movies = get_movies(act)
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
	return hr(movies)

def get_user(act):
	answer = ""
	for acts in act:
		answer = answer + acts[3] + "    " + acts[2] + "    " + acts[0] + " " + acts[1] + '\n'
	return answer

def user(request):
	context = RequestContext(request)
	user = ""
	if request.method == 'GET':
		get = request.GET['suggestion']
		res = request.GET['res']
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if res == "NO":
				cur.execute("SELECT first_name,last_name,picture,username from auth_user,movies_userprofile where first_name ~* '%s' and is_superuser = 'f' and auth_user.id = movies_userprofile.user_id" % (get,))
				act = cur.fetchall()[:5]
				user = get_user(act)
			else:
				get = get.split()
				cur.execute("SELECT username from auth_user where first_name ~* '%s' and is_superuser = 'f'" % (get[0],))
				act = cur.fetchone()
				if act == None:
					user = "NONE"
				else:
					user = act[0]
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
	return hr(user)

def director(request,director):
	context = RequestContext(request) 
	con = None
	context_dict = {}
	get_director = director.replace('_',' ')
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		cur.execute("SELECT * from movies where director=%s",(get_director,))
		ver = cur.fetchall()
		ver = change(ver)
		context_dict['movie'] = ver
		context_dict['decide'] = "director"
		if request.user.is_authenticated():
			profile = UserProfile.objects.get(user = request.user)
			context_dict['profile'] = profile
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return render_to_response('movies/answer.html', context_dict, context)

def actor(request,actor):
	context = RequestContext(request) 
	con = None
	context_dict = {}
	get_actor = actor.replace('_',' ')
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		cur.execute("SELECT * from movies,actors where actors.movieid = movies.movieid and actors=%s",(get_actor,))
		act = cur.fetchall()
		context_dict['get_actor'] = get_actor
		context_dict['decide'] = "actor"
		act = change(act)
		context_dict['movie'] = act
		if request.user.is_authenticated():
			profile = UserProfile.objects.get(user = request.user)
			context_dict['profile'] = profile
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return render_to_response('movies/answer.html', context_dict, context)

def genre(request,genre):
	context = RequestContext(request) 
	con = None
	context_dict = {}
	try:
		con = psycopg2.connect(database='project',user='postgres')
		cur = con.cursor()
		cur.execute("SELECT * from movies,genre where genre.movieid = movies.movieid and genre = %s ORDER BY RANDOM() LIMIT 20",(genre,))
		act = cur.fetchall()
		act = change(act) 
		context_dict['genre'] = genre
		context_dict['movie'] = act
		context_dict['decide'] = "genre"
		if request.user.is_authenticated():
			profile = UserProfile.objects.get(user = request.user)
			context_dict['profile'] = profile
	except psycopg2.DatabaseError, e:
		if con:
			con.rollback()
		print 'Error %s' %e
		sys.exit(1)
	finally:
		if con:
			con.close()
	return render_to_response('movies/answer.html', context_dict, context)

def send_email(you,html,image,subject):
	me = 'vijender4312@gmail.com'
	you = you	
	msgRoot = MIMEMultipart('related')
	msgRoot['Subject'] = subject
	msgRoot['From'] = me
	msgRoot['To'] = you
	msgAlternative = MIMEMultipart('alternative')
	msgRoot.attach(msgAlternative)
	msgText = MIMEText(html, 'html')
	msgAlternative.attach(msgText)
	fp = open(image,'rb')
	msgImage = MIMEImage(fp.read())
	fp.close()
	msgImage.add_header('Content-ID', '<image1>')
	msgRoot.attach(msgImage)
	s = smtplib.SMTP('smtp.gmail.com:587')
	s.ehlo()
	s.starttls()
	s.login('vijender4312@gmail.com', 'sirsa654321')
	s.sendmail(me, you, msgRoot.as_string())
	s.quit()

def unfollow(request):
	context = RequestContext(request)
	if request.method == 'GET':
		name = request.GET['unfollow']
		user = User.objects.get(username = name)
		con = None
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			cur.execute("select id from auth_user where username = %s", (name,))
			search_user = cur.fetchall()
			cur.execute("select id from auth_user where username = %s", (request.user.username,))
			login_user = cur.fetchall()
			follower = None
			try:
				follower = user.follow.follower.all();
			except:
				follower = []
			if (len(follower) > 1):
				cur.execute("select movies_follow_follower.id from movies_follow_follower,movies_follow where movies_follow.user_id = %s and movies_follow.id = follow_id and movies_follow_follower.user_id = %s", (search_user[0],login_user[0],))
				res = cur.fetchall()
				cur.execute("delete from movies_follow_follower where id = %s",(res[0],))
				con.commit()
			elif (len(follower) == 1):
				cur.execute("select movies_follow_follower.id from movies_follow_follower,movies_follow where movies_follow.user_id = %s and movies_follow.id = follow_id and movies_follow_follower.user_id = %s", (search_user[0],login_user[0],))
				res = cur.fetchall()
				cur.execute("delete from movies_follow_follower where id = %s",(res[0],))
				cur.execute("delete from movies_follow where user_id = %s",(search_user[0],))
				con.commit()
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return hr("DONE")	

def follow(request):
	context = RequestContext(request)
	if request.method == 'GET':
		name = request.GET['follow']
		i = User.objects.get(username = name)
		follower = None
		try:
			follower = i.follow.follower.all();
		except:
			follower = []
		if (len(follower) > 0):
			i.follow.follower.add(request.user)
			i.save()
		else:
			foo = Follow()
			foo.user = i
			foo.save()
			foo.follower.add(request.user)
			foo.save()
		pic = UserProfile.objects.get(user = request.user).picture
		link = 'http://127.0.0.1:8000/movies/profile/'+request.user.username
		html = """
<html>
	<div style='background-color: 9999FF; color : white; width : 550px; height : 25px'>
		<span style='font-size : 20px; padding: 3cm 3cm 3cm 3cm; margin-left : 60px'>DIRECTOR's CUT</span>
	</div>
	<div style='float : left; margin-top : 10px'><img src='cid:image1' width='100' height='100'>
	</div>
	<div style="font-size : 12px; font-family:LucidaGrande,tahoma,verdana,arial,sans-serif; margin-left : 120px; margin-top : 15px">
		Hi 
		<b> %s ,</b><br>
		<a href="%s"> %s %s</a> is now following you on DIRECTOR's CUT.<br>
	</div>
	<span style='float : left; font-size : 12px; font-family:LucidaGrande,tahoma,verdana,arial,sans-serif; margin-left : 20px; margin-top : 20px'> 
		Thanks,<br>DIRECTOR's CUT Team
	</span>
</html>
""" %(i.first_name,link,request.user.first_name,request.user.last_name)
		image = '/home/vijender/workspace/DBMS/media/' + str(pic)
		subject = request.user.first_name + " " + request.user.last_name + " is now following you on DIRECTOR's CUT"
		send_email(i.email,html,image,subject)	
		return hr("DONE")

@login_required
def reset(request,reset):
	context = RequestContext(request)
	context_dict = {}
	if (reset == "password"):
		context_dict['reset'] = reset
		if request.method == 'POST':
			current = request.POST['current']
			new = request.POST['now']
			if (request.user.check_password(current) == True):
				localtime = time.asctime( time.localtime(time.time()) ) 
				pic = UserProfile.objects.get(user = request.user).picture
				image = '/home/vijender/workspace/DBMS/media/' + str(pic)
				user_agent = request.META['HTTP_USER_AGENT'].split('/')[2].split(' ')[1]
				html = "<div style='background-color: 9999FF; color : white; width : 550px; height : 25px'><span style='font-size : 20px; padding: 3cm 3cm 3cm 3cm; margin-left : 60px'>DIRECTOR's CUT</span></div>"+"<div style='float : left; margin-top : 10px'><img src='cid:image1' width='100' height='100'></div><div style='float : left; font-size : 12px; font-family: LucidaGrande,tahoma,verdana,arial,sans-serif; margin-left : 30px; margin-top : 10px'>"+"Hi <b>"+ request.user.first_name +",</b><br>Your DIRECTOR's CUT password was changed on <b>"+ localtime +"</b><br><br><span style='color : grey; margin-left : 30px'>Operating System </span> <b>&nbsp; :</b> "+ platform.system() + "<br><span style='color : grey; margin-left : 30px'>Browser </span><span style='margin-left : 52px'> <b>&nbsp; : </b>"+ user_agent +"</span><br><br><span style='position : absolute; left : 140px'><b>If you did this,</b> you can safely disregard this email</span><br><span style='margin-top :5px;'><b>If you did n't do this,</b> please <a href='http://127.0.0.1:8000/movies/sure/password/reset/'>secure your account.</span></a></div><div style='clear : both; float : left; margin-left : 130px; font-size : 12px; font-family : LucidaGrande,tahoma,verdana,arial,sans-serif; margin-top : 10px'> Thanks,<br><b>Vijender</b><br>CEO, DIRECTOR's CUT</div>"
				send_email(request.user.email,html,image,'Password Changed')
				request.user.set_password(new)
				request.user.save()
				return hr("1")
			else:
				return hr("2")
		else:
			context_dict['user'] = request.user.username
			return render_to_response('movies/reset.html', context_dict, context)
	else:
		context_dict['reset'] = reset
		if request.method == 'POST':
			email = request.POST['email']
			if (email == request.user.email):
				first = request.POST['first']
				last = request.POST['last']
				age = request.POST['age']
				zipcode = request.POST['zipcode']
				occupation = request.POST['occupation']
				interest = request.POST['checked']
				userid = (request.user.id + 943 - 1)
				try:
					con = psycopg2.connect(database='project',user='postgres')
					cur = con.cursor()
					cur.execute("update movies_userprofile set age = %s, zipcode = %s, occupation = %s, interest = %s where user_id = %s", (age,zipcode,occupation,interest,request.user.id))
					cur.execute("update user_profile set age = %s, zipcode = %s, occupation = %s where userid = %s", (age,zipcode,occupation,userid))
					cur.execute("update auth_user set first_name = %s, last_name = %s, email = %s where id = %s", (first,last,email,request.user.id))
					con.commit()
				except psycopg2.DatabaseError, e:
					if con:
						con.rollback()
					print 'Error %s' %e
					sys.exit(1)
				finally:
					if con:
						con.close()
				return hr(json.dumps("done"))
			else:	
				user_email = User.objects.filter(email = email)
				if (len(user_email)>0):
					return hr(json.dumps("EMAIL"))
		else:
			context_dict['user'] = request.user
			pro = UserProfile.objects.get(user = request.user)
			context_dict['profile']=pro
			try:
				con = psycopg2.connect(database='project',user='postgres')
				cur = con.cursor()
				cur.execute("select interest from movies_userprofile where user_id = %s", (request.user.id,))
				interest = cur.fetchone()
				context_dict['interest'] = interest[0].split(',')
			except psycopg2.DatabaseError, e:
				if con:
					con.rollback()
				print 'Error %s' %e
				sys.exit(1)
			finally:
				if con:
					con.close()
			return render_to_response('movies/reset.html', context_dict, context)
	
def login(request):
	context = RequestContext(request)
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username = username,password = password)
		if user is not None:
			if user.is_active:
				auth_login(request,user)
				return hr(user.username) 
			else:
				return hr("2")
		else:
			return hr("3") 
	else:
		if request.user.is_authenticated():
			return HttpResponseRedirect("/movies/profile/"+request.user.username)
		else:
			login_form = LoginForm()
			context_dict = {'login_form': login_form }
			return render_to_response("movies/login.html",context_dict,context)	

res = ""
def create(s1,s2,s3,s4,s5,s6):
	l = []
	global res
	res = ""
	if (s1 != "title ~* ''"):
		l = l + [s1]
		res = res+' '+s1.replace('~*','=')
	if (s2 != "year = "):
		l = l + [s2]
		res = res + ' '+s2
	if (s3 != "imdbrating >= "):
		l = l + [s3]
		res = res + ' '+s3
	if (s4 != "imdbvotes >= "):
		l = l + [s4]
		res = res + ' '+s4
	if (s5 != "genre ~* ''"):
		l = l + [s5]
		res = res + ' '+s5.replace('~*','=')
	if (s6 != "actors ~* ''"):
		l = l + [s6]
		res = res + ' '+s6.replace('~*','=')
	return l

def convert(s):
	return unicodedata.normalize('NFKD', s).encode('ascii','ignore') 

def generate(l,s):
	 for i in range(len(l)):
		 s = s + " " + l[i] + " and"
	 return s[:-4]
	
def add(request):
	context = RequestContext(request)
	context_dict = {}
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)
		context_dict['profile'] = profile
	if request.method == 'POST':
		movie = request.POST['movie']  
		year = request.POST['year']
		rating = request.POST['imdbrating']  
		votes = request.POST['imdbvotes']
		genre = request.POST['genre']
		actor = request.POST['actor']
		con = None
		s1 = "title ~* '%s'" % (movie)
		s2 = "year = "+convert(year)
		s3 = "imdbrating >= "+convert(rating)
		s4 = "imdbvotes >= "+convert(votes)
		s5 = "genre ~* '%s'" % (genre)
		s6 = "actors ~* '%s'" % (actor)
		if (movie == "" and year == "" and rating == "" and votes == "" and actor == "" and genre == "" ):
			return render_to_response("movies/check.html",context_dict,context)
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			if (actor != "" and genre != ""):
				s = "SELECT * from movies,genre,actors where genre.movieid = movies.movieid and genre.movieid=actors.movieid and"
			elif (actor != "" or genre != ""):
				if (actor != ""):
					s = "SELECT * from movies,actors where actors.movieid = movies.movieid and"
				elif (genre != ""):
					s = "SELECT * from movies,genre where genre.movieid = movies.movieid and"
			elif (movie != "" or year != "" or rating != "" or votes != ""):
				s = "select * from movies where" 
			l = create(s1,s2,s3,s4,s5,s6)
			query = generate(l,s) + "LIMIT 100"
			cur.execute(query)
			act = cur.fetchall()
			act = change(act)
			context_dict['search'] = res
			context_dict['movie'] = act
			if request.user.is_authenticated():
				profile = UserProfile.objects.get(user = request.user)	
				context_dict['profile'] = profile
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
		return render_to_response("movies/answer.html",context_dict,context)
	else:
		return render_to_response("movies/check.html",context_dict,context)

def trans(request):
	context = RequestContext(request)
	context_dict = {}
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)	
		context_dict['profile'] = profile
		con=None
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			userid = (profile.user_id + 943 - 1)
			cur.execute("SELECT title,year,price,issold,buyer from movies,transaction where transaction.movieid = movies.movieid and seller = %s",(userid,))
			act = cur.fetchall()
			context_dict['movie'] = act
			cur.execute("SELECT title,year,price,seller from movies,transaction where transaction.movieid = movies.movieid and buyer = %s",(userid,))
			act = cur.fetchall()
			context_dict['collection'] = act
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()
	return render_to_response("movies/trans.html",context_dict,context)

def get(request):
	context = RequestContext(request)
	l = []
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)	
		if request.method == 'GET':
			movie = request.GET['search']
			try:
				con = psycopg2.connect(database='project',user='postgres')
				cur = con.cursor()
				userid = (profile.user_id + 943 - 1)
				cur.execute("SELECT title,year,seller,price,transid from movies,transaction where title ~* %s and movies.movieid = transaction.movieid and issold = 0",(movie,))
				ver = cur.fetchall()
				for var in ver:
					dic = { "title" : var[0], "year" : var[1], "seller" : var[2], "price" : var[3], "transid" : var[4] }
					l = l + [dic]
			except psycopg2.DatabaseError, e:
				if con:
					con.rollback()
				print 'Error %s' %e
				sys.exit(1)
			finally:
				if con:
					con.close()
	return hr(json.dumps(l))

def final(request,transid):
	context = RequestContext(request)
	context_dict = {}
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)	
		context_dict['profile'] = profile
		if request.method == 'POST':
			try:
				con = psycopg2.connect(database='project',user='postgres')
				cur = con.cursor()
				userid = (profile.user_id + 943 - 1)
				if 'submit' in request.POST:
					cur.execute("select issold from transaction where transid = %s",(transid,))
					ver=cur.fetchall()
					if (ver[0] == 1):
						print "Not Possible"
					else:
						cur.execute("UPDATE TRANSACTION SET issold = 1 where transid = %s",(transid,))
						con.commit()
				if 'cancel' in request.POST:
					cur.execute("select issold from transaction where transid = %s",(transid,))
					ver=cur.fetchall()
					if (ver[0] == 1):
						print "Not Possible"
					else:
						cur.execute("UPDATE TRANSACTION SET buyer = -1 where transid = %s",(transid,))
						con.commit()
			except psycopg2.DatabaseError, e:
				if con:
					con.rollback()
				print 'Error %s' %e
				sys.exit(1)
			finally:
				if con:
					con.close()	
	return Profile(request,request.user.username)
	
def transaction(request,transid):
	context = RequestContext(request)
	context_dict = {}
	if request.user.is_authenticated():
		profile = UserProfile.objects.get(user = request.user)	
		context_dict['profile'] = profile
		try:
			con = psycopg2.connect(database='project',user='postgres')
			cur = con.cursor()
			userid = (profile.user_id + 943 - 1)
			cur.execute("SELECT title,year,seller,price,picture,transid from movies,transaction where transid = %s and movies.movieid = transaction.movieid",(transid,))
			ver = cur.fetchall()
			context_dict['movie'] = ver
			cur.execute("BEGIN;")
			cur.execute("UPDATE TRANSACTION SET buyer = %s where transid = %s ;",(userid,transid))
			con.commit()
		except psycopg2.DatabaseError, e:
			if con:
				con.rollback()
			print 'Error %s' %e
			sys.exit(1)
		finally:
			if con:
				con.close()	
	return render_to_response("movies/transaction.html",context_dict,context)
		
@login_required
def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/movies/')
