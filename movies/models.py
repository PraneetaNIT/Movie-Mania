from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
#   sudo fuser -k 8000/tcp

class UserProfile(models.Model):
	user = models.OneToOneField(User)
	sex = models.CharField(max_length=8)
	age = models.IntegerField(default=0)
	occupation = models.CharField(max_length = 40)
	zipcode = models.CharField(max_length = 20)
	picture = models.ImageField(upload_to='profile_images',blank=True)
	def __unicode__(self):
		return self.user.username

class Change(models.Model):
	picture = models.ImageField(upload_to='profile_images',blank=True)
	def __unicode__(self):
		return self.picture
		
class Follow(models.Model):
	user = models.OneToOneField(User)
	follower = models.ManyToManyField(User,related_name='following',symmetrical=False)
	# user.following.all()
	def __unicode__(self):
		return self.user.username

class Message(models.Model):
	msg = models.TextField(_("Message"))
	sender = models.ForeignKey(User, related_name='sent_messages', verbose_name=_("Sender"))
	recipient = models.ForeignKey(User, related_name='received_messages', null=True, blank=True, verbose_name=_("Recipient"))
	sent_at = models.DateTimeField(_("sent at"), default=timezone.now)
	read_at = models.DateTimeField(_("read at"), null=True, blank=True)
	replied_at = models.DateTimeField(_("replied at"), null=True, blank=True)
	sender_deleted = models.BooleanField(default=False)
	recipient_deleted = models.BooleanField(default=False)
