

import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.concurrent import Future

import json
import time


"""

* Client:
    * Chat Page
        * Message Buffer
            * Watch for new messages
        * Login Form
            * Nick name
            * Submit button
            * Submits data via ajax
            * If login is successful, will show Input Form
        * Input Form
            * Replaces Login Form after successful login
            * Input box for new messages
            * Submit button to send messages
        * Nick Buffer
            * Shows all chatters' nicks
            * When someone new joins, nick shows up here
            * When someone logs out or disconnects, nick goes away from here
* Server
    * Serves Chat Page
    * Answer login queries
    * Take message submissions
    * Rebroadcast message submissions
    * Rebroadcast nick logins/logouts

"""





"""
1. We will use "message buffer" to hand out futures, to different "waiters", in other words
people waiting in line at Mr. Broadcaster's desk.

2. We will have a list of futures/"waiters".

3. Whenever Mr. Login (or Mr. Message) gets a message needing to
be broadcasted, we will fullfill all the futures in the list, and satisfy
all the "waiters" at once.


"""


class MessageBuffer:
    #allows communications between the different handlers, AKA "people"

    def __init__(self):
        self.waiters = []

        #a list of the last 200 (or so) messages
        self.cache = []

        self.last_generated_msg_id = 0

    def get_a_future_for_the_next_message(self, cursor):
        #get on line to Mr Broadcaster, and receive a ticket.


        #TAKE A NUMBER! *nasty voice*
        f = Future()

        #if there is a cache, and the cursor is not the last message in the cache:
        if len(self.cache) > 0 and self.cache[-1]['id'] != cursor:
            #fullfill the future with all the messages in the cache RIGHT NOW

            #example, cache == [ {"id": 3}, {"id": 4}, {"id": 5} ]
            #example cursor == 4
            #resulting messages = [{"id": 5}]

            #example, cache == [ {"id": 3}, {"id": 4}, {"id": 5} ]
            #example cursor == 3
            #resulting messages = [{"id": 4}, {"id": 5}]


            #example, cache == [ {"id": 3}, {"id": 4}, {"id": 5} ]
            #example cursor == None
            #resulting messages = [{"id": 3}, {"id": 4}, {"id": 5}]

            def find_start_message_index():
                #find the index into the cache, where the cursor points to
                for (i,message) in enumerate(self.cache):
                    if message['id'] == cursor:
                        #then i is the index that we are looking for
                        return i + 1

                #if for some reason the cursor does not exist in the cache at all,
                #return 0, because that means we need to send him the entire cache.
                return 0

            index = find_start_message_index()

            #print (index, flush=True)

            #get all the messages in the cache, starting from `index`, until the end.
            next_messages = self.cache[index:]

            assert len(next_messages) > 0

            f.set_result(next_messages)

            return f

        else:
            #guy has to wait a bit, until the next message comes in.


            #put the number in the list
            self.waiters.append(f)

            #give the guy his number
            #so he can yield from the future and wait until it is ready (in other words, until the next message).
            return f



    def notify(self, messages):

        #store it in the cache
        self.cache += messages


        #we can now clear the line and let everyone have their message.

        for f in self.waiters:
            f.set_result(messages)

        self.waiters = []

    def generate_message_id(self):
        self.last_generated_msg_id += 1

        return str(self.last_generated_msg_id)






class ChatPageHandler(tornado.web.RequestHandler):
    def get(self, wildcard=None):
        self.render('chat.html')


"""
This handler speaks to our login button via ajax.
"""
class MrLogin(tornado.web.RequestHandler):
    def get(self, wildcard=None):


        message = self.get_argument('message')
        message = json.loads(message)
        #example message
        #{"type": "login", "payload": "realz"}

        global_message_buffer = self.application.global_message_buffer
        message['id'] = global_message_buffer.generate_message_id()

        #example message
        #{"type": "login", "payload": "realz", "id": 51}

        #print (message, flush=True)


        #do some checking here to see if the guy should actually be allowed to login
        #TODO

        global_message_buffer.notify([message])






        self.set_header('Content-Type', 'text/json; charset="utf-8"')


        autosuccess = """
{
      "success": true
    , "msg": "YOU HAVE LOGGED IN"
}
"""
        self.write(autosuccess)







class MrBroadcaster(tornado.web.RequestHandler):


    @gen.coroutine
    def get(self, wildcard=None):
        #id of my last message, if any
        cursor = self.get_argument('cursor', None)


        #print ('global_message_buffer.cache:', global_message_buffer.cache)



        global_message_buffer = self.application.global_message_buffer

        #get a ticket/future
        f = global_message_buffer.get_a_future_for_the_next_message(cursor)

        #wait for the ticket/future to be called (fullfilled)
        next_messages = yield f


        self.set_header('Content-Type', 'text/json; charset="utf-8"')


        """
        example response:
        {
            "messages": [ {"type": "login", "payload": "django", "id": 245}
                        , {"type": "logout", "payload": "django_", "id": 244}
                        , {"type": "chat", "payload": {"text": "anyone here", "timestamp": 12345678, "author": "realz"}, "id": 243}]
        }
        """


        response_dictionary = { "messages": next_messages }
        response_in_json_string = json.dumps( response_dictionary )
        self.write( response_in_json_string )

        #it terminates the connection by virtue of hitting the end of the function
        #however, long-polling involves simply getting back on line immediately.
        #so you don't miss a message.



class MrMessage(tornado.web.RequestHandler):

    def get(self,wildcard=None):
        #example url to this page: /mr.message?message=<json message>

        global_message_buffer = self.application.global_message_buffer

        message = self.get_argument('message')
        message = json.loads(message)

        #example message: {"type": "chat", "payload": {"author": "realz", "text": "hunter2"} }

        message['id'] = global_message_buffer.generate_message_id()
        message['payload']['timestamp'] = time.time()

        global_message_buffer.notify([message])

        self.set_header('Content-Type', 'text/json; charset="utf-8"')

        autosuccess = """
{
      "success": true
    , "msg": "YOU HAVE SUCCESSFULLY SENT THE MESSAGE"
}
"""
        self.write(autosuccess)



def make_app():

    paths = [
        ("/", ChatPageHandler),
        ("/mr.login", MrLogin),
        ("/mr.broadcaster", MrBroadcaster),
        ("/mr.message", MrMessage),

        #matches url with /static/*, and looks on disk in ./staticstuff
        ('/static/(.*)', tornado.web.StaticFileHandler, {'path': './staticstuff'})
    ]
    app = tornado.web.Application(paths, template_path='./templates', debug=True)


    global_message_buffer = MessageBuffer()

    app.global_message_buffer = global_message_buffer



    return app



if __name__ == "__main__":
    app = make_app()
    app.listen(8888)

    #start the server
    tornado.ioloop.IOLoop.current().start()

    #never runs




