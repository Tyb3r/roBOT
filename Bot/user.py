#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Functions for basic bot behaviours. """

import os
import logging
from datetime import date
import re
from Bot.cognition import recognize_sticker, replace_emojis
from Bot.geolocate import recognize_location
from OfferParser.translator import translate
from Databases import mysql_connection as db
from Bot.facebook_webhooks import get_user_info


class User:
    """ All user info that we also store in db """

    def __init__(self, facebook_id):

        # permanent:
        self.facebook_id = facebook_id
        #TODO auto fill info:
        # info = get_user_info(facebook_id)
        # print(info)
        # self.first_name = info['first_name']
        # self.last_name = info['last_name']
        # self.gender = info['gender']
        # self.language = info['locale']
        self.first_name = None
        self.last_name = None
        self.gender = None
        self.language = None
        # query parameters:
        self.business_type = None
        self.housing_type = None
        self.price_limit = None
        self.features = []  # ["dla studenta", "nieprzechodni", "niepalacy"]
        # address:
        self.country = None
        self.city = None
        self.street = None
        self.latitude = 0
        self.longitude = 0
        # dialogue parameters:
        self.context = "initialization"  # initialiation, greeting, ...
        self.interactions = 0
        self.shown_input = False
        self.asked_for_features = False
        self.wants_more_features = True
        self.wants_more_locations = True
        self.confirmed_data = False
        self.add_more = False

        if not db.user_exists(self.facebook_id):
            db.push_user(user_obj=self, update=False)

    # TODO universal setter?
    # def set_field(self, field_name, filed_value):
    # self.FIELD_NAME = FIELD.VALUE

    def increment(self):
        # TODO fix bug:     self.interactions += 1
        pass

    def set_facebook_id(self, facebook_id):
        self.facebook_id = str(facebook_id)
        logging.info(f"[User info] facebook_id set to {facebook_id}")
        db.update_user(self.facebook_id, field_to_update="facebook_id", field_value=self.facebook_id)

    def set_first_name(self, first_name):
        self.first_name = str(first_name)
        logging.info(f"[User info] first_name set to {first_name}")
        db.update_user(self.facebook_id, field_to_update="first_name", field_value=self.first_name)

    def set_last_name(self, last_name):
        self.last_name = str(last_name)
        logging.info(f"[User info] last_name set to {last_name}")
        db.update_user(self.facebook_id, field_to_update="last_name", field_value=self.last_name)

    def set_gender(self, gender):
        self.gender = str(gender)
        logging.info(f"[User info] gender set to {gender}")
        db.update_user(self.facebook_id, field_to_update="gender", field_value=self.gender)

    def set_context(self, context):
        self.context = str(context)
        logging.info(f"[User info] context set to {context}")
        db.update_user(self.facebook_id, field_to_update="context", field_value=self.context)

    def set_business_type(self, business_type):
        business_type = translate(business_type, "Q") # TODO Skasuj mnie jak Kuba poprawi w bazie.
        self.business_type = str(business_type)
        logging.info(f"[User info] business_type set to {business_type}")
        db.update_user(self.facebook_id, field_to_update="business_type", field_value=self.business_type)

    def set_housing_type(self, housing_type):
        housing_type = translate(housing_type, "Q")  # TODO Skasuj mnie jak Kuba poprawi w bazie.
        self.housing_type = str(housing_type)
        logging.info(f"[User info] housing_type set to {housing_type}")
        db.update_user(self.facebook_id, field_to_update="housing_type", field_value=self.housing_type)

    def set_price_limit(self, price_limit):
        try:
            # workaround for witai returning date instead of price:
            if "-" in str(price_limit) and ":" in str(price_limit):
                price_limit = price_limit[0:5]
            clean = re.sub("[^0-9]", "", str(price_limit))
            self.price_limit = int(clean)
            db.update_user(self.facebook_id, field_to_update="price_limit", field_value=self.price_limit)
            logging.info(f"[User info] price_limit set to {str(self.price_limit)}")

        except:
            logging.warning(f"Couldn't set the price limit using: '{price_limit}', so it remains at {self.price_limit}.")

    def set_city(self, city):
        self.city = str(city)
        logging.info(f"[User info] city set to {city}")
        db.update_user(self.facebook_id, field_to_update="city", field_value=self.city)

    def set_country(self, country):
        self.country = str(country)
        logging.info(f"[User info] country set to {country}")
        db.update_user(self.facebook_id, field_to_update="country", field_value=self.country)

    # TODO narazie nadpisuje, a powinno dodawać bo przecież może chcieć Mokotów Wolę i Pragę
    def add_location(self, location="", lat=0, long=0):

        if lat != 0 and long != 0:
            loc = recognize_location(lat=lat, long=long)
        elif "entrum" in str(location):
            if hasattr(self, 'city'):
                loc = recognize_location(location="centrum", city=self.city)
            else:
                loc = recognize_location(location=str(location))
        else:
            loc = recognize_location(location=str(location))

        self.latitude = float(loc['lat'])
        self.longitude = float(loc['lon'])
        self.country = loc['country']
        self.city = loc['city']
        self.street = loc['street']
        # self.state = loc['state']
        # self.county = loc['county']

        db.update_user(self.facebook_id, field_to_update="latitude", field_value=self.latitude)
        db.update_user(self.facebook_id, field_to_update="longitude", field_value=self.longitude)
        db.update_user(self.facebook_id, field_to_update="city", field_value=self.city)
        db.update_user(self.facebook_id, field_to_update="street", field_value=self.street)
        db.update_user(self.facebook_id, field_to_update="country", field_value=self.country)

        logging.info(f"User({self.facebook_id[0:5]})'s location changed to: latitude={self.latitude}, longitude={self.longitude}, city={self.city}, street={self.street}, country={self.country}")

    def add_feature(self, feature):
        feature = replace_emojis(feature)
        if feature not in self.features:
            self.features.append(str(feature))
            logging.info(f"[User info] added feature: {feature}. Now features are: {str(self.features)}")
            current = db.get_user(self.facebook_id).features
            appended = str(current)+"&"+str(feature)
            db.update_user(self.facebook_id, field_to_update="feature", field_value=appended)
        else:
            logging.info(f"[User info] Feature: {feature} was already in the object.")

    def set_confirmed_data(self, confirmed_data):
        self.confirmed_data = confirmed_data
        logging.info(f"[User info] confirmed_data set to: {confirmed_data}")
        db.update_user(self.facebook_id, field_to_update="confirmed_data", field_value=self.confirmed_data)
