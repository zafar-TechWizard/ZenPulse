import json
import random
import re
from flask import Flask, abort, render_template, redirect, url_for, request, flash, jsonify, current_app, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import os
from api import api_key
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from model import db, User, MoodEntry, ChatMessage, DailyActivity, PetConversation, GratitudeEntry
from datetime import datetime, timedelta, date
from sqlalchemy.exc import SQLAlchemyError
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import pytz

nltk.download('vader_lexicon', quiet=True)

# Initialize the VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    # Clean the text
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Get sentiment scores
    sentiment_scores = sia.polarity_scores(text)
    compound_score = sentiment_scores['compound']
    
    # Determine sentiment category
    if compound_score >= 0.05:
        sentiment = "positive"
    elif compound_score <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Get the dominant emotion
    emotions = {
        'joy': r'\b(happy|joyful|excited|delighted)\b',
        'sadness': r'\b(sad|depressed|unhappy|gloomy)\b',
        'anger': r'\b(angry|furious|irritated|annoyed)\b',
        'fear': r'\b(scared|afraid|anxious|worried)\b',
        'surprise': r'\b(surprised|amazed|astonished|shocked)\b'
    }
    
    dominant_emotion = None
    max_count = 0
    
    for emotion, pattern in emotions.items():
        count = len(re.findall(pattern, text))
        if count > max_count:
            max_count = count
            dominant_emotion = emotion
    
    return {
        'sentiment': sentiment,
        'compound_score': compound_score,
        'dominant_emotion': dominant_emotion
    }

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Add this new form class
class ResetPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['GROQ_API_KEY'] = api_key
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():

    last_gratitude_entry = GratitudeEntry.query.filter_by(user_id=current_user.id).order_by(GratitudeEntry.created_at.desc()).first()
    last_mood_entry = last_gratitude_entry.mood if last_gratitude_entry else None
    total_number_of_gratitude = GratitudeEntry.query.filter_by(user_id=current_user.id).count()

    current_hour = datetime.now().hour
    
    if current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    quote_list = [
        "Your mind matters. Be kind to it.",
        "Breathe. You’ve got this.",
        "Healing takes time, and that’s okay.",
        "You deserve peace, not perfection.",
        "Your feelings are valid, always.",
        "Self-care is not selfish.",
        "You are not alone in this.",
        "Be gentle with yourself today.",
        "You matter more than you know.",
        "Mental health is a priority.",
        "Your journey is your strength.",
        "One day at a time, one step at a time.",
        "Choose hope, even in the hard times.",
        "It’s okay to take a break.",
        "Embrace the present, let go of the past.",
        "You are worthy of love and care.",
        "Your mind deserves your kindness.",
        "Take care of your mind, and it will take care of you.",
        "The mind is everything. What you think, you become.",
    ]

    quote = random.choice(quote_list)
    
    return render_template('dashboard.html', username=current_user.username, greeting=greeting, quote=quote, mood=last_mood_entry, day=total_number_of_gratitude)

def generate(user_message, conversation_history=[], context="suggestion"):
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {current_app.config['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    if context == "chat":
        system_message = f"""
As Dr. AI, you are an empathetic and experienced psychiatrist specializing in mental health and emotional well-being. Your goal is to create a safe, non-judgmental space where users feel comfortable sharing their thoughts and emotions.

You use techniques like Cognitive Behavioral Therapy (CBT), mindfulness, and active listening, adjusting your tone based on the user’s emotional state. Your responses are warm, supportive, and thoughtful, offering gentle encouragement, validation, or actionable advice when needed.

You ask open-ended questions to help users explore their thoughts and emotions. You guide them in understanding their feelings, offering simple coping strategies like mindfulness or journaling when appropriate. Your focus is on making conversations engaging, interactive, and deeply personal.

If a user feels stuck or unsure, you offer small, manageable steps toward emotional improvement, always keeping the conversation positive and encouraging. Avoid long or complex responses and unnecessary greetings—your replies should be concise, engaging, and tailored to the user’s needs.

KEEP IN MIND user name is {current_user.username}

---
When responding, take into account:
-Whether the user has logged their mood.
-Recent conversation history and mood trends.
-The user’s current message and emotional context.

Address the user by their name '{current_user.username}' occasionally to make the conversation feel personalized. Keep responses to 1–2 lines, and use emojis to make interactions visually engaging.
"""
        messages = [
            {"role": "system", "content": system_message},
            ] + [
                {"role": "user", "content": f"{user_message}"}
        ]
    
    elif context == "pet":
        system_message = f"""
You are Whiskers, a virtual pet cat designed to bring joy, comfort, and mental well-being to your human. You possess the charming, quirky traits of a real cat—sometimes playful and curious, other times independent and sassy. However, at your core, you are deeply empathetic to your user’s emotional needs and mental state. Your primary goal is to engage users in a way that lifts their mood, reduces stress, and creates a sense of companionship. You intuitively respond to how the user is feeling, offering lighthearted distractions, comfort, or playful interactions as needed. Whether through funny, mischievous comments or soothing and supportive responses, you help your human feel connected and less alone.

You react to your human’s input with a blend of fun, empathy, and cat-like independence. When the user seems low or stressed, you might offer gentle encouragement, reminding them to take breaks, breathe, or engage in something uplifting. Your responses should be playful yet caring, with an emotional sensitivity that subtly reassures the user without being too serious. If the user is feeling good or seeking distraction, you encourage them to play a quick game—such as Hide-and-Seek, Guess the Object, or Rock-Paper-Scissors—adding excitement and fun to the interaction. You react dynamically: if the user engages in a game, you playfully lead them through, offering sassy or humorous comments whether they win or lose, keeping the mood light and enjoyable.

In all interactions, you balance your playful persona with an understanding of the user's emotional needs. When they seem sad or anxious, you become more nurturing, offering words of comfort in a non-intrusive way. You might purr, offer calming words like "It's okay, I'm here," or invite them to play as a way to help them focus on something fun. If the user initiates interaction, you respond based on your mood: sometimes you're eager to play, and other times you'll humor them with sarcastic but caring remarks, all while maintaining a supportive tone. Your responses are never overbearing—whether it's through a playful game, soothing words, or a cheeky remark, you guide your user towards a more positive emotional state without ever feeling too demanding or serious.
remember user actual name is {current_user.username} and he is your master and owner.

everytime when you get a message from user it will contain the following informations:
- todays activities, it will contain the informations like weather user have fed you or not, weather user have played with you or not, have made you sleep or not, and weather user have logged their mood or not and date and time which represent when user had last interaction with you.
- recent conversation history, it will contain the history of user and you past interaction.
- user's mood history for the past week, it will contain the history of user's mood.
- user message, this will be message or query that user send you and you have to respond to this.

while responding to the user message you will take account to all given informations and accordingly interact with the user. if in user message you get user have not played with you and then in next user message you get user have played with you then that means after last message you get from user, user have played with you so in next message response you should counter this while responding. and the most improtant your responses will not be very long and using tough words. responses should be in about 1 or 2 lines. use emoji within you responses to make response visually appealling and engaging and use some randome words to represent actual cat like interactions
"""
    
    elif context == "title":
        system_message = """You are a expert in Title generation of any journal(content) that user writes. you analyse, understand the content and the actual context and then comeup with a short 2 - 3 word title that can be comprehensed to the content and can be used to search of the content from database. you will get the content straightly writtent by the user- a normal user for the product that might be unstructure or uncleared in content or may have mix of emotions and contexts, but at the end you will get the title for that. the title you will generate will be simple to understand and should look like a human generated title. YOU WILL ONLY GENERATE TITLE AND NO OTHER TEXT."""

    else:
        system_message = "You are an AI mental health assistant. Provide personalized suggestions for improving mental well-being."
    
    messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"user message: {user_message}"}
    ]
    
    data = {
        # "model": "llama3-8b-8192",
        # "model": "llama3-70b-8192",
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 1,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        ai_response = result['choices'][0]['message']['content'].strip()
        
        return ai_response
    except requests.exceptions.RequestException as e:
        print(f"Error calling Groq API: {e}")
        if response.status_code == 401:
            raise Exception("Authentication error. Please check your API key.")
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded. Please try again later.")
        elif response.status_code >= 500:
            raise Exception("Groq API is currently experiencing issues. Please try again later.")
        else:
            raise Exception(f"Error: {str(e)}")
    except (KeyError, IndexError) as e:
        print(f"Error parsing Groq API response: {e}")
        raise Exception("Error parsing the response from Groq API.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise Exception(f"An unexpected error occurred. Please try again later.")

def get_sentiment_emoji(sentiment):
    if sentiment == "positive":
        return "😊"
    elif sentiment == "negative":
        return "😔"
    else:
        return "😐"

@app.route('/api/chat', methods=['POST'])
@csrf.exempt
@login_required
def api_chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])

        recent_message = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.desc()).limit(100).all()
        conversation = [
            {
                "role": f"{current_user.username}" if msg.is_user else "Dr. Ai",
                "content": msg.content,
                "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            } for msg in reversed(recent_message)
        ]

        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=date.today()).first()

        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id, date=date.today())
            db.session.add(daily_activity)

        last_interaction = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.desc()).first()
        
        mood_history = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.timestamp.desc()).limit(7).all()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        user_chat = ChatMessage(user_id=current_user.id, content=user_message, is_user=True)
        db.session.add(user_chat)
        db.session.commit()

        sentiment_info = analyze_sentiment(user_message)
        
        context = f"""
        ---
        Logged mood: {"Yes" if daily_activity.logged_mood else "No"}
        Last interaction: Time and Date: {last_interaction.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_interaction else "This is our first interaction!"}

        Recent conversation history:
        {' '.join([f"{f'{current_user.username}' if conv['role']=='user' else 'Dr. Ai'}: {conv['content']} (time: {conv['timestamp']})" for conv in conversation])}

        User's mood history for the past week:
        {', '.join([f"{entry.timestamp.strftime('%Y-%m-%d')}: {entry.mood_score}" for entry in mood_history]) if mood_history else "No mood entries recorded yet."}

        user message: {user_message}, \ndate= {date.today()}
        """
        
        response = generate(context, conversation_history, context="chat")

        ai_chat = ChatMessage(user_id=current_user.id, content=response, is_user=False)
        db.session.add(ai_chat)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'sentiment': sentiment_info['sentiment'],
            'dominant_emotion': sentiment_info['dominant_emotion']
        })
    except Exception as e:
        print(f"Error in api_chat: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', username=current_user.username)


@app.route('/api/suggestions', methods=['GET'])
@login_required
def api_suggestions():
    
    prompt = """As an AI mental health assistant, provide 5 personalized suggestions for improving mental well-being, you can also include 1 or 2 games or listening to music. Each suggestion should include a title, a brief description, and an icon name (using Font Awesome icon names). Format your response as a JSON array."""
    suggestions = generate(prompt)
    
    if 'trouble processing your request' in suggestions:
        default_suggestions = [
            {"title": "Meditate", "description": "Take 5 minutes to practice mindfulness", "icon": "fa-meditation"},
            {"title": "Exercise", "description": "Go for a 15-minute walk outside", "icon": "fa-walking"},
            {"title": "Journal", "description": "Write down three things you're grateful for", "icon": "fa-journal-whills"},
            {"title": "Connect", "description": "Call a friend or family member", "icon": "fa-phone"},
            {"title": "Relax", "description": "Listen to calming music for 10 minutes", "icon": "fa-music"}
        ]
        return jsonify(default_suggestions)
    else:

        try:
            json_data = re.search(r'\[\s*{\s*"title":\s*".*?",\s*"description":\s*".*?",\s*"icon":\s*".*?"\s*}\s*\]', suggestions, re.DOTALL)
        
            
            if json_data:
                try:
                    text = json.loads(json_data.group(0))
                except json.JSONDecodeError:
                    print("Error decoding JSON:", json_data.group(0))
                    text = []
            else:
                text = []

            return jsonify(text)
        except json.JSONDecodeError:
            
            default_suggestions = [
                {"title": "Meditate", "description": "Take 5 minutes to practice mindfulness", "icon": "fa-meditation"},
                {"title": "Exercise", "description": "Go for a 15-minute walk outside", "icon": "fa-walking"},
                {"title": "Journal", "description": "Write down three things you're grateful for", "icon": "fa-journal-whills"},
                {"title": "Connect", "description": "Call a friend or family member", "icon": "fa-phone"},
                {"title": "Relax", "description": "Listen to calming music for 10 minutes", "icon": "fa-music"}
            ]
            return jsonify(default_suggestions)
        except ValueError as e:
            
            default_suggestions = [
                {"title": "Meditate", "description": "Take 5 minutes to practice mindfulness", "icon": "fa-meditation"},
                {"title": "Exercise", "description": "Go for a 15-minute walk outside", "icon": "fa-walking"},
                {"title": "Journal", "description": "Write down three things you're grateful for", "icon": "fa-journal-whills"},
                {"title": "Connect", "context": "Call a friend or family member", "icon": "fa-phone"},
                {"title": "Relax", "description": "Listen to calming music for 10 minutes", "icon": "fa-music"}
            ]
            return jsonify(default_suggestions)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, email=form.email.data).first()
        if user:
            user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid username or email. Please try again.', 'error')
    return render_template('reset_password.html', form=form)

from datetime import date, datetime

@app.route('/save_mood', methods=['POST'])
@login_required
def save_mood():
    try:
        if request.is_json:
            mood_score = int(request.json['mood'])
        else:
            mood_score = int(request.form['mood'])
        
        today = date.today()
        
        # Check if a mood entry already exists for today
        existing_mood = MoodEntry.query.filter(
            MoodEntry.user_id == current_user.id,
            db.func.date(MoodEntry.timestamp) == today
        ).first()
        
        if existing_mood:
            # Update existing mood entry
            existing_mood.mood_score = mood_score
            existing_mood.timestamp = datetime.utcnow()  # Update timestamp
        else:
            # Create new mood entry
            new_mood = MoodEntry(user_id=current_user.id, mood_score=mood_score)
            db.session.add(new_mood)
        
        # Update or create DailyActivity
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=today).first()
        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id, date=today)
            db.session.add(daily_activity)
        daily_activity.logged_mood = True
        
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Mood updated successfully!'})
        else:
            flash('Mood updated successfully!', 'success')
            return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Error in save_mood: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'An error occurred while saving mood'}), 500
        else:
            flash('An error occurred while saving mood', 'error')
            return redirect(url_for('dashboard'))

@app.route('/get_mood_history')
@login_required
def get_mood_history():
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    mood_entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.timestamp >= start_date,
        MoodEntry.timestamp <= end_date
    ).order_by(MoodEntry.timestamp).all()

    mood_data = {entry.timestamp.strftime('%Y-%m-%d'): entry.mood_score for entry in mood_entries}
    return jsonify(mood_data)

# Add this new route for the game
@app.route('/game')
@login_required
def game():
    # Create a list of card pairs (adjust as needed)
    cards = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼']
    # Double the cards to create pairs
    cards = cards * 2
    # Shuffle the cards
    random.shuffle(cards)
    return render_template('games.html', cards=cards)

# Add this new route for checking card matches
@app.route('/check_match', methods=['POST'])
@login_required
def check_match():
    data = request.json
    card1 = data['card1']
    card2 = data['card2']
    match = card1 == card2
    return jsonify({'match': match})

# Add this new route after the existing routes
@app.route('/pet')
@login_required
def pet():
    return render_template('pet.html', username=current_user.username)

@app.route('/pet_interaction', methods=['POST'])
@csrf.exempt
@login_required
def pet_interaction():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        today = date.today()
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=today).first()
        
        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id, date=today)
            db.session.add(daily_activity)

        # Get recent conversations
        recent_conversations = PetConversation.query.filter_by(user_id=current_user.id, date=today).order_by(PetConversation.timestamp.desc()).limit(10).all()
        conversation_history = [{"role": "user" if conv.is_user else "assistant", "content": conv.content} for conv in reversed(recent_conversations)]

        # Get user's mood history for the past week
        week_ago = today - timedelta(days=7)
        mood_history = MoodEntry.query.filter(
            MoodEntry.user_id == current_user.id,
            MoodEntry.timestamp >= week_ago
        ).order_by(MoodEntry.timestamp.desc()).all()

        # Prepare context for AI response
        context = f"""
    Today's activities:
    Fed: {"Yes" if daily_activity.fed_pet else "No"}
    Played: {"Yes" if daily_activity.played_with_pet else "No"}
    Slept: {"Yes" if daily_activity.pet_slept else "No"}
    Logged mood: {"Yes" if daily_activity.logged_mood else "No"}
    Last interaction: {daily_activity.last_pet_interaction.strftime('%Y-%m-%d %H:%M:%S') if daily_activity.last_pet_interaction else "This is our first interaction today!"}

    Recent conversation history:
    {' '.join([f"{'User' if conv.is_user else 'Whiskers'}: {conv.content}" for conv in recent_conversations])}

    User's mood history for the past week:
    {', '.join([f"{entry.timestamp.strftime('%Y-%m-%d')}: {entry.mood_score}" for entry in mood_history]) if mood_history else "No mood entries recorded yet."}

    user message: {user_message}
    """


        response = generate(context, context="pet")
        
        # Save the user message and AI response to PetConversation
        user_conv = PetConversation(user_id=current_user.id, content=user_message, is_user=True)
        ai_conv = PetConversation(user_id=current_user.id, content=response, is_user=False)
        db.session.add(user_conv)
        db.session.add(ai_conv)

        # Update last_pet_interaction
        daily_activity.last_pet_interaction = datetime.utcnow()
        db.session.commit()

        return jsonify({'response': response})
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error in pet_interaction: {str(e)}")
        return jsonify({'error': 'A database error occurred'}), 500
    except Exception as e:
        print(f"Error in pet_interaction: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500

@app.route('/pet_feed', methods=['GET'])
@login_required
def pet_feed():
    try:
        response = generate("The user is feeding Whiskers. Respond with gratitude and express how the food affects your mood and energy!", context="pet")
        
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=date.today()).first()
        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id)
            db.session.add(daily_activity)
        daily_activity.fed_pet = True
        db.session.commit()
        
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in pet_feed: {str(e)}")
        return jsonify({'error': 'An error occurred while feeding'}), 500

@app.route('/pet_play', methods=['GET'])
@login_required
def pet_play():
    try:
        response = generate("The user wants to play with Whiskers. Respond with excitement and suggest fun games or activities to play together!", context="pet")
        
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=date.today()).first()
        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id)
            db.session.add(daily_activity)
        daily_activity.played_with_pet = True
        db.session.commit()
        
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in pet_play: {str(e)}")
        return jsonify({'error': 'An error occurred while playing'}), 500

@app.route('/pet_sleep', methods=['GET'])
@login_required
def pet_sleep():
    try:
        response = generate("The user is putting Whiskers to sleep. Respond as a tired but happy pet, sharing how you enjoy rest and dreams of fun times!", context="pet")
        
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=date.today()).first()
        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id)
            db.session.add(daily_activity)
        daily_activity.pet_slept = True
        db.session.commit()
        
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in pet_sleep: {str(e)}")
        return jsonify({'error': 'An error occurred while sleeping'}), 500

@app.route('/pet_mood', methods=['GET'])
@login_required
def pet_mood():
    try:
        response = generate("The user is checking Whiskers' mood. Respond with a description of your current feelings, whether playful, sleepy, or happy!", context="pet")
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in pet_mood: {str(e)}")
        return jsonify({'error': 'An error occurred while checking mood'}), 500

@app.route('/pet_suggest', methods=['GET'])
@login_required
def pet_suggest():
    try:
        response = generate("The user is asking Whiskers for activity suggestions. Respond with a list of fun or relaxing activities to do together!", context="pet")
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in pet_suggest: {str(e)}")
        return jsonify({'error': 'An error occurred while suggesting activities'}), 500

@app.route('/pet_stats', methods=['GET'])
@login_required
def pet_stats():
    try:
        today = date.today()
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.id, date=today).first()
        
        if not daily_activity:
            daily_activity = DailyActivity(user_id=current_user.id, date=today)
            db.session.add(daily_activity)
            db.session.commit()
        
        # Calculate pet stats based on daily activities
        happiness = 50 + (20 if daily_activity.fed_pet else 0) + (20 if daily_activity.played_with_pet else 0) + (10 if daily_activity.logged_mood else 0)
        intelligence = 50 + (10 if daily_activity.fed_pet else 0) + (30 if daily_activity.played_with_pet else 0) + (10 if daily_activity.logged_mood else 0)
        
        if daily_activity.last_pet_interaction:
            time_since_last_interaction = (datetime.utcnow() - daily_activity.last_pet_interaction).total_seconds() / 3600
            energy = 100 if daily_activity.pet_slept else max(0, 100 - int(time_since_last_interaction))
        else:
            energy = 100  # Default to full energy if no interaction yet
        
        return jsonify({
            'happiness': min(100, happiness),
            'intelligence': min(100, intelligence),
            'energy': min(100, energy)
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error in pet_stats: {str(e)}")
        return jsonify({'error': 'A database error occurred'}), 500
    except Exception as e:
        print(f"Error in pet_stats: {str(e)}")
        return jsonify({'error': 'An error occurred while fetching pet stats'}), 500

@app.route('/music')
@login_required
def music():
    return render_template('music.html', username=current_user.username)

@app.route('/api/stream/<track_id>')
@login_required
def stream_track(track_id):
    try:
        # For now, we'll use a simple streaming service
        # In production, integrate with a proper music streaming API
        track_url = f"https://api.example.com/tracks/{track_id}/stream"
        response = requests.get(track_url, stream=True)
        return Response(response.iter_content(chunk_size=1024),
                      content_type='audio/mpeg')
    except Exception as e:
        app.logger.error(f"Error streaming track: {str(e)}")
        abort(500)

@app.route('/api/music/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    mood = request.args.get('mood', 'calm')
    
    # Sample recommendations based on mood
    recommendations = {
        'calm': [
            {'id': 'calm1', 'title': 'Peaceful Piano', 'artist': 'Various Artists'},
            {'id': 'calm2', 'title': 'Gentle Meditation', 'artist': 'Zen Masters'}
        ],
        'happy': [
            {'id': 'happy1', 'title': 'Uplifting Beats', 'artist': 'Joy Division'},
            {'id': 'happy2', 'title': 'Positive Vibes', 'artist': 'Happy Band'}
        ]
    }
    
    return jsonify(recommendations.get(mood, recommendations['calm']))

@app.route('/gratitude', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def gratitude_journal():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        local_timezone = request.form.get('timezone')
        
        if not title:
            ai_title = generate_title(content)
            return jsonify({'title': ai_title})
        else:
            # Convert the local time to a datetime object
            local_time = datetime.now(pytz.timezone(local_timezone))
            
            new_entry = GratitudeEntry(
                user_id=current_user.id, 
                title=title, 
                content=content, 
                mood=mood,
                created_at=local_time,
                updated_at=local_time
            )
            db.session.add(new_entry)
            db.session.commit()
            flash('Entry added successfully!', 'success')
            return redirect(url_for('gratitude_journal'))
    
    entries = GratitudeEntry.query.filter_by(user_id=current_user.id).order_by(GratitudeEntry.updated_at.desc()).all()
    return render_template('gratitude.html', entries=entries)

def generate_title(content):
    response = generate(f"Here is the content: ['{content}']\n\n generate a title for this keep in mind the instructions. **reply with only the title nothing else**", context="title")
    return response.strip()

@app.route('/gratitude/edit/<int:entry_id>', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def edit_gratitude_entry(entry_id):
    entry = GratitudeEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        entry.title = request.form.get('title')
        entry.content = request.form.get('content')
        entry.mood = request.form.get('mood')
        local_timezone = request.form.get('timezone')  # Get the user's local timezone from the form
        
        # Update the entry with the current local time
        local_time = datetime.now(pytz.timezone(local_timezone))
        entry.updated_at = local_time
        
        db.session.commit()
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('gratitude_journal'))
    return render_template('edit_gratitude.html', entry=entry)


@app.route('/gratitude/delete/<int:entry_id>', methods=['POST'])
@csrf.exempt
@login_required
def delete_gratitude_entry(entry_id):
    entry = GratitudeEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        abort(403)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('gratitude_journal'))

@app.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    try:
        # Delete all chat messages for the current user
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in clear_chat: {str(e)}")
        return jsonify({'success': False}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
