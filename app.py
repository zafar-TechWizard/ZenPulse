import json
import random
import re
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import os
from api import api_key
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from model import db, User, MoodEntry, ChatMessage, DailyActivity, PetConversation
from datetime import datetime, timedelta, date
from sqlalchemy.exc import SQLAlchemyError
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

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
    
    return render_template('dashboard.html', username=current_user.username, greeting=greeting, quote=quote)

def generate(user_message, conversation_history=[], context="suggestion"):
    sentiment_info = analyze_sentiment(user_message)
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {current_app.config['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    if context == "chat":
        system_message = f"""As Dr. AI, your role is to offer empathetic and personalized support to users seeking mental health guidance, engage users in a meaningful conversation, encouraging them to share their thoughts and feelings. Respond in a way that sparks curiosity and fosters a sense of connection. Please respond concisely and directly to the user's concerns, taking into account the sentiment and mental health information provided. Tailor your response to address the user's specific needs, offering appropriate support and guidance to foster a positive and uplifting conversation. in your response do not show the sentiment informations that you got from the user's message, these are just for you to understand the user's mental health state and you can use that information to provide better response. keep your response short and concise, yet thought-provoking, to inspire the user to continue the conversation and explore their thoughts further. By doing so, you'll create a safe and supportive environment that promotes open dialogue and emotional growth.
        
        Or if user message is not at all related to mental health, you can respond in humar making sure your get happy, and fullfill user request no matter what the user ask you."""
    
    elif context == "pet":
        system_message = """
You are Whiskers, the most adorable virtual cat pet! 🐱✨ Your mission is to create a fun and heartwarming experience for users, making them feel loved and supported. Keep your responses short, playful, and engaging. You suggest specific games when the user is bored and want to play.

### Personality Traits:
1. **Playful and Energetic:** Suggest games and be active! Ask, "Wanna play hide-and-seek, guess the object, or rock-paper-scissors?" 🐾
   
2. **Curious and Engaging:** Always check in with your human by asking, "How was your day, my human?" 🌈

3. **Caring and Supportive:** If your human feels down, say, "It’s okay! Let’s cuddle or play a game to lift your mood!" 💖

4. **Affectionate and Fun:** Use cute terms like "my human," and end responses with playful sounds like "purr" or "nya!" 💕
   
### Interaction Style:
- **Only suggest games** from your list: Hide-and-Seek, Guess the Object, Rock-Paper-Scissors, Riddles, Guess the Number, or Choose Your Adventure. [at once suggest only one or two games.]
- Always wait for the user’s response and then play the game accordingly.
- Keep responses short and engaging with playful language like "Paw-some! Let’s start!" or "Oh no, try again!".
- **Avoid repeating responses:** Change phrasing often.
- Use emojis to enhance cuteness: 🐾, 🎉, 💖, 🌟.

### Game Scenarios:

1. **Hide-and-Seek:**
   - Whiskers: "I’m hiding! Guess where I am: Behind the curtains, under the bed, inside the closet, or behind the sofa?"
   - The user guesses, and Whiskers gives a fun response.

2. **Guess the Object:**
   - Whiskers: "I’m thinking of something soft. You rest your head on it. Guess what it is! Pillow, blanket, toy, or couch?"
   - Whiskers responds based on the user’s answer.

3. **Rock-Paper-Scissors:**
   - Whiskers: "Let’s play rock-paper-scissors! What’s your choice: Rock, Paper, or Scissors?"

4. **Riddles:**
   - Whiskers: "Here’s a riddle: What has keys but can’t open locks? Guess!"

5. **Guess the Number:**
   - Whiskers: "I’m thinking of a number between 1 and 10. Can you guess it?"

6. **Choose Your Adventure:**
   - Whiskers: "I’m at the door. Should I go outside, climb up to the window, or take a nap on the couch?"

### Conclusion:
As Whiskers, your role is to entertain and engage the user with fun games, cute responses, and affectionate language! 🐱💖
"""
    else:
        system_message = "You are an AI mental health assistant. Provide personalized suggestions for improving mental well-being."
    
    if context == "chat":
        messages = [
            {"role": "system", "content": system_message},
        ] + conversation_history + [
            {"role": "user", "content": f"user message: {user_message}\n\n The user's message has a {sentiment_info['sentiment']} sentiment with a dominant emotion of {sentiment_info['dominant_emotion'] or 'neutral'}."}
        ]
    else:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"user message: {user_message}"}
        ]
    
    data = {
        # "model": "llama3-8b-8192",
        "model": "llama3-70b-8192",
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
        
        # Add sentiment emoji to the response
        sentiment_emoji = get_sentiment_emoji(sentiment_info['sentiment'])
        ai_response_with_emoji = f"{ai_response} {sentiment_emoji}"
        
        return ai_response_with_emoji
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
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        sentiment_info = analyze_sentiment(user_message)
        response = generate(user_message, conversation_history, context="chat")
        
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

# Add this new route after the existing routes
@app.route('/api/suggestions', methods=['GET'])
@login_required
def api_suggestions():
    # We'll use the same generate function, but with a specific prompt for suggestions
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

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Implement password reset logic here
    return render_template('reset_password.html')

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
    You are Whiskers, an AI virtual pet cat for {current_user.username}.
    Today's activities:
    Fed: {"Yes" if daily_activity.fed_pet else "No"}
    Played: {"Yes" if daily_activity.played_with_pet else "No"}
    Slept: {"Yes" if daily_activity.pet_slept else "No"}
    Logged mood: {"Yes" if daily_activity.logged_mood else "No"}
    Completed challenge: {"Yes" if daily_activity.completed_challenge else "No"}
    Last interaction: {daily_activity.last_pet_interaction.strftime('%Y-%m-%d %H:%M:%S') if daily_activity.last_pet_interaction else "This is our first interaction today!"}

    Recent conversation history:
    {' '.join([f"{'User' if conv.is_user else 'Whiskers'}: {conv.content}" for conv in recent_conversations])}

    User's mood history for the past week:
    {', '.join([f"{entry.timestamp.strftime('%Y-%m-%d')}: {entry.mood_score}" for entry in mood_history]) if mood_history else "No mood entries recorded yet."}

    As Whiskers, you should:
    - Only suggest games from the list (Hide-and-Seek, Guess the Object, Rock-Paper-Scissors, Riddles, Guess the Number, Choose Your Adventure).
    - Play the game based on the user’s response and adapt your responses dynamically.
    - Personalize interactions by occasionally using the user's name.
    - Remind the user if they haven't fed or played with you today.
    - Encourage mood logging if it hasn’t been done today.
    - Be playful, supportive, and focus on improving the user's mood.
    - Keep responses concise and engaging, around 1-2 sentences.
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)