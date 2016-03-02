from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect

from . models import Wine, Review, Cluster
from . forms import ReviewForm
from . suggestions import update_clusters

import datetime

# Create your views here.
def review_list(request):
	# gets a list of the latest 9 reviews
	latest_review_list = Review.objects.order_by('-pub_date')[:9]
	context = {'latest_review_list':latest_review_list}
	return render(request, 'reviews/review_list.html', context)

def review_detail(request, review_id):
	review = get_object_or_404(Review, pk=review_id)
	context = {'review':review}
	return render(request, 'reviews/review_detail.html', context)

def wine_list(request):
	wine_list = Wine.objects.order_by('-name')
	context = {'wine_list':wine_list}
	return render(request, 'reviews/wine_list.html', context)

def wine_detail(request, wine_id):
	wine = get_object_or_404(Wine, pk=wine_id)
	form = ReviewForm
	context = {'wine': wine}
	context['form'] = form
	return render(request, 'reviews/wine_detail.html', context)

@login_required
def add_review(request, wine_id):
	wine = get_object_or_404(Wine, pk=wine_id)
	form = ReviewForm(request.POST)
	if form.is_valid():
		rating = form.cleaned_data['rating']
		comment = form.cleaned_data['comment']
		# user_name = form.cleaned_data['user_name']
		user_name = request.user.username
		review = Review()
		review.wine = wine
		# review.user_name = user_name
		review.rating = rating
		review.comment = comment
		review.pub_date = datetime.datetime.now()
		review.save()
		# declared in suggestions.py (same folder)
		update_clusters()
		# Always return an HttpResponseRedirect after successfully dealing
		# with POST data. This prevents data from being posted twice if a
		# user hits the Back button.

		# form.save()
		return HttpResponseRedirect(reverse('reviews:wine_detail', args=(wine.id,)))
	return render(request, 'reviews/wine_detail.html', {'wine':wine, 'form':form})

def user_review_list(request, username=None):
	if not username:
		username = request.user.username
	latest_review_list = Review.objects.filter(user_name=username).order_by('-pub_date')
	context = {'latest_review_list':latest_review_list, 'username':username}
	return render(request, 'reviews/user_review_list.html', context)

# Return a list of wine recommendation for that user
# Basically:
# We get the reviews of the logged-in user's friends, lambdas are used to get their ids for better filtering on the objects
# Exclude the review of the current user so only his' friends reviews are included
# Return the wine that was reviewed and sort it by average rating
@login_required
def user_recommendation_list(request):
	# get this user reviews
	user_reviews = Review.objects.filter(user_name=request.user.username).prefetch_related('wine')
	# from the reviews, get a set of wine IDs
	# Simple gets the ids of all wine objects in a list of the user_reviews
	user_reviews_wine_ids = set(list(map(lambda x: x.wine.id, user_reviews)))
	
	# get request user cluster name (just the first one right now)
	# try-except clause is used in order to deal with non-existing cluster assignments for a user when getting the first cluster
	try:
		user_cluster_name = User.objects.get(username=request.user.username).cluster_set.first().name
	except:
		update_clusters()
		user_cluster_name = User.objects.get(username=request.user.username).cluster_set.first().name

	# get usernames for other members of the cluster
	user_cluster_other_members = Cluster.objects.get(name=user_cluster_name).users.exclude(username=request.user.username).all()
	other_members_usernames = set(list(map(lambda x: x.username, user_cluster_other_members)))

	# get reviews by those users, excluding wines reviewed by the request user
	other_users_reviews = Review.objects.filter(user_name__in=other_members_usernames).exclude(wine__id__in=user_reviews_wine_ids)
	other_users_reviews_wine_ids = set(list(map(lambda x: x.wine.id, other_users_reviews)))


	# then get a wine list excluding the previous IDs
	# A list of wine with sorted average rate
	wine_list = sorted(
		Wine.objects.filter(id__in=other_users_reviews_wine_ids),
		key=lambda x: x.average_rating(),
		reverse=True
	)
	context = {'username':request.user.username}
	# the wine list will be a list of wines that were not reviewed by the logged-in user
	context['wine_list'] = wine_list
	return render(request, 'reviews/user_recommendation_list.html', context)