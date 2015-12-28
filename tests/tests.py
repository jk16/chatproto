



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




class LoginBroadcastTest(BaseHTTPTestCase, LogTrapTestCase):


    def setUp(self):

        #this calls the base class's setUp
        BaseHTTPTestCase.setUp(self)
        LogTrapTestCase.setUp(self)
        

        


    def tearDown(self):

        pass



    @tornado.testing.gen_test(timeout=20)
    def test_login(self):

        client = AsyncHTTPClient(self.io_loop)


        message0 = {"type": "login", "payload": "django"}

        url = self.get_url('/mr.login?message=' + urllib.parse.quote(json.dumps(message0)))

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

        
        self.assertTrue( isinstance(login_response, dict), msg=login_response )


        self.assertTrue( 'success' in login_response, msg=login_response )
        self.assertTrue( isinstance(login_response['success'], bool), msg=login_response )
        self.assertTrue( login_response['success'], msg=login_response )



        self.assertTrue( 'msg' in login_response, msg=login_response )
        self.assertTrue( isinstance(login_response['msg'], str), msg=login_response )


        cache = self.myapp.global_message_buffer.cache
        self.assertTrue( len(cache) > 0, msg=cache )
        self.assertTrue( cache[-1]['type'] == message0['type'] )
        self.assertTrue( cache[-1]['payload'] == message0['payload'] )




    @tornado.testing.gen_test(timeout=20)
    def test_broadcast(self):



        message0 = {"type": "login", "payload": "django"}

        @tornado.gen.coroutine
        def do_login():

            client = AsyncHTTPClient(self.io_loop)
            #examlpe url: /mr.login?message=<message in JSON>&other_data_for_the_query_string=value
            url = self.get_url('/mr.login?message=' + urllib.parse.quote(json.dumps(message0)))

            response = yield client.fetch(url, method='GET')

            self.assertEqual(response.code, 200)


        yield do_login()



        client = AsyncHTTPClient(self.io_loop)

        url = self.get_url('/mr.broadcaster?cursor=100002325435')
        response = yield client.fetch(url, method='GET')
        self.assertEqual(response.code, 200)

        bodystr = None
        try:
            bodystr = response.body.decode("utf-8")
        except ValueError:
            self.fail("Mr. Broadcaster gave an invalid response to a broadcast request; it was not valid utf-8; response: %s" % repr(response.body))


        broadcast = None
        try:
            broadcast = json.loads(bodystr)
        except ValueError:
            self.fail("Mr. Broadcaster gave an invalid response to a broadcast request; it was not valid json; response: %s" % repr(response.body))


        self.assertTrue( isinstance(broadcast, dict), msg=broadcast )

        self.assertTrue( 'messages' in broadcast, msg=broadcast )
        self.assertTrue( isinstance(broadcast['messages'], list), msg=broadcast )


        found_login_message = False

        for message in broadcast['messages']:

            self.assertTrue( isinstance(message, dict), msg=message )



            self.assertTrue( 'id' in message, msg=message )
            self.assertTrue( isinstance(message['id'], (int,str)), msg=message )



            self.assertTrue( 'type' in message, msg=message )
            self.assertTrue( isinstance(message['type'], str), msg=message )
            self.assertTrue( message['type'] in ['login'], msg=message )



            self.assertTrue( 'payload' in message, msg=message )

            if (message['type'] == 'login'):
                self.assertTrue( isinstance(message['payload'], str), msg=message )



            if message['type'] == 'login' and message['payload'] == 'django':
                found_login_message = True



        self.assertTrue(found_login_message
                            , msg='Did not find the expected login message that we gave Mr. login; message0: %s, broadcast: %s'
                                     % (message0, broadcast))
































