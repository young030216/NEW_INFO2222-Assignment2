from flask import render_template, url_for, flash, redirect, request, session, make_response
from Assignment import app, db, bcrypt, socketio
from Assignment.forms import Registeration, Login
from Assignment.models import User, Message, FriendRequest, Room, FriendRoom
from flask_login import login_user, current_user
from flask_socketio import join_room, leave_room, send, emit
from string import ascii_uppercase
import random


rooms = {}

def generate_unique_code(Length):
    while True:
        code = ''
        for _ in range(Length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
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
    current_user = User.query.filter_by(username=current_user_name).first()
    current_user_id = current_user.id
    pending_requests = FriendRequest.query.filter_by(receiver_id=current_user_id, accepted=False).all()
    friend_requests = FriendRequest.query.filter_by(sender_id=current_user_id, accepted=True).all()
    rooms = Room.query.all()
    friendrooms = FriendRoom.query.all()

    if request.method == "POST":
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        friend_name = request.form.get("clickfriend", False)

        if friend_name != False:
            exist_room = FriendRoom.query.filter_by(user_name=current_user.username, friend_name=friend_name).first()
            exist_friend_room = FriendRoom.query.filter_by(friend_name=current_user.username, user_name=friend_name).first()
            
            if exist_friend_room or exist_room:
                print("f**!")
                if exist_friend_room:
                    session["room"] = exist_friend_room.room_code
                elif exist_room:
                    session["room"] = exist_room.room_code
                session["name"] = current_user_name
                return redirect(url_for("room"))

    
            room = Room(code=generate_unique_code(4))
            friendroom = FriendRoom(user_name=current_user_name, friend_name=friend_name, room_code=room.code)
            db.session.add(room)
            db.session.add(friendroom)
            db.session.commit()

            session["room"] = room.code
            session["name"] = current_user_name
            return redirect(url_for("room"))


        if join != False and not code:
            return render_template('chathome.html', chat_error='Please enter a Room code.', current_user_name=current_user_name, rooms=rooms, friend_requests=pending_requests)

        room = Room.query.filter_by(code=code).first()
        if create != False:
            room = Room(code=generate_unique_code(4))
            db.session.add(room)
            db.session.commit()
        elif not room:
            return render_template('chathome.html', chat_error='Room does not exist.', current_user_name=current_user_name, rooms=rooms, friend_requests=pending_requests)

        session["room"] = room.code
        session["name"] = current_user_name
        return redirect(url_for("room"))

    return render_template('chathome.html', title='chatroom', current_user_name=current_user_name, friend_requests=pending_requests, friends=friend_requests, rooms=rooms)

#register
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Registeration()
    if form.validate_on_submit():
        ##store the name and passwrod into db
        hassed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, password = hassed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login', 'success')
        return redirect(url_for('login'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')
    return render_template('register.html', title='Register', form=form)

#login
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            response = make_response(redirect(url_for('chathome')))
            response.set_cookie('username', user.username)
            return response
        else:
            flash('Login Unsuccessful. Please check username and password','danger')
            
    return render_template('login.html', title='Login', form = form)


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


# chatroom
@app.route("/chatroom")
def room():
    room_code = session.get("room")
    if room_code is None or session.get("name") is None:
        return redirect(url_for("chathome"))
    room = Room.query.filter_by(code=room_code).first()
    if not room:
        return redirect(url_for("chathome"))
    messages = room.messages
    return render_template("chatroom.html", code=room.code, message=messages)

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
    emit("message", {"name": name, "message": "has entered the room"}, to=room_code)

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

@socketio.on("message")
def message(data):
    room_code = session.get("room")
    if room_code:
        room = Room.query.filter_by(code=room_code).first()
        if room:
            name = session.get("name")
            content = {
                "name": name,
                "message": data["data"]
            }
            room.messages.append(Message(message=data["data"], user_name=current_user.username, room_id=room.id))
            db.session.commit()
            send(content, to=room_code)
