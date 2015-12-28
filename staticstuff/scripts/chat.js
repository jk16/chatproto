


$(document).ready(function(){
    
    $('#loginform')
        .show()
        .on('submit', function(eventObject){

            ///TLDR: TELL SEVER I AM LOGGING IN, AND HERE IS MY NICK


            console.log('USER SUBMITTED LOGIN!');
            eventObject.preventDefault();


            var nick = $('#nickname').val();

            ///let us use a standard message format, that will generalize all client => server communications
            var message = {type: 'login', payload: nick};

            var data = {message: JSON.stringify(message)};

            /**
             * Unescaped example of what the url will look like
             * /login?message={"type": "login", "payload": "realz"}
             */

            $.ajax({url: '/mr.login', data: data, dataType: 'json'})
                .done(function(response){
                    /*
                     {
                          success: boolean
                        , msg: string
                     }
                     */

                    if (response.success)
                    {
                        $('#loginform').hide();
                        //.. show msg-input-form
                        
                        $('#inputform').show();

                    } else {
                        alert(response.msg);
                    }
                })
                .fail(function(err){
                    console.log(err);
                    alert(err.statusText);
                });





            return false;
        });


    $('#inputform')
        .on('submit', function(eventObject){
            eventObject.preventDefault();

            ///TODO
        });











    ///Callback for what happens when we receive a broadcastted message from the server.
    function ReceivedMessage(msg) {
        ///TLDR: We got a message from the server! NOW HANDLE IT!! IN OTHER WORDS, SINCE YOU DO NOT KNOW WHAT HANDLE MEANS,
        /// $$$$ing DO SOMETHING WITH IT.

        if (msg['type'] == 'login')
        {
            var nick = msg['payload'];

            $('<li>' + nick + '</li>').appendTo( $('#nick-buffer-list') );
        } else {
            console.error('GOT A MESSAGE WITH UNRECOGNIZED TYPE');
        }

        ///TODO: HANDLE OTHER MESSAGE TYPES


    }


    var last_known_message_id = null;

    ///check if there are any server messages waiting for us
    function poll(){



        $.ajax({url: "/mr.broadcaster", type: "GET", data: {cursor: last_known_message_id}, dataType: "json"})
            .done(function(response){
                ///TLDR: GOT A BATCH OF MESSAGES FROM THE BROADCASTER!
                /*
                 * Example response:
                 *
                 * {
                 *    "messages": [ {"type": "login", "payload": "realz"},  {"type": "logout", "payload": "django"}   ]
                 *
                 * }
                 *
                 */

                ///TLDR: FOR EACH MESSAGE, DO SOMETHING WITH IT!
                for (var i = 0; i < response.messages.length; ++i)
                {
                    var message = response.messages[i];
                    ///TLDR: DO SOMETHING WITH IT!!
                    ReceivedMessage(message);

                    ///THIS IS THE LAST MESSAGE I SAW
                    last_known_message_id = message['id'];
                }



                setTimeout(poll, 0);



            })
            .fail(function(err){
                console.error(err);
                setTimeout(poll, 0);
            });
    }





    setTimeout(poll, 0);



});







