# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import unittest2

import oauth2client_latest
import oauth2client_latest.client
import oauth2client_latest.contrib.sqlalchemy

Base = sqlalchemy.ext.declarative.declarative_base()


class DummyModel(Base):
    __tablename__ = 'dummy'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    # we will query against this, because of ROWID
    key = sqlalchemy.Column(sqlalchemy.Integer)
    credentials = sqlalchemy.Column(
        oauth2client_latest.contrib.sqlalchemy.CredentialsType)


class TestSQLAlchemyStorage(unittest2.TestCase):
    def setUp(self):
        engine = sqlalchemy.create_engine('sqlite://')
        Base.metadata.create_all(engine)

        self.session = sqlalchemy.orm.sessionmaker(bind=engine)
        self.credentials = oauth2client_latest.client.OAuth2Credentials(
            access_token='token',
            client_id='client_id',
            client_secret='client_secret',
            refresh_token='refresh_token',
            token_expiry=datetime.datetime.utcnow(),
            token_uri=oauth2client_latest.GOOGLE_TOKEN_URI,
            user_agent='DummyAgent',
        )

    def tearDown(self):
        session = self.session()
        session.query(DummyModel).filter_by(key=1).delete()
        session.commit()

    def compare_credentials(self, result):
        self.assertEqual(result.access_token, self.credentials.access_token)
        self.assertEqual(result.client_id, self.credentials.client_id)
        self.assertEqual(result.client_secret, self.credentials.client_secret)
        self.assertEqual(result.refresh_token, self.credentials.refresh_token)
        self.assertEqual(result.token_expiry, self.credentials.token_expiry)
        self.assertEqual(result.token_uri, self.credentials.token_uri)
        self.assertEqual(result.user_agent, self.credentials.user_agent)

    def test_get(self):
        session = self.session()
        credentials_storage = oauth2client_latest.contrib.sqlalchemy.Storage(
            session=session,
            model_class=DummyModel,
            key_name='key',
            key_value=1,
            property_name='credentials',
        )
        self.assertIsNone(credentials_storage.get())
        session.add(DummyModel(
            key=1,
            credentials=self.credentials,
        ))
        session.commit()

        self.compare_credentials(credentials_storage.get())

    def test_put(self):
        session = self.session()
        oauth2client_latest.contrib.sqlalchemy.Storage(
            session=session,
            model_class=DummyModel,
            key_name='key',
            key_value=1,
            property_name='credentials',
        ).put(self.credentials)
        session.commit()

        entity = session.query(DummyModel).filter_by(key=1).first()
        self.compare_credentials(entity.credentials)

    def test_delete(self):
        session = self.session()
        session.add(DummyModel(
            key=1,
            credentials=self.credentials,
        ))
        session.commit()

        query = session.query(DummyModel).filter_by(key=1)
        self.assertIsNotNone(query.first())
        oauth2client_latest.contrib.sqlalchemy.Storage(
            session=session,
            model_class=DummyModel,
            key_name='key',
            key_value=1,
            property_name='credentials',
        ).delete()
        session.commit()
        self.assertIsNone(query.first())
