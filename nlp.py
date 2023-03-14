import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import math 

def get_sentiment_score(text):
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(text)
    sentiment_score = scores['compound']
    return int((sentiment_score + 1) / 2 * 100)

    # convert to log scale
    weighted_score = math.log(sentiment_score + 1)
    sentiment_percent = (weighted_score + 1) / 2 * 100
    return int(sentiment_percent)
