import tweepy
import yaml

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

def addAccount():
    auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
    auth.get_authorization_url()
    verifier = ''
    auth.get_access_token(verifier)

if __name__ == '__main__':
    ...
    # addAccount()

