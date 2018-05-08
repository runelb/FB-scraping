import urllib.request
import json
import datetime
import csv
import time

# get your access token from here:
# https://developers.facebook.com/docs/facebook-login/access-tokens
# setup up developer is relatively quick and painless

page_id = input("Public page name:")

access_token = input("Your access token:")

def request_the_page(url):
    success = False
    while success is False:
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL", url, ":", datetime.datetime.now())
            print("Retrying...")

    return response.read()


def get_Facebook_page_feed_data(page_id, access_token, num_statuses):

    # Construct the URL string; see http://stackoverflow.com/a/37239851 for
    # Reactions parameters
    base = "https://graph.facebook.com/v2.6"                                    # NEWEST version v2.12... keep 2.6 for now
    node = "/" + page_id
    fields = "?fields=posts.limit(" + str(num_statuses) +
     "){message,link,permalink_url,created_time,type,name,id}"

    # removed from fields, may be added if required:
    # number of comments, shares and reacts
    # + "comments.limit(0).summary(true),shares,reactions.limit(0).summary(true)")

    parameters = "&access_token=" + access_token     # look at stackoverflow link above
    url = base + node + fields + parameters

    # retrieve data
    data = json.loads(request_the_page(url))

    return data


# Required for data on reactions

# def get_reactions_for_status(status_id, access_token):
#
#     # See http://stackoverflow.com/a/37239851 for Reactions parameters
#         # Reactions are only accessable at a single-post endpoint
#
#     base = "https://graph.facebook.com/v2.6"
#     node = "/%s" % status_id
#     reactions = "/?fields=" \
#             "reactions.type(LIKE).limit(0).summary(total_count).as(like)" \
#             ",reactions.type(LOVE).limit(0).summary(total_count).as(love)" \
#             ",reactions.type(WOW).limit(0).summary(total_count).as(wow)" \
#             ",reactions.type(HAHA).limit(0).summary(total_count).as(haha)" \
#             ",reactions.type(SAD).limit(0).summary(total_count).as(sad)" \
#             ",reactions.type(ANGRY).limit(0).summary(total_count).as(angry)"
#     parameters = "&access_token=%s" % access_token
#     url = base + node + reactions + parameters
#
#     # retrieve data
#     data = json.loads(request_the_page(url))
#
#     return data


def process_Facebook_page_feed_status(status, access_token):
    status_id = status['id']
    status_message = '' if 'message' not in status.keys() else status['message']
    link_name = '' if 'name' not in status.keys() else status['name']
    status_type = status['type']
    status_link = '' if 'link' not in status.keys() else status['link']
    status_permalink_url = '' if 'permalink_url' not in status.keys() else status['permalink_url']

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.
    status_published = datetime.datetime.strptime(status['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published.strftime('%Y-%m-%d %H:%M:%S')


    # comments, reacts, and shares below

    # # Nested items require chaining dictionary keys.
    #
    # num_reactions = 0 if 'reactions' not in status else \
    #         status['reactions']['summary']['total_count']
    # num_comments = 0 if 'comments' not in status else \
    #         status['comments']['summary']['total_count']
    # num_shares = 0 if 'shares' not in status else status['shares']['count']
    #
    # # Counts of each reaction separately; good for sentiment
    # # Only check for reactions if past date of implementation:
    # # http://newsroom.fb.com/news/2016/02/reactions-now-available-globally/
    #
    # reactions = get_reactions_for_status(status_id, access_token) if \
    #         status_published > '2016-02-24 00:00:00' else {}
    #
    # num_likes = 0 if 'like' not in reactions else \
    #         reactions['like']['summary']['total_count']
    #
    # # Special case: Set number of Likes to Number of reactions for pre-reaction
    # # statuses
    #
    # num_likes = num_reactions if status_published < '2016-02-24 00:00:00' \
    #         else num_likes
    #
    # def get_num_total_reactions(reaction_type, reactions):
    #     if reaction_type not in reactions:
    #         return 0
    #     else:
    #         return reactions[reaction_type]['summary']['total_count']
    #
    # num_loves = get_num_total_reactions('love', reactions)
    # num_wows = get_num_total_reactions('wow', reactions)
    # num_hahas = get_num_total_reactions('haha', reactions)
    # num_sads = get_num_total_reactions('sad', reactions)
    # num_angrys = get_num_total_reactions('angry', reactions)

    # Return a tuple of all processed data

    return (status_published, status_message, link_name, status_type, status_link, status_permalink_url, status_id)
        # taken out from return tuple, comments, shares, reacts:
        # , num_reactions, num_comments, num_shares,
        # num_likes, num_loves, num_wows, num_hahas, num_sads, num_angrys



def scrape_Facebook_page_feed_status(page_id, access_token):
    with open(page_id + '_facebook_statuses.csv', 'w') as file:
        w = csv.writer(file)
        w.writerow(["status_published", "status_message", "link_name", "status_type",
                    "status_link", "permalink_url", "status_id"])
                # removed from writerow: comments, shares, reacts
                    # , "num_reactions",
                    # "num_comments", "num_shares", "num_likes", "num_loves",
                    # "num_wows", "num_hahas", "num_sads", "num_angrys"

        has_next_page = True
        num_processed = 0
        scrape_starttime = datetime.datetime.now()

        print("Scraping", page_id, "Facebook Page:", scrape_starttime, "\n")

        statuses = get_Facebook_page_feed_data(page_id, access_token, 100)['posts']

        while has_next_page:
            for status in statuses['data']:

                # Ensure it is a status with the expected metadata
                if 'message' in status and 'created_time' in status:
                    try:
                        w.writerow(process_Facebook_page_feed_status(status, access_token))
                    except UnicodeEncodeError:
                        continue

                # output progress occasionally to make sure code is not stalling
                num_processed += 1
                if num_processed % 100 == 0:
                    print(num_processed, "statuses processed:",  datetime.datetime.now())

            # if there is no next page, we're done.
            if 'paging' in statuses:
                print("paging...")
                statuses = json.loads(request_the_page(statuses['paging']['next']))
            else:
                print("end of timeline!")
                has_next_page = False


        print("\nDone!")
        print(num_processed, "statuses processed in", datetime.datetime.now() - scrape_starttime)


if __name__ == '__main__':
    scrape_Facebook_page_feed_status(page_id, access_token)
