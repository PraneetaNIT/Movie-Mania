from django.conf.urls import *
from movies import views
from django.conf import settings

urlpatterns = patterns('',
       url(r'^$', views.home, name='home'),
       url(r'^register/$',views.register,name='register'),
       url(r'^login/$',views.login,name = 'login'),
       url(r'^view_all_message/$',views.view_all_message ,name = 'view_message'),
       url(r'^message/(?P<name>\w+)/$',views.view_user_message ,name = 'user_message'),
       url(r'^message/$',views.save_message ,name = 'message'),
       url(r'^latest_updates/$',views.latest_updates, name = 'updates'),
       url(r'^profile/(?P<name>\w+)/$',views.Profile,name='profile'),
       url(r'^logout/$', views.logout, name="logout"),
       url(r'^add/$', views.add, name='add'),
       url(r'^get/$', views.get, name='get'),
       url(r'^follow/$', views.follow, name='follow'),
       url(r'^unfollow/$', views.unfollow, name='unfollow'),
       url(r'^remove_picture/$', views.no_picture, name='no_picture'),
       url(r'^changed/$', views.change_profile, name='change'),
       url(r'^facebook_profile/$', views.facebook_profile, name='facebook_profile'),
       url(r'^suggestion/$', views.suggestion, name='suggestion'),
       url(r'^user/$', views.user, name='user'),
       url(r'^reset/(?P<reset>\w+)/$', views.reset, name='reset'),
	   url(r'^transaction/$', views.trans, name='trans'),
	   url(r'^final/(?P<transid>\w+)/$', views.final, name='final'),
	   url(r'^sell/(?P<transid>\w+)/$', views.transaction, name='transaction'),
       url(r'^view/(?P<top>\w+)/$', views.top100, name='top'),
       url(r'^comment/post/(?P<movieid>\w+)/$', views.post_comment, name='post'),
       url(r'^comment/edit_history/$', views.edit_comment_history, name='history'),
       url(r'^comment/comment/$', views.do_comment, name='comment'),
       url(r'^comment/edit/$', views.edit_comment, name='edit'),
       url(r'^comment/like/$', views.like_comment, name='like'),
       url(r'^comment/unlike/$', views.unlike_comment, name='unlike'),
       url(r'^comment/show_likes/$', views.show_liked_people, name='show_like'),
       url(r'^comment/delete/$', views.delete_comment, name='delete'),
	   url(r'^director/(?P<director>[A-Z a-z . _ -]+)/$', views.director, name='director'),
	   url(r'^actor/(?P<actor>[A-Z a-z . _ -]+)/$', views.actor, name='actor'),
	   url(r'^genre/(?P<genre>[A-Z a-z . _ -]+)/$', views.genre, name='genre'),
	   url(r'^rate/(?P<movieid>\w+)/$',views.update, name='update'),
       url(r'^sure/password/reset/$', 'django.contrib.auth.views.password_reset', {'post_reset_redirect' : '/movies/password/reset/done/'}, name="password_reset"),
       url(r'^password/reset/done/$', 'django.contrib.auth.views.password_reset_done'),
       url(r'^password/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm',{'post_reset_redirect' : '/movies/sure/password/done/'}),
       url(r'^sure/password/done/$', 'django.contrib.auth.views.password_reset_complete'),
	   url(r'^(?P<movieid>\w+)/$', views.movies, name='movie'),
       url(r'^(?P<name>\w+)/(?P<follow>\w+)/$', views.display_follow, name='display_follow'),
)

if settings.DEBUG:
        urlpatterns += patterns(
                'django.views.static',
                (r'media/(?P<path>.*)',
                'serve',
                {'document_root': settings.MEDIA_ROOT}), )