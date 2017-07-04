import settings
import math
import nltk

THRESHOLD_DISTANCE = 7

def coord_distance(lat1, lon1, lat2, lon2):
    """
    Finds the distance between two pairs of latitude and longitude.
    :param lat1: Point 1 latitude.
    :param lon1: Point 1 longitude.
    :param lat2: Point two latitude.
    :param lon2: Point two longitude.
    :return: Kilometer distance.
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km

def in_box(coords, box):
    """
    Find if a coordinate tuple is inside a bounding box.
    :param coords: Tuple containing latitude and longitude.
    :param box: Two tuples, where first is the bottom left, and the second is the top right of the box.
    :return: Boolean indicating if the coordinates are in the box.
    """
    if box[0][0] < coords[0] < box[1][0] and box[1][1] < coords[1] < box[0][1]:
        return True
    return False

def post_listing_to_slack(sc, listing):
    """
    Posts the listing to slack.
    :param sc: A slack client.
    :param listing: A record of the listing.
    """
    desc = "{0} | {1} | {2} | {3} | <{4}>".format(listing["price"], listing["area_rank"], listing["area"], listing["name"], listing["url"])
    #desc = "{0} | {1} | {2} | <{3}>".format(listing["area"], listing["price"], listing["name"], listing["url"])

    sc.api_call(
        "chat.postMessage", channel=settings.SLACK_CHANNEL, text=desc,
        username='pybot', icon_emoji=':robot_face:'
    )



def find_points_of_interest(location):
    
    # top areas filtered as per Levenstein's distance
    areas = []

    for area in settings.NEIGHBORHOODS:
        x = [name for name in location.split(' ') if nltk.edit_distance(name.lower(), area) < 2]
        if (len(x) > 0):
            areas.append(area)

    #areas = [area for area in settings.NEIGHBORHOODS if nltk.edit_distance(area, location.lower()) < THRESHOLD_DISTANCE]

    return {
        "area_rank": ','.join(areas) 
    }