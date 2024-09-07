# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import os
import random
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
import requests
from PIL import Image
from faker import Faker
from flask import current_app
from sqlalchemy.exc import IntegrityError

from albumy.extensions import db
from albumy.models import User, Photo, Tag, Comment, Notification

fake = Faker()
endpoint = "https://mlinplab1.cognitiveservices.azure.com/"
key = os.getenv('AZURE_VISION_KEY')
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))


def fake_admin():
    admin = User(name='Grey Li',
                 username='greyli',
                 email='admin@helloflask.com',
                 bio=fake.sentence(),
                 website='http://greyli.com',
                 confirmed=True)
    admin.set_password('helloflask')
    notification = Notification(message='Hello, welcome to Albumy.', receiver=admin)
    db.session.add(notification)
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for i in range(count):
        user = User(name=fake.name(),
                    confirmed=True,
                    username=fake.user_name(),
                    bio=fake.sentence(),
                    location=fake.city(),
                    website=fake.url(),
                    member_since=fake.date_this_decade(),
                    email=fake.email())
        user.set_password('123456')
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=30):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.follow(User.query.get(random.randint(1, User.query.count())))
    db.session.commit()


def fake_azure_tags(image_path):
    with open(image_path, "rb") as image_data:
        # analyze_image_in_stream: sends images to Azure API for analysis, opened in binary mode
        # visual_features: ask API to return tags
        tags_analysis = computervision_client.analyze_image_in_stream(image_data, visual_features = [VisualFeatureTypes.tags])
        # loops thru each tag and extracts the actual label for the tag
        # then aggregates into list 'tags'
        tags = [tag.name for tag in tags_analysis.tags]
    return tags    

def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

# reduce to 10 from 30 to prevent 429 error: free tier problem
def fake_photo(count=10):
    # photos
    upload_path = current_app.config['ALBUMY_UPLOAD_PATH']
    for i in range(count):
        print(i)

        filename = 'random_%d.jpg' % i
        r = lambda: random.randint(128, 255)
        img = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))
        img_path = os.path.join(upload_path, filename)
        img.save(os.path.join(upload_path, filename))

        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year()
        )

        # Attach Azure Tags
        azure_tags = fake_azure_tags(img_path)
        print(f"Azure Vision Tags for {filename}: {azure_tags}")

        # Add the azure Tags to the photo
        for tag_name in azure_tags:
            # check if the tag is already in the database
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name = tag_name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
        db.session.add(photo)

        # photo.tags.append(tag)
        # original ways to add tags
        # for j in range(random.randint(1, 5)):
        #     tag = Tag.query.get(random.randint(1, Tag.query.count()))
        #     print("tag", tag)
        #     if tag not in photo.tags:
        #         photo.tags.append(tag)

        # db.session.add(photo)
    db.session.commit()


def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Photo.query.get(random.randint(1, Photo.query.count())))
    db.session.commit()


def fake_comment(count=100):
    for i in range(count):
        comment = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            photo=Photo.query.get(random.randint(1, Photo.query.count()))
        )
        db.session.add(comment)
    db.session.commit()
