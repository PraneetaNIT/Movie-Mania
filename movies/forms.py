from django import forms
from django.contrib.auth.models import User
from movies.models import UserProfile, Change, Message

class UserForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput())
	class Meta:
		model = User
		fields = ('username','first_name','last_name','email','password')

class UserProfileForm(forms.ModelForm):
	sex = forms.CharField(max_length=8)
	occupation = forms.CharField(max_length=40 )
	zipcode = forms.CharField(max_length=20)
	age = forms.IntegerField()
	class Meta:
		model = UserProfile
		fields = ('sex','age','occupation','zipcode','picture')
	
class LoginForm(forms.ModelForm):
	username = forms.CharField(max_length = 128)
	password = forms.CharField(widget=forms.PasswordInput())		
	class Meta:
		model = User
		fields = ('username','password')
		
class Changed(forms.ModelForm):
	class Meta:
		model = Change
		fields = ('picture',)
