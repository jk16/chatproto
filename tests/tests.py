



import unittest

import tornado.ioloop
import tornado.httpclient
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, AsyncHTTPClient, LogTrapTestCase

import urllib
import json


from chatproto import make_app


class BaseHTTPTestCase(AsyncHTTPTestCase):

    def get_app(self):
        self.myapp = make_app()

        return self.myapp


    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()




class LoginBroadcastTest(BaseHTTPTestCase):


    def setUp(self):

        #this calls the base class's setUp
        BaseHTTPTestCase.setUp(self)
        

        


    def tearDown(self):

        pass



    @tornado.testing.gen_test(timeout=60)
    def test_login_broadcast(self):

        client = AsyncHTTPClient(self.io_loop)

        #message = {"type": "login", "payload": "django"}
        #data = {"message": message}

        message0 = {"type": "login", "payload": "django"}
        #data = {"message": json.dumps(message), "other_data_for_the_query_string": "value"}

        #examlpe url: /mr.login?message=<message in JSON>&other_data_for_the_query_string=value
        url = self.get_url('/mr.login?message=' + urllib.parse.quote(json.dumps(message0)))
        #url = self.get_url('/mr.login?' + urllib.parse.urlencode(data))

        response = yield client.fetch(url, method='GET')

        self.assertEqual(response.code, 200)

        bodystr = None
        try:
            bodystr = response.body.decode("utf-8")
        except ValueError:
            self.fail("Mr. Login gave an invalid response to a login; it was not valid utf-8; response: %s" % repr(response.body))


        login_response = None
        try:
            login_response = json.loads(bodystr)
        except ValueError:
            self.fail("Mr. Login gave an invalid response to a login; it was not valid json; response: %s" % repr(response.body))

        
        self.assertTrue( 'success' in login_response, msg=login_response )
        self.assertTrue( isinstance(login_response['success'], bool), msg=login_response )
        self.assertTrue( login_response['success'], msg=login_response )



        self.assertTrue( 'msg' in login_response, msg=login_response )
        self.assertTrue( isinstance(login_response['msg'], str), msg=login_response )








