#!/usr/bin/python
"""
"""

import sys
import redis
import string
import regex as re
import raven
import twitter

from raven import Client

client = Client('https://ad7b9867c209488da9baa4fbae04d8f0:b63c0acd29eb40269b52d3e6f82191d9@sentry.io/144998')

#
# api = twitter.Api(consumer_key=[consumer key],
#                   consumer_secret=[consumer secret],
#                   access_token_key=[access token],
#                   access_token_secret=[access token secret])

r = redis.StrictRedis(host='localhost', port=6379, db=0)

parsername = "nyt.NYTParser"

try:
    url = sys.argv[1]
except IndexError:
    url = None

module, classname = parsername.rsplit('.', 1)
parser = getattr(__import__(module, globals(), fromlist=[classname]), classname)

def tweet_word(word):
    if int( r.get("recently") or 0 ) < 3:
        r.incr("recently")
        r.expire("recently", 60 * 30)
        print word
        status = api.PostUpdate(word)
        print "%s just posted: %s" % (status.user.name, status.text)

def ok_word(s):
    return (not any(i.isdigit() for i in s)) and s.islower()

def remove_punctuation(text):
    return re.sub(ur"\p{P}+", "", text)

def process_article(content):
    text = unicode(content)
    words = text.split()
    for raw_word in words:
        if ok_word(raw_word):
            word = remove_punctuation(raw_word)
            if len(word) + 1 < len(raw_word):
                continue
            wkey = "word:" + word
            if not r.get(wkey):
                tweet_word(word)
                r.set(wkey, '1')

links = parser.feed_urls()
for link in links:
    akey = "article:"+link
    if not r.get(akey):
        parsed_article = parser(link)
        process_article(parsed_article)
        r.set(akey, '1')
