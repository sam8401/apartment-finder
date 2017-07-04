#from craigslist import CraigslistHousing

import pickle as p

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import sessionmaker
from dateutil.parser import parse
from util import post_listing_to_slack, find_points_of_interest
from slackclient import SlackClient
import time
import settings

engine = create_engine('sqlite:///listings2.db', echo=False)

Base = declarative_base()

class Listing(Base):
    """
    A table to store data on craigslist listings.
    """

    __tablename__ = 'listings2'

    id = Column(Integer, primary_key=True)
    link = Column(String, unique=True)
    created = Column(DateTime)
    name = Column(String)
    price = Column(Float)
    location = Column(String)
    cl_id = Column(Integer, unique=True)
    area = Column(String)
    area_rank = Column(String)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def scrape_area():
    """
    Scrapes craigslist for a certain geographic area, and finds the latest listings.
    :param area:
    :return: A list of results.
    """
    #cl_h = CraigslistHousing(site=settings.CRAIGSLIST_SITE, category=settings.CRAIGSLIST_HOUSING_SECTION,
                             #filters={'max_price': settings.MAX_PRICE, 'min_price': settings.MIN_PRICE, 'is_furnished' : 1})
    #for result in cl_h.get_results(sort_by='newest', geotagged=True, limit=20)

    results = [] 

    saved_results = p.load(open('saved_furnished.p', 'rb'))
    for result in saved_results:

        # Don't store the listing if it already exists.    
        listing = session.query(Listing).filter_by(cl_id=result["id"]).first()

        if listing is None:
            if result["where"] is None:
                # If there is no string identifying which neighborhood the result is from, skip it.
                continue
     

            # Annotate the result with information about the area it's in and points of interest near it.
            geo_data = find_points_of_interest(result["where"])
            result.update(geo_data)

            # Try parsing the price.
            price = 0
            try:
                price = float(result["price"].replace("$", ""))
            except Exception:
                pass

            # Create the listing object.
            listing = Listing(
                link=result["url"],
                created=parse(result["datetime"]),
                name=result["name"],
                price=price,
                location=result["where"],
                cl_id=result["id"],
                area=result["area"],
                area_rank=result["area_rank"]
            )

            # Save the listing so we don't grab it again.
            session.add(listing)
            session.commit()
        
            if len(result["area_rank"]) > 0 :
                results.append(result)

    return results

def do_scrape():
    """
    Runs the craigslist scraper, and posts data to slack.
    """

    # Create a slack client.
    sc = SlackClient(settings.SLACK_TOKEN)

    # Get all the results from craigslist. 
    all_results = scrape_area()

    print("{}: Got {} results".format(time.ctime(), len(all_results)))

    # Post each result to slack.
    for result in all_results:
        post_listing_to_slack(sc, result)
