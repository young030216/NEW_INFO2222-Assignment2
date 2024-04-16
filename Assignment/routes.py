from flask import render_template, url_for, flash, redirect, request, session, make_response
from Assignment import app, db, bcrypt, socketio
from Assignment.forms import Registeration, Login
from Assignment.models import User, Message, Friend, FriendRequest
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
    current_user_id= current_user.id
    pending_requests = FriendRequest.query.filter_by(receiver_id=current_user_id, accepted=False).all()

    if request.method == "POST":
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        if  join!= False and not code:
            return render_template('chathome.html', chat_error='Please enter a Room code.', current_user_name=current_user_name)
                   
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members":0, "message":[]}
        elif code not in rooms:
           return render_template('chathome.html', chat_error='Room dose not exist.', current_user_name=current_user_name)
        
        session["room"] = room
        session["name"] = current_user_name
        return redirect(url_for("room"))
    
    return render_template('chathome.html', title='chatroom', current_user_name=current_user_name, friend_requests=pending_requests)

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
    if friend_username in [friend.username for friend in current_user.friends]:
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




# chatroom
@app.route("/chatroom")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("chathome"))
    return render_template("chatroom.html", code=room, message=rooms[room]["message"])

# socket listening join event
@socketio.on('connect')
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    session["name"] = name
    join_room(room)
    # send join message to room
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1

# socket listening leave event
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    # send leave message to room
    send({"name": name, "message": "has left the room"}, to=room)

# socket listening sending message event
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    name = session.get("name")
    content = {
        "name": name,
        "message": data["data"]
    }
    # send message
    send(content, to=room)
    # save message for history
    rooms[room]["message"].append(content)
    print(f"{session.get('name')} said: {data['data']}")
