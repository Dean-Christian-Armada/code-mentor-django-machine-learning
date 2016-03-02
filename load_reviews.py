import sys, os
import pandas as pd
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "winerama.settings")
import django
django.setup()

# Setup Django first before running this
from reviews.models import Review, Wine

# Saves from reviews.csv to the review model
def save_review_from_row(review_row):
	review = Review()
	review.id = review_row[0]
	review.user_name = review_row[1]
	# This can be an error if you gave not imported the wines yet
	review.wine = Wine.objects.get(id=review_row[2])
	review.rating = review_row[3]
	review.pub_date = datetime.datetime.now()
	review.comment = review_row[4]
	review.save()

if __name__=='__main__':
	# Check number of arguments (including the command name)
	if len(sys.argv) == 2:
		print ("Reading from file " + str(sys.argv[1]))
		# reviews the csv through pandas read_csv method
		reviews_df = pd.read_csv(sys.argv[1])
		print (reviews_df)

		# apply save_review_from_row to each review in the data frame
		# axis = 1 means per row and y-axis
		reviews_df.apply(
			save_review_from_row,
			axis=1
		)
		print ("There are {} reviews in DB".format(Review.objects.count()))
	else:
		print ("Please, provide Reviews file path")