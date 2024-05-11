from flask import render_template, url_for, flash, redirect, request, session, make_response, jsonify
from Assignment import app, db, socketio
from Assignment.models import User, Message, FriendRequest, Room, Key, UserRole
from flask_socketio import join_room, leave_room, send, emit
from string import ascii_uppercase
import random



def generate_unique_code(Length):
    rooms = Room.query.all()
    all_rooms = []
    for room in rooms:
        all_rooms.append(room.code)
    while True:
        code = ''
        for _ in range(Length):
            code += random.choice(ascii_uppercase)
        if code not in all_rooms:
            break
        
    return code


#homepage
@app.route("/")
def home():
    return render_template('home.html', title='homepage')

#homepage after login
@app.route("/chathome", methods=["POST", "GET"])
def chathome():
    current_user_name = request.cookies.get('username')
    if(current_user_name is None):
        return redirect(url_for("home"))
    current_user = User.query.filter_by(username=current_user_name).first()
    current_user_id = current_user.id
    pending_requests = FriendRequest.query.filter_by(receiver_id=current_user_id, accepted=False).all()
    friend_requests = FriendRequest.query.filter_by(sender_id=current_user_id, accepted=True).all()

    if request.method == "POST":
        user = request.form.get("username")
        join = request.form.get("join", False)
        friend_name = request.form.get("clickfriend", False)

        if friend_name != False:
            exist_room = Room.query.filter_by(creater=current_user_name, receiver=friend_name).first()
            exist_friend_room = Room.query.filter_by(receiver=current_user_name, creater=friend_name).first()
            
            if exist_friend_room or exist_room:
                
                if exist_friend_room:
                    session["room"] = exist_friend_room.code
                    session["name"] = current_user_name
                    friend_pk = Key.query.filter_by(username=friend_name).first()
                    return redirect(url_for("room",friend_pk=friend_pk.public_key))
                elif exist_room:
                    session["room"] = exist_room.code
                    session["name"] = current_user_name
                    friend_pk = Key.query.filter_by(username=friend_name).first()
                    return redirect(url_for("room",friend_pk=friend_pk.public_key))

            room = Room(code=generate_unique_code(4), creater=current_user_name, receiver=friend_name)
            db.session.add(room)
            db.session.commit()
            session["room"] = room.code
            session["name"] = current_user_name
            friend_pk = Key.query.filter_by(username=friend_name).first()
            return redirect(url_for("room",friend_pk=friend_pk.public_key))


        if join != False and not user:
            return render_template('chathome.html', chat_error='Please enter a username', current_user_name=current_user_name, friend_requests=pending_requests, friends=friend_requests, role = current_user.role.value)

        exist_userroom = Room.query.filter_by(creater=current_user_name, receiver=user).first()
        receive_room = Room.query.filter_by(receiver=current_user_name, creater=user).first()
        exist_user = User.query.filter_by(username=user).first()
        if not exist_user:
            return render_template('chathome.html', chat_error='User does not exist.', current_user_name=current_user_name, friend_requests=pending_requests, friends=friend_requests, role = current_user.role.value)
        if exist_userroom or receive_room:
                if(exist_userroom):
                    session["room"] = exist_userroom.code
                    session["name"] = current_user_name
                    friend_pk = Key.query.filter_by(username=user).first()
                    return redirect(url_for("room", friend_pk=friend_pk.public_key))
                elif(receive_room):
                    session["room"] = receive_room.code
                    session["name"] = current_user_name
                    friend_pk = Key.query.filter_by(username=user).first()
                    return redirect(url_for("room",friend_pk=friend_pk.public_key))
        else:
            room = Room(code=generate_unique_code(4), creater=current_user_name, receiver=user)
            db.session.add(room)
            db.session.commit()
            session["room"] = room.code
            session["name"] = current_user_name
            friend_pk = Key.query.filter_by(username=user).first()
            return redirect(url_for("room",friend_pk=friend_pk.public_key))

    return render_template('chathome.html', title='chatroom', current_user_name=current_user_name, friend_requests=pending_requests, friends=friend_requests, role =current_user.role.value)

#register
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username =  request.form.get("username")
        password =  request.form.get("password")
        pk = request.form.get('PK')
        salt = request.form.get("salt")
        if len(username) < 2 or len(username) > 20 or (username == ""):
            return render_template('register.html', register_error='Please enter a valid username, length from 2 to 20.')
        user = User.query.filter_by(username=username).first()
        if(user != None):
            return render_template('register.html', register_error='Username already exist')
        exist = Key.query.filter_by(username=username).first()
        if(exist == None):
            key = Key(username=username, public_key = pk)
            db.session.add(key)
            db.session.commit()
        user = User(username = username, password = password, salt = salt, role = UserRole.student)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login', 'success')
        return redirect(url_for('home'))

    return render_template('register.html', title='register')


@socketio.on('user_salt')
def get_user_salt(data):
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if user:
        salt = user.salt
        emit('salt', {'salt': salt})
    else:
        emit('login_error', {'error': 'This user does not exist.'})
        return

#login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        pk = request.form.get('PK')
        user = User.query.filter_by(username=username).first()
        if user and (user.password == password):
            response = make_response(redirect(url_for('chathome')))
            response.set_cookie('username', user.username)
            return response
        else:
            return render_template('login.html', title='login', login_error='Password is incorrect')

            
    return render_template('login.html', title='login')



# Socket listening for sending friend request event
@socketio.on('send_friend_request')
def send_friend_request(data):
    friend_username = data.get('friendUsername')
    sender_name = request.cookies.get('username')
    if friend_username == sender_name:
        emit('friend_request_error', {'error': 'You cannot add yourself as a friend.'})
        return
    
    receiver = User.query.filter_by(username=friend_username).first()
    if not receiver:
        emit('friend_request_error', {'error': 'This user does not exist.'})
        return
    sender = User.query.filter_by(username=sender_name).first()
    if friend_username in [friend.sender.username for friend in FriendRequest.query.filter_by(sender_id=sender.id, accepted=True).all()]:
        emit('friend_request_error', {'error': 'This user has already been your friend.'})
        return
    
    repeat = FriendRequest.query.filter_by(receiver_id=receiver.id, sender_id=sender.id).first()
    if repeat == None:
        friend_request = FriendRequest(sender_id=sender.id, receiver_id=receiver.id)
        db.session.add(friend_request)
        db.session.commit()
        emit('friend_request_notification', {'receiver': receiver.username})
    else:
        emit('friend_request_error', {'error': 'You already send the friend request.'})

# Socket listening for accepting friend request event
@socketio.on('accept_request')
def accept_request(data):
    request_id = data.get('request_id')

    curr_request = FriendRequest.query.filter_by(id=request_id).first()
    if curr_request:
        if not curr_request.accepted:
            FriendRequest.query.filter_by(id=request_id).update({'accepted': True})
            friend_request = FriendRequest(sender_id=curr_request.receiver.id, receiver_id=curr_request.sender.id, accepted=True)
            db.session.add(friend_request)
            db.session.commit()
            emit('accept')
        else:
            emit('accept_error', {'error': 'You have already accepted the friend request.'})
    else:
        emit('accept_error', {'error': 'Friend request not found.'})
    
# Socket listening for rejecting friend request event
@socketio.on('reject_request')
def reject_request(data):
    request_id = data.get('request_id')

    curr_request = FriendRequest.query.filter_by(id=request_id).first()
    if curr_request:
        FriendRequest.query.filter_by(id=request_id).delete()
        db.session.commit()
        emit('reject')
    else:
        emit('reject_error', {'error': 'Friend request not found.'})
        db.session.rollback()

@socketio.on("remove")
def remove(data):
    fid = data.get("fid")
    id = data.get("id")
    FriendRequest.query.filter_by(sender_id=id, receiver_id=fid).delete()
    FriendRequest.query.filter_by(receiver_id=id, sender_id=fid).delete()
    db.session.commit()
    emit("remove_msg")

# chatroom
@app.route("/chatroom")
def room():
    room_code = session.get("room")
    friend_pk = request.args.get("friend_pk")
    current_user_name = request.cookies.get('username')
    current_user = User.query.filter_by(username=current_user_name).first()
    if room_code is None or session.get("name") is None:
        return redirect(url_for("home"))
    room = Room.query.filter_by(code=room_code).first()
    if not room:
        return redirect(url_for("home"))
    messages = room.messages
    return render_template("chatroom.html", code=room.code, message=messages, friend_pk=friend_pk, current_user=current_user)

# socket listening join event
@socketio.on('connect')
def connect(auth):
    room_code = session.get("room")
    name = session.get("name")
    if not room_code or not name:
        return
    room = Room.query.filter_by(code=room_code).first()
    if not room:
        leave_room(room_code)
        return
    session["name"] = name
    join_room(room_code)
    
    # room.messages.append(Message(message=f"{name} has entered the room", user_name=current_user.username, room_id=room.id))
    # db.session.commit()
    emit("enter", {"name": name, "message": "has entered the room"}, to=room_code)

@socketio.on("disconnect")
def disconnect():
    room_code = session.get("room")
    name = session.get("name")
    # if room_code:
    #     room = Room.query.filter_by(code=room_code).first()
    #     if room:
    #         room.messages.append(Message(message=f"{name} has left the room", user_name=current_user.username, room_id=room.id))
    #         db.session.commit()
    leave_room(room_code)
    emit("enter", {"name": name, "message": "has left the room"}, to=room_code)

@socketio.on("message")
def message(data):
    room_code = session.get("room")
    if room_code:
        room = Room.query.filter_by(code=room_code).first()
        if room:
            name = request.cookies.get('username')
            content = {
                "name": name,
                "message": data["data"],
                "mac": data["mac"]
            }
            room.messages.append(Message(message=data["data"], user_name=name, room_id=room.id))
            db.session.commit()
            send(content, to=room_code)