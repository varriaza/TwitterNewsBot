from twitter.get_tweets import parse_tweet_date

dates = [
    "Thu May 08 01:51:15 +0000 2025",
    "Tue May 06 10:09:37 +0000 2025",
    "Fri May 09 09:55:55 +0000 2025",
    "Sun May 08 16:03:03 +0000 2011",
    "Fri May 09 07:57:52 +0000 2025",
    "Sat Jul 17 15:07:50 +0000 2010",
    "Thu May 08 15:12:55 +0000 2025",
    "Tue Nov 05 13:03:06 +0000 2019",
]

for date in dates:
    parsed_date = parse_tweet_date(date)
    print(parsed_date)