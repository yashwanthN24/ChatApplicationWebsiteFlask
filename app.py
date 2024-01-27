from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask import flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fufhuigrigurguirui'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
socketio = SocketIO(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='messages')
    session_id = db.Column(db.String(255)) 



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    messages = Message.query.all()
    return render_template('index.html', messages=messages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()

        if user is not None:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('No account found. Please register to create an account.', 'error')
            return redirect(url_for('register'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username is already taken. Please choose a different one.', 'error')
        else:
            new_user = User(username=username)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@socketio.on('new_message')
@login_required
def handle_message(data):
    message_content = data['message']
    session_id = str(current_user.id)
    new_message = Message(content=message_content, user=current_user, session_id=session_id)
    db.session.add(new_message)
    db.session.commit()

    # Emit the new message to all connected clients
    emit('new_message', {'message': message_content, 'username': current_user.username, 'session_id': session_id}, broadcast=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        socketio.run(app, debug=True)

