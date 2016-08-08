# Copyright 2015 Google Inc. All rights reserved.
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

"""Unit tests for oauth2client_latest._helpers."""

import mock
import unittest2

from oauth2client_latest import _helpers


__author__ = 'jcgregorio@google.com (Joe Gregorio)'


class PositionalTests(unittest2.TestCase):

    def test_usage(self):
        _helpers.positional_parameters_enforcement = (
            _helpers.POSITIONAL_EXCEPTION)

        # 1 positional arg, 1 keyword-only arg.
        @_helpers.positional(1)
        def function(pos, kwonly=None):
            return True

        self.assertTrue(function(1))
        self.assertTrue(function(1, kwonly=2))
        with self.assertRaises(TypeError):
            function(1, 2)

        # No positional, but a required keyword arg.
        @_helpers.positional(0)
        def function2(required_kw):
            return True

        self.assertTrue(function2(required_kw=1))
        with self.assertRaises(TypeError):
            function2(1)

        # Unspecified positional, should automatically figure out 1 positional
        # 1 keyword-only (same as first case above).
        @_helpers.positional
        def function3(pos, kwonly=None):
            return True

        self.assertTrue(function3(1))
        self.assertTrue(function3(1, kwonly=2))
        with self.assertRaises(TypeError):
            function3(1, 2)

    @mock.patch('oauth2client_latest._helpers.logger')
    def test_enforcement_warning(self, mock_logger):
        _helpers.positional_parameters_enforcement = (
            _helpers.POSITIONAL_WARNING)

        @_helpers.positional(1)
        def function(pos, kwonly=None):
            return True

        self.assertTrue(function(1, 2))
        self.assertTrue(mock_logger.warning.called)

    @mock.patch('oauth2client_latest._helpers.logger')
    def test_enforcement_ignore(self, mock_logger):
        _helpers.positional_parameters_enforcement = _helpers.POSITIONAL_IGNORE

        @_helpers.positional(1)
        def function(pos, kwonly=None):
            return True

        self.assertTrue(function(1, 2))
        self.assertFalse(mock_logger.warning.called)


class ScopeToStringTests(unittest2.TestCase):

    def test_iterables(self):
        cases = [
            ('', ''),
            ('', ()),
            ('', []),
            ('', ('',)),
            ('', ['', ]),
            ('a', ('a',)),
            ('b', ['b', ]),
            ('a b', ['a', 'b']),
            ('a b', ('a', 'b')),
            ('a b', 'a b'),
            ('a b', (s for s in ['a', 'b'])),
        ]
        for expected, case in cases:
            self.assertEqual(expected, _helpers.scopes_to_string(case))


class StringToScopeTests(unittest2.TestCase):

    def test_conversion(self):
        cases = [
            (['a', 'b'], ['a', 'b']),
            ('', []),
            ('a', ['a']),
            ('a b c d e f', ['a', 'b', 'c', 'd', 'e', 'f']),
        ]

        for case, expected in cases:
            self.assertEqual(expected, _helpers.string_to_scopes(case))


class AddQueryParameterTests(unittest2.TestCase):

    def test__add_query_parameter(self):
        self.assertEqual(
            _helpers._add_query_parameter('/action', 'a', None),
            '/action')
        self.assertEqual(
            _helpers._add_query_parameter('/action', 'a', 'b'),
            '/action?a=b')
        self.assertEqual(
            _helpers._add_query_parameter('/action?a=b', 'a', 'c'),
            '/action?a=c')
        # Order is non-deterministic.
        self.assertIn(
            _helpers._add_query_parameter('/action?a=b', 'c', 'd'),
            ['/action?a=b&c=d', '/action?c=d&a=b'])
        self.assertEqual(
            _helpers._add_query_parameter('/action', 'a', ' ='),
            '/action?a=+%3D')


class Test__parse_pem_key(unittest2.TestCase):

    def test_valid_input(self):
        test_string = b'1234-----BEGIN FOO BAR BAZ'
        result = _helpers._parse_pem_key(test_string)
        self.assertEqual(result, test_string[4:])

    def test_bad_input(self):
        test_string = b'DOES NOT HAVE DASHES'
        result = _helpers._parse_pem_key(test_string)
        self.assertEqual(result, None)


class Test__json_encode(unittest2.TestCase):

    def test_dictionary_input(self):
        # Use only a single key since dictionary hash order
        # is non-deterministic.
        data = {u'foo': 10}
        result = _helpers._json_encode(data)
        self.assertEqual(result, '{"foo":10}')

    def test_list_input(self):
        data = [42, 1337]
        result = _helpers._json_encode(data)
        self.assertEqual(result, '[42,1337]')


class Test__to_bytes(unittest2.TestCase):

    def test_with_bytes(self):
        value = b'bytes-val'
        self.assertEqual(_helpers._to_bytes(value), value)

    def test_with_unicode(self):
        value = u'string-val'
        encoded_value = b'string-val'
        self.assertEqual(_helpers._to_bytes(value), encoded_value)

    def test_with_nonstring_type(self):
        value = object()
        with self.assertRaises(ValueError):
            _helpers._to_bytes(value)


class Test__from_bytes(unittest2.TestCase):

    def test_with_unicode(self):
        value = u'bytes-val'
        self.assertEqual(_helpers._from_bytes(value), value)

    def test_with_bytes(self):
        value = b'string-val'
        decoded_value = u'string-val'
        self.assertEqual(_helpers._from_bytes(value), decoded_value)

    def test_with_nonstring_type(self):
        value = object()
        with self.assertRaises(ValueError):
            _helpers._from_bytes(value)


class Test__urlsafe_b64encode(unittest2.TestCase):

    DEADBEEF_ENCODED = b'ZGVhZGJlZWY'

    def test_valid_input_bytes(self):
        test_string = b'deadbeef'
        result = _helpers._urlsafe_b64encode(test_string)
        self.assertEqual(result, self.DEADBEEF_ENCODED)

    def test_valid_input_unicode(self):
        test_string = u'deadbeef'
        result = _helpers._urlsafe_b64encode(test_string)
        self.assertEqual(result, self.DEADBEEF_ENCODED)


class Test__urlsafe_b64decode(unittest2.TestCase):

    def test_valid_input_bytes(self):
        test_string = b'ZGVhZGJlZWY'
        result = _helpers._urlsafe_b64decode(test_string)
        self.assertEqual(result, b'deadbeef')

    def test_valid_input_unicode(self):
        test_string = b'ZGVhZGJlZWY'
        result = _helpers._urlsafe_b64decode(test_string)
        self.assertEqual(result, b'deadbeef')

    def test_bad_input(self):
        import binascii
        bad_string = b'+'
        with self.assertRaises((TypeError, binascii.Error)):
            _helpers._urlsafe_b64decode(bad_string)
