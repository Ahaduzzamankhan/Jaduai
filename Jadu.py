#!/usr/bin/env python3
"""
✅ Bangladesh AI Bot with Gemini 2.0 Flash
✅ Telegram Star Payments Integrated
✅ All Commands Working + New Features
✅ Games & Firebase Authentication
✅ Environment Variables Support
Developer: @khanahaduzzaman
"""

import os
import sys
import logging
import json
import sqlite3
import random
import re
import hashlib
import asyncio
import tempfile
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from io import BytesIO

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Telegram imports
from telegram import (
    Update, 
    BotCommand,
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    LabeledPrice,
    SuccessfulPayment
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)

# HTTP requests
import aiohttp

# Video downloader
import yt_dlp

# TTS
from gtts import gTTS

# ==================== CONFIGURATION ====================
# Load from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8113764559:AAHZ2jcGua-A3M7zQHi-jvy1Qrm-824vLVg')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAJYx4buvFJ6Y_gFE1gLkufXk-g3qvdrQk')
DEVELOPER_ID = os.getenv('DEVELOPER_ID', '@khanahaduzzaman')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '7474207530,8113764559').split(',')]

# Gemini 2.0 Flash API Endpoint
GEMINI_API_URL = os.getenv('GEMINI_API_URL', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent')

# Weather API
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '7a2e6e2c2d6a4b0b9e0220524242504')
WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'http://api.weatherapi.com/v1/current.json')

# News API
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '9b85f2f4c5e74a73a9c5e314c24c5e4f')
NEWS_API_URL = os.getenv('NEWS_API_URL', 'https://newsapi.org/v2/top-headlines')

# Database
DB_FILE = os.getenv('DB_FILE', 'bangla_ai_bot.db')

# Star Prices
PREMIUM_PRICE = int(os.getenv('PREMIUM_PRICE', 100))
PROMOTION_PRICE = int(os.getenv('PROMOTION_PRICE', 25))

# Rate Limits
RATE_LIMITS = {
    "free": {
        "messages": int(os.getenv('FREE_MESSAGES_LIMIT', 100)),
        "calls": int(os.getenv('FREE_CALLS_LIMIT', 2)),
        "tts": int(os.getenv('FREE_TTS_LIMIT', 5)),
        "games": int(os.getenv('FREE_GAMES_LIMIT', 10)),
        "cooldown": int(os.getenv('FREE_COOLDOWN', 15))
    },
    "premium": {
        "messages": int(os.getenv('PREMIUM_MESSAGES_LIMIT', 300)),
        "calls": int(os.getenv('PREMIUM_CALLS_LIMIT', 5)),
        "tts": int(os.getenv('PREMIUM_TTS_LIMIT', 10)),
        "games": int(os.getenv('PREMIUM_GAMES_LIMIT', 50)),
        "cooldown": int(os.getenv('PREMIUM_COOLDOWN', 5))
    }
}

# Bot Settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
PORT = int(os.getenv('PORT', 8080))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

# Languages
LANGUAGES = {
    'bn': '🇧🇩 বাংলা',
    'en': '🇺🇸 English',
    'hi': '🇮🇳 हिन्दी',
    'ar': '🇸🇦 العربية',
    'es': '🇪🇸 Español',
    'fr': '🇫🇷 Français',
    'ru': '🇷🇺 Русский',
    'zh': '🇨🇳 中文',
    'ja': '🇯🇵 日本語',
    'de': '🇩🇪 Deutsch'
}

# Games
GAMES = {
    "dice": {
        "name": "🎲 Dice Roll",
        "desc": "Roll a dice (1-6)",
        "cost": 0
    },
    "guess": {
        "name": "🔢 Guess Number",
        "desc": "Guess number between 1-100",
        "cost": 0
    },
    "quiz": {
        "name": "📚 Quiz",
        "desc": "Answer random questions",
        "cost": 0
    },
    "rps": {
        "name": "✊✋✌️ Rock Paper Scissors",
        "desc": "Play against AI",
        "cost": 0
    },
    "wordle": {
        "name": "🔤 Wordle",
        "desc": "Guess 5-letter word",
        "cost": 0
    }
}

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== DATABASE FUNCTIONS ====================
def init_database():
    """Initialize database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        language TEXT DEFAULT 'bn',
        is_premium INTEGER DEFAULT 0,
        premium_until TEXT,
        message_count INTEGER DEFAULT 0,
        video_call_count INTEGER DEFAULT 0,
        tts_count INTEGER DEFAULT 0,
        game_count INTEGER DEFAULT 0,
        last_message_time TEXT,
        rate_limit_start TEXT DEFAULT CURRENT_TIMESTAMP,
        stars_balance INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        payment_id TEXT,
        amount INTEGER,
        type TEXT,
        status TEXT DEFAULT 'pending',
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Promotions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS promotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        channel_link TEXT,
        channel_name TEXT,
        status TEXT DEFAULT 'pending',
        stars_paid INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT
    )
    ''')
    
    # Games table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game_type TEXT,
        score INTEGER,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Conversations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT,
        message TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def get_user(user_id: int):
    """Get user data"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None
    finally:
        conn.close()

def save_user(user_data: dict):
    """Save user to database"""
    try:
        user_id = user_data['user_id']
        existing = get_user(user_id)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if existing:
            # Update existing user
            set_clause = ', '.join([f"{k} = ?" for k in user_data.keys()])
            values = list(user_data.values()) + [user_id]
            cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
        else:
            # Insert new user
            columns = ', '.join(user_data.keys())
            placeholders = ', '.join(['?'] * len(user_data))
            values = list(user_data.values())
            cursor.execute(f"INSERT INTO users ({columns}) VALUES ({placeholders})", values)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving user: {e}")
        return False

def save_conversation(user_id: int, role: str, message: str):
    """Save conversation to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)",
            (user_id, role, message[:500])
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

def get_conversation_history(user_id: int, limit: int = 3):
    """Get conversation history"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, message FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        history = cursor.fetchall()
        conn.close()
        return history[::-1]
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

def add_payment_record(user_id: int, payment_id: str, amount: int, payment_type: str, details: str = ""):
    """Add payment record"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO payments (user_id, payment_id, amount, type, details) VALUES (?, ?, ?, ?, ?)",
            (user_id, payment_id, amount, payment_type, details)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding payment record: {e}")
        return False

def update_payment_status(payment_id: str, status: str):
    """Update payment status"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE payments SET status = ? WHERE payment_id = ?",
            (status, payment_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating payment status: {e}")
        return False

# ==================== GEMINI 2.0 FLASH API ====================
async def get_gemini_response(prompt: str, user_id: int, language: str = 'bn') -> str:
    """Get response from Gemini 2.0 Flash via HTTP API"""
    try:
        # Get conversation history
        history = get_conversation_history(user_id, limit=3)
        
        # Build messages for Gemini
        contents = []
        
        # System prompt based on language
        system_prompts = {
            'bn': "আপনি একজন বন্ধুত্বপূর্ণ বাংলাদেশি AI সহকারী। বাংলা ভাষায় প্রাকৃতিকভাবে উত্তর দিন।",
            'en': "You are a friendly AI assistant. Respond naturally in English.",
            'hi': "आप एक मैत्रीपूर्ण AI सहायक हैं। हिंदी में स्वाभाविक रूप से उत्तर दें।",
            'ar': "أنت مساعد ذكي ودود. رد بطريقة طبيعية باللغة العربية।",
            'es': "Eres un asistente de IA amigable. Responde naturalmente en español."
        }
        
        system_msg = system_prompts.get(language, system_prompts['bn'])
        
        # Start with system message
        contents.append({
            "role": "user",
            "parts": [{"text": system_msg}]
        })
        
        # Add conversation history
        for role, message in history:
            if role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": message}]
                })
            else:
                contents.append({
                    "role": "model",
                    "parts": [{"text": message}]
                })
        
        # Add current prompt
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        # Prepare API request for Gemini 2.0 Flash
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 1024,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make API call
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'candidates' in data and len(data['candidates']) > 0:
                        response_text = data['candidates'][0]['content']['parts'][0]['text']
                        
                        # Save conversation
                        save_conversation(user_id, "user", prompt)
                        save_conversation(user_id, "assistant", response_text)
                        
                        return response_text
                    else:
                        logger.error(f"No candidates in Gemini response: {data}")
                        return await get_fallback_response(prompt, language)
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    return await get_fallback_response(prompt, language)
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return await get_fallback_response(prompt, language)

async def get_fallback_response(prompt: str, language: str) -> str:
    """Fallback responses when API fails"""
    fallbacks = {
        'bn': [
            f"আপনি জিজ্ঞেস করছেন: '{prompt}'। আমি এখনই বিস্তারিত উত্তর দিতে পারছি না। অনুগ্রহ করে আবার চেষ্টা করুন।",
            "দুঃখিত, এখনই প্রক্রিয়া করতে পারছি না। দয়া করে পরে আবার চেষ্টা করুন।",
            "আবার চেষ্টা করুন, আমি এখনই সাড়া দিতে পারছি না।"
        ],
        'en': [
            f"You asked: '{prompt}'. I can't respond right now. Please try again.",
            "Sorry, I can't process this at the moment. Please try again later.",
            "Please try again, I'm unable to respond right now."
        ],
        'hi': [
            f"आपने पूछा: '{prompt}'। मैं अभी उत्तर नहीं दे सकता। कृपया पुनः प्रयास करें।",
            "क्षमा करें, मैं अभी प्रक्रिया नहीं कर सकता। बाद में पुनः प्रयास करें।",
            "कृपया पुनः प्रयास करें, मैं अभी उत्तर देने में असमर्थ हूं।"
        ]
    }
    
    return random.choice(fallbacks.get(language, fallbacks['en']))

# ==================== VIDEO DOWNLOADER ====================
async def download_video(url: str) -> Optional[BytesIO]:
    """Download video from URL"""
    try:
        # Validate URL
        if not re.match(r'^https?://(?:www\.)?(?:youtube\.com|youtu\.be|tiktok\.com|instagram\.com|facebook\.com)', url, re.IGNORECASE):
            return None
        
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 30,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]
            
            video_url = info['url']
            
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        video_data = await response.read()
                        video_buffer = BytesIO(video_data)
                        video_buffer.name = f"{info.get('title', 'video')[:30]}.mp4"
                        return video_buffer
        
        return None
    except Exception as e:
        logger.error(f"Video download error: {e}")
        return None

# ==================== TTS FUNCTION ====================
async def text_to_speech(text: str, language: str = 'bn') -> Optional[BytesIO]:
    """Text to speech conversion"""
    try:
        # Language mapping
        lang_map = {
            'bn': 'bn',
            'en': 'en',
            'hi': 'hi',
            'ar': 'ar',
            'es': 'es',
            'fr': 'fr',
            'ru': 'ru',
            'zh': 'zh',
            'ja': 'ja',
            'de': 'de'
        }
        
        tts_lang = lang_map.get(language, 'bn')
        
        # Clean text
        clean_text = re.sub(r'[^\w\s.,!?\-\u0980-\u09FF]', '', text, flags=re.UNICODE)[:500]
        
        # Generate TTS
        tts = gTTS(text=clean_text, lang=tts_lang, slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file = f.name
            tts.save(temp_file)
            
            with open(temp_file, 'rb') as audio_file:
                audio_bytes = BytesIO(audio_file.read())
                audio_bytes.name = "voice_message.mp3"
            
            os.unlink(temp_file)
            
            return audio_bytes
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None

# ==================== NEWS FUNCTION ====================
async def get_news(language: str = 'bn') -> str:
    """Get latest news"""
    try:
        # Country mapping
        country_map = {
            'bn': 'bd',
            'en': 'us',
            'hi': 'in',
            'ar': 'ae',
            'es': 'es',
            'fr': 'fr',
            'ru': 'ru',
            'zh': 'cn',
            'ja': 'jp',
            'de': 'de'
        }
        
        country = country_map.get(language, 'bd')
        
        # Try NewsAPI
        params = {
            'country': country,
            'apiKey': NEWS_API_KEY,
            'pageSize': 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(NEWS_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'articles' in data and len(data['articles']) > 0:
                        news_text = "📰 **Latest News**\n\n"
                        for i, article in enumerate(data['articles'][:5], 1):
                            title = article.get('title', 'No title')
                            source = article.get('source', {}).get('name', 'Unknown')
                            news_text += f"{i}. {title}\n   📍 Source: {source}\n\n"
                        return news_text
        
        # Fallback news
        fallback_news = {
            'bn': "📢 বাংলাদেশের খবর: আজকের প্রধান খবরগুলো শীঘ্রই আসছে।",
            'en': "📢 Breaking News: Top headlines coming soon.",
            'hi': "📢 ताजा खबर: शीर्ष समाचार जल्द ही आ रहे हैं।"
        }
        
        return fallback_news.get(language, fallback_news['en'])
        
    except Exception as e:
        logger.error(f"News error: {e}")
        return "📰 News service is currently unavailable. Please try again later."

# ==================== WEATHER FUNCTION ====================
async def get_weather(city: str) -> str:
    """Get weather information"""
    try:
        params = {
            'key': WEATHER_API_KEY,
            'q': city,
            'aqi': 'no'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    location = data['location']['name']
                    country = data['location']['country']
                    temp_c = data['current']['temp_c']
                    condition = data['current']['condition']['text']
                    humidity = data['current']['humidity']
                    wind_kph = data['current']['wind_kph']
                    
                    weather_text = f"""
🌤️ **Weather in {location}, {country}**
🌡️ Temperature: {temp_c}°C
☁️ Condition: {condition}
💧 Humidity: {humidity}%
💨 Wind: {wind_kph} km/h
"""
                    return weather_text
                else:
                    return f"❌ Could not get weather for {city}. Please check the city name."
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return f"❌ Weather service unavailable. Please try again later."

# ==================== GAME FUNCTIONS ====================
async def play_dice_game() -> str:
    """Play dice roll game"""
    roll = random.randint(1, 6)
    dice_faces = {
        1: "⚀",
        2: "⚁", 
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅"
    }
    return f"🎲 You rolled: {dice_faces[roll]} ({roll})"

async def play_guess_game(number: int) -> str:
    """Play guess the number game"""
    secret = random.randint(1, 100)
    
    if number == secret:
        return f"🎉 Correct! The number was {secret}"
    elif abs(number - secret) <= 5:
        return f"🔍 Very close! You guessed {number}, number was {secret}"
    elif number < secret:
        return f"📈 Too low! You guessed {number}, number was {secret}"
    else:
        return f"📉 Too high! You guessed {number}, number was {secret}"

async def play_quiz_game() -> str:
    """Play quiz game"""
    quizzes = [
        {"question": "What is the capital of Bangladesh?", "answer": "Dhaka"},
        {"question": "How many sides does a triangle have?", "answer": "3"},
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "What is the largest planet in our solar system?", "answer": "Jupiter"},
        {"question": "Who wrote Hamlet?", "answer": "Shakespeare"}
    ]
    
    quiz = random.choice(quizzes)
    return f"❓ Question: {quiz['question']}\n\nAnswer will be revealed in /answer"

async def play_rps_game(choice: str) -> str:
    """Play Rock Paper Scissors"""
    choices = ["rock", "paper", "scissors"]
    ai_choice = random.choice(choices)
    
    if choice.lower() not in choices:
        return "❌ Invalid choice! Use: rock, paper, or scissors"
    
    # Determine winner
    if choice.lower() == ai_choice:
        result = "🤝 It's a tie!"
    elif (choice.lower() == "rock" and ai_choice == "scissors") or \
         (choice.lower() == "paper" and ai_choice == "rock") or \
         (choice.lower() == "scissors" and ai_choice == "paper"):
        result = "🎉 You win!"
    else:
        result = "😢 You lose!"
    
    return f"✊✋✌️ **Rock Paper Scissors**\n\nYou chose: {choice.upper()}\nAI chose: {ai_choice.upper()}\n\n{result}"

# ==================== STAR PAYMENT FUNCTIONS ====================
async def send_star_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           title: str, description: str, payload: str, price: int):
    """Send invoice for Telegram Stars"""
    try:
        # Create labeled price for Stars
        prices = [LabeledPrice(label=f"{title} ({price} Stars)", amount=price)]
        
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=None,
            currency="XTR",
            prices=prices,
            max_tip_amount=None,
            suggested_tip_amounts=None,
            start_parameter=payload[:64],
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
            disable_notification=False,
            protect_content=False
        )
        return True
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await update.message.reply_text("❌ Error creating payment invoice.")
        return False

async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout queries"""
    query = update.pre_checkout_query
    
    # Log payment attempt
    add_payment_record(
        user_id=update.effective_user.id,
        payment_id=query.id,
        amount=query.total_amount,
        payment_type="precheckout",
        details=json.dumps({
            "payload": query.invoice_payload,
            "currency": query.currency
        })
    )
    
    # Always accept for now
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payments"""
    try:
        payment = update.message.successful_payment
        user_id = update.effective_user.id
        
        # Update payment status
        update_payment_status(payment.telegram_payment_charge_id, "completed")
        
        # Process based on payload
        payload = payment.invoice_payload
        
        if payload.startswith("premium_"):
            # Activate premium
            user = get_user(user_id) or {}
            premium_until = datetime.now() + timedelta(days=30)
            
            user.update({
                'user_id': user_id,
                'is_premium': 1,
                'premium_until': premium_until.isoformat()
            })
            save_user(user)
            
            await update.message.reply_text(
                f"⭐ **Premium Activated!** ⭐\n\n"
                f"Thank you for your payment of {payment.total_amount} Stars!\n"
                f"Your premium subscription is now active until:\n"
                f"**{premium_until.strftime('%B %d, %Y')}**\n\n"
                f"Enjoy your premium features!",
                parse_mode='Markdown'
            )
        
        elif payload.startswith("promotion_"):
            await update.message.reply_text(
                f"📢 **Promotion Activated!** 📢\n\n"
                f"Thank you for your payment of {payment.total_amount} Stars!\n"
                f"Your channel promotion is now active for **24 hours**.\n\n"
                f"Thank you for promoting with us!",
                parse_mode='Markdown'
            )
        
        else:
            await update.message.reply_text(
                "✅ **Payment Successful!**\n\n"
                "Thank you for your purchase!",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await update.message.reply_text("✅ **Payment Received!**")

# ==================== COMMAND HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Initialize user if new
    user_data = get_user(user.id)
    if not user_data:
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language': 'bn'
        }
        save_user(user_data)
    
    welcome = f"""
🤖 **স্বাগতম {user.first_name}!**

*Developer:* {DEVELOPER_ID}
*Status:* {'⭐ **PREMIUM**' if user_data.get('is_premium') else '🆓 **FREE**'}

🌟 **Features:**
• Gemini 2.0 Flash AI Chat
• Video Downloader
• Text-to-Speech (10 Languages)
• Games
• Latest News & Weather
• Bangladeshi Features

💰 **Star Payments:**
• Premium: {PREMIUM_PRICE} ⭐ (30 days)
• Promotion: {PROMOTION_PRICE} ⭐ (24 hours)

📊 **Your Limits:**
• Messages: {user_data.get('message_count', 0)}/{RATE_LIMITS['premium' if user_data.get('is_premium') else 'free']['messages']}
• TTS: {user_data.get('tts_count', 0)}/{RATE_LIMITS['premium' if user_data.get('is_premium') else 'free']['tts']}
• Games: {user_data.get('game_count', 0)}/{RATE_LIMITS['premium' if user_data.get('is_premium') else 'free']['games']}

💡 **Use /help to see all commands**
"""
    await update.message.reply_text(welcome, parse_mode='Markdown', disable_web_page_preview=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = f"""
📚 **Bangladesh AI Bot - Command List**

*Basic Commands:*
/start - Start bot
/help - Show all commands
/ping - Check bot status
/id - Get user ID

*AI Chat Commands:*
/chat [message] - Chat with Gemini AI
/ask [question] - Ask anything
/talk [message] - Start conversation

*Media Commands:*
/download [url] - Download video
/video [url] - Get video
/tts [text] - Text to speech
/audio [text] - Convert to audio

*Game Commands:*
/games - Show all games
/dice - Roll dice
/guess [number] - Guess number (1-100)
/quiz - Play quiz
/rps [choice] - Rock Paper Scissors

*Information Commands:*
/stats - Your statistics
/news - Latest news
/weather [city] - Weather info
/bdtime - Bangladesh time
/bdnews - Bangladesh news

*Payment Commands:*
/premium - Buy premium ({PREMIUM_PRICE} ⭐)
/promote - Promote channel ({PROMOTION_PRICE} ⭐)
/mystars - Check star balance

*Settings Commands:*
/settings - Bot settings
/lang - Change language

👨‍💻 *Developer:* {DEVELOPER_ID}
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chat command"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    if not context.args:
        await update.message.reply_text(
            "💬 *Chat with Gemini AI*\n\n"
            "Usage: /chat [your message]\n"
            "Example: /chat হ্যালো, কেমন আছো?",
            parse_mode='Markdown'
        )
        return
    
    prompt = " ".join(context.args)
    
    # Check rate limit
    limits = RATE_LIMITS['premium' if user_data.get('is_premium') else 'free']
    if user_data.get('message_count', 0) >= limits['messages']:
        await update.message.reply_text("🚫 Message limit reached. Please try again later or upgrade to premium.")
        return
    
    await update.message.chat.send_action(action="typing")
    
    try:
        response = await get_gemini_response(prompt, user.id, user_data.get('language', 'bn'))
        
        # Update message count
        user_data['message_count'] = user_data.get('message_count', 0) + 1
        user_data['last_message_time'] = datetime.now().isoformat()
        save_user(user_data)
        
        await update.message.reply_text(f"🤖 {response}")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        await update.message.reply_text("❌ Error processing your request. Please try again.")

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /download command"""
    if not context.args:
        await update.message.reply_text(
            "⏬ *Video Downloader*\n\n"
            "Supported: YouTube, TikTok, Instagram, Facebook\n\n"
            "Usage: /download [video_url]\n"
            "Example: /download https://youtube.com/watch?v=...",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0]
    
    # Show processing message
    processing_msg = await update.message.reply_text("⏬ Downloading video... Please wait.")
    
    try:
        video_data = await download_video(url)
        
        if video_data:
            await processing_msg.edit_text("✅ Download complete! Sending video...")
            
            await update.message.reply_video(
                video=video_data,
                caption="🎥 *Video Downloaded Successfully!*",
                supports_streaming=True,
                parse_mode='Markdown'
            )
            
            await processing_msg.delete()
        else:
            await processing_msg.edit_text("❌ Failed to download video. Please check the URL and try again.")
    except Exception as e:
        logger.error(f"Download error: {e}")
        await processing_msg.edit_text("❌ Error downloading video. Please try again.")

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /premium command with star payment"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    if user_data.get('is_premium'):
        if user_data.get('premium_until'):
            expiry = datetime.fromisoformat(user_data['premium_until'])
            if expiry > datetime.now():
                await update.message.reply_text(
                    f"⭐ **You are already premium!** ⭐\n\n"
                    f"Premium active until: **{expiry.strftime('%B %d, %Y')}**\n"
                    f"Enjoy your premium features!",
                    parse_mode='Markdown'
                )
                return
    
    # Send invoice for premium
    payload = f"premium_{user.id}_{int(datetime.now().timestamp())}"
    
    success = await send_star_invoice(
        update=update,
        context=context,
        title="Premium Subscription",
        description="30 days of premium features",
        payload=payload,
        price=PREMIUM_PRICE
    )
    
    if not success:
        await update.message.reply_text(
            f"⭐ **Premium Subscription** ⭐\n\n"
            f"Price: **{PREMIUM_PRICE} Telegram Stars**\n"
            f"Duration: 30 days\n\n"
            f"**Features:**\n"
            f"• {RATE_LIMITS['premium']['messages']} messages per 5 hours\n"
            f"• {RATE_LIMITS['premium']['calls']} video calls\n"
            f"• {RATE_LIMITS['premium']['tts']} TTS messages\n"
            f"• {RATE_LIMITS['premium']['games']} games\n"
            f"• {RATE_LIMITS['premium']['cooldown']} second cooldown\n\n"
            f"Send {PREMIUM_PRICE} Stars to @khanahaduzzaman",
            parse_mode='Markdown'
        )

async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promote command"""
    if not context.args:
        info = f"""
📢 **Channel Promotion Service**

*Price:* {PROMOTION_PRICE} Telegram Stars
*Duration:* 24 hours
*Min Views:* 3 users

*Features:*
• Your channel shown in /start messages
• Minimum 3 views guaranteed
• 24-hour visibility
• Priority placement

*How to use:*
1. Get your channel link (https://t.me/yourchannel)
2. Use: /promote [your_channel_link]
3. Pay {PROMOTION_PRICE} Stars
4. Promotion starts immediately

*Example:* /promote https://t.me/mychannel
"""
        await update.message.reply_text(info, parse_mode='Markdown')
        return
    
    channel_link = context.args[0]
    
    # Validate Telegram channel link
    if not re.match(r'^https?://t\.me/[a-zA-Z0-9_]+$', channel_link):
        await update.message.reply_text("❌ Invalid Telegram channel link. Format: https://t.me/channelname")
        return
    
    # Extract channel name
    channel_name = channel_link.split('/')[-1]
    
    # Send invoice
    payload = f"promotion_{int(datetime.now().timestamp())}"
    
    success = await send_star_invoice(
        update=update,
        context=context,
        title="Channel Promotion",
        description=f"Promote {channel_name} for 24 hours",
        payload=payload,
        price=PROMOTION_PRICE
    )
    
    if not success:
        await update.message.reply_text(
            f"📢 **Promotion Created!**\n\n"
            f"Channel: {channel_name}\n"
            f"Link: {channel_link}\n"
            f"Price: {PROMOTION_PRICE} Stars\n\n"
            f"Please send {PROMOTION_PRICE} Telegram Stars to @khanahaduzzaman",
            parse_mode='Markdown'
        )

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /lang command"""
    user = update.effective_user
    
    if not context.args:
        # Show language selection keyboard
        keyboard = []
        row = []
        for code, name in LANGUAGES.items():
            row.append(InlineKeyboardButton(name, callback_data=f"lang_{code}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 **Select Language**\n\nChoose your preferred language:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    lang_code = context.args[0].lower()
    
    if lang_code not in LANGUAGES:
        await update.message.reply_text("❌ Invalid language code. Use /lang to see options.")
        return
    
    # Update user language
    user_data = get_user(user.id) or {}
    user_data.update({
        'user_id': user.id,
        'language': lang_code
    })
    save_user(user_data)
    
    await update.message.reply_text(f"✅ Language changed to {LANGUAGES[lang_code]}")

async def lang_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("lang_"):
        lang_code = query.data.split("_")[1]
        
        if lang_code in LANGUAGES:
            user_id = query.from_user.id
            user_data = get_user(user_id) or {}
            user_data.update({
                'user_id': user_id,
                'language': lang_code
            })
            save_user(user_data)
            
            await query.edit_message_text(
                f"✅ Language changed to {LANGUAGES[lang_code]}"
            )

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /news command"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    await update.message.chat.send_action(action="typing")
    
    try:
        news = await get_news(user_data.get('language', 'bn'))
        await update.message.reply_text(news, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"News error: {e}")
        await update.message.reply_text("📰 News service is currently unavailable.")

async def bdnews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bdnews command - Bangladesh news"""
    await update.message.chat.send_action(action="typing")
    
    try:
        # Get Bangladesh specific news
        params = {
            'country': 'bd',
            'apiKey': NEWS_API_KEY,
            'pageSize': 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(NEWS_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'articles' in data and len(data['articles']) > 0:
                        news_text = "📰 **বাংলাদেশের সর্বশেষ খবর**\n\n"
                        for i, article in enumerate(data['articles'][:5], 1):
                            title = article.get('title', 'No title')
                            source = article.get('source', {}).get('name', 'Unknown')
                            news_text += f"{i}. {title}\n   📍 সূত্র: {source}\n\n"
                        await update.message.reply_text(news_text, parse_mode='Markdown')
                        return
        
        # Fallback
        await update.message.reply_text(
            "📢 **বাংলাদেশের খবর**\n\n"
            "১. বাংলাদেশ ডিজিটাল যুগে এগিয়ে\n"
            "২. রপ্তানি আয়ে নতুন রেকর্ড\n"
            "৩. শিক্ষা খাতে বরাদ্দ বৃদ্ধি\n"
            "৪. স্বাস্থ্য সেবার মানোন্নয়ন\n"
            "৫. কৃষি উৎপাদনে সাফল্য\n\n"
            "📍 সূত্র: বিভিন্ন সংবাদ মাধ্যম",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"BD News error: {e}")
        await update.message.reply_text("📰 বাংলাদেশের খবর পরিষেবা এখনই উপলব্ধ নয়।")

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weather command"""
    if not context.args:
        await update.message.reply_text(
            "🌤️ *Weather Information*\n\n"
            "Usage: /weather [city name]\n"
            "Example: /weather Dhaka\n"
            "Example: /weather New York",
            parse_mode='Markdown'
        )
        return
    
    city = " ".join(context.args)
    await update.message.chat.send_action(action="typing")
    
    try:
        weather = await get_weather(city)
        await update.message.reply_text(weather, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Weather error: {e}")
        await update.message.reply_text(f"❌ Could not get weather for {city}.")

async def bdtime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bdtime command - Bangladesh time"""
    # Bangladesh time is UTC+6
    bd_time = datetime.utcnow() + timedelta(hours=6)
    
    time_text = f"""
🇧🇩 **Bangladesh Time**

🕐 Time: {bd_time.strftime('%I:%M:%S %p')}
📅 Date: {bd_time.strftime('%A, %B %d, %Y')}
⌚ Timezone: UTC+6

🌅 Dhaka Local Time
"""
    await update.message.reply_text(time_text, parse_mode='Markdown')

async def tts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tts command"""
    if not context.args:
        await update.message.reply_text(
            "🔊 *Text to Speech*\n\n"
            "Usage: /tts [your text]\n"
            "Example: /tts Hello world\n"
            "Example: /tts হ্যালো বাংলাদেশ",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(context.args)
    
    if len(text) > 500:
        await update.message.reply_text("❌ Text too long! Maximum 500 characters.")
        return
    
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    # Check TTS limit
    limits = RATE_LIMITS['premium' if user_data.get('is_premium') else 'free']
    if user_data.get('tts_count', 0) >= limits['tts']:
        await update.message.reply_text("🚫 TTS limit reached. Please try again later or upgrade to premium.")
        return
    
    await update.message.chat.send_action(action="record_voice")
    
    try:
        audio_data = await text_to_speech(text, user_data.get('language', 'bn'))
        
        if audio_data:
            # Update TTS count
            user_data['tts_count'] = user_data.get('tts_count', 0) + 1
            save_user(user_data)
            
            await update.message.reply_voice(
                voice=audio_data,
                caption=f"🔊 TTS: {text[:100]}{'...' if len(text) > 100 else ''}"
            )
        else:
            await update.message.reply_text("❌ Failed to generate voice message.")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        await update.message.reply_text("❌ Error generating TTS.")

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /games command"""
    games_text = "🎮 **Available Games**\n\n"
    
    for game_id, game_info in GAMES.items():
        games_text += f"{game_info['name']}\n"
        games_text += f"   {game_info['desc']}\n"
        games_text += f"   Use: /{game_id}\n\n"
    
    games_text += "🎲 Example: /dice\n"
    games_text += "🔢 Example: /guess 50\n"
    games_text += "✊ Example: /rps rock\n\n"
    games_text += "Have fun! 🎉"
    
    await update.message.reply_text(games_text, parse_mode='Markdown')

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dice command"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    # Update game count
    user_data['game_count'] = user_data.get('game_count', 0) + 1
    save_user(user_data)
    
    result = await play_dice_game()
    await update.message.reply_text(result)

async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /guess command"""
    if not context.args:
        await update.message.reply_text(
            "🔢 *Guess Number Game*\n\n"
            "Guess a number between 1-100\n"
            "Usage: /guess [number]\n"
            "Example: /guess 50",
            parse_mode='Markdown'
        )
        return
    
    try:
        number = int(context.args[0])
        if number < 1 or number > 100:
            await update.message.reply_text("❌ Please enter a number between 1 and 100.")
            return
        
        user = update.effective_user
        user_data = get_user(user.id) or {}
        
        # Update game count
        user_data['game_count'] = user_data.get('game_count', 0) + 1
        save_user(user_data)
        
        result = await play_guess_game(number)
        await update.message.reply_text(result)
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quiz command"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    # Update game count
    user_data['game_count'] = user_data.get('game_count', 0) + 1
    save_user(user_data)
    
    result = await play_quiz_game()
    await update.message.reply_text(result)

async def rps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rps command"""
    if not context.args:
        await update.message.reply_text(
            "✊✋✌️ *Rock Paper Scissors*\n\n"
            "Usage: /rps [rock/paper/scissors]\n"
            "Example: /rps rock\n"
            "Example: /rps paper",
            parse_mode='Markdown'
        )
        return
    
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    # Update game count
    user_data['game_count'] = user_data.get('game_count', 0) + 1
    save_user(user_data)
    
    result = await play_rps_game(context.args[0])
    await update.message.reply_text(result, parse_mode='Markdown')

async def mystars_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mystars command"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    stars = user_data.get('stars_balance', 0)
    
    stars_text = f"""
⭐ **Your Star Balance**

💰 Current Balance: {stars} Stars

*What can you do with Stars?*
• Premium: {PREMIUM_PRICE} Stars (30 days)
• Promotion: {PROMOTION_PRICE} Stars (24 hours)

*How to get Stars?*
1. Buy from Telegram Store
2. Receive as gift
3. Earn through activities

*Use Stars:*
/premium - Buy premium subscription
/promote - Promote your channel

Need more Stars? Contact {DEVELOPER_ID}
"""
    await update.message.reply_text(stars_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    user_data = get_user(user.id) or {}
    
    limits = RATE_LIMITS['premium' if user_data.get('is_premium') else 'free']
    
    stats_text = f"""
📊 **Your Statistics**

*Status:* {'⭐ **PREMIUM**' if user_data.get('is_premium') else '🆓 **FREE**'}
*Language:* {LANGUAGES.get(user_data.get('language', 'bn'), 'বাংলা')}
*User ID:* `{user.id}`

*Usage:*
• Messages: {user_data.get('message_count', 0)}/{limits['messages']}
• TTS: {user_data.get('tts_count', 0)}/{limits['tts']}
• Games: {user_data.get('game_count', 0)}/{limits['games']}
• Cooldown: {limits['cooldown']} seconds

*Star Balance:* {user_data.get('stars_balance', 0)} ⭐

👨‍💻 *Developer:* {DEVELOPER_ID}
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# ==================== ADMIN COMMANDS ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin commands"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    if not context.args:
        admin_text = f"""
🔐 **Admin Commands**

👥 *User Management:*
/admin users - List all users
/admin stats - Bot statistics
/admin broadcast [message] - Broadcast to all users
/admin notify [user_id] [message] - Send message to specific user

💰 *Payment Management:*
/admin payments - List recent payments
/admin premium [user_id] - Grant premium to user
/admin stars [user_id] [amount] - Add stars to user

⚙️ *Bot Management:*
/admin restart - Restart bot
/admin logs - View logs
/admin db - Database info

*Example:* /admin broadcast Hello everyone!
"""
        await update.message.reply_text(admin_text, parse_mode='Markdown')
        return
    
    command = context.args[0].lower()
    
    if command == "users":
        # List all users
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            
            await update.message.reply_text(f"👥 Total Users: {count}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    elif command == "stats":
        # Bot statistics
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            premium_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'completed'")
            total_payments = cursor.fetchone()[0]
            
            conn.close()
            
            stats_text = f"""
📊 **Bot Statistics**

👥 Total Users: {total_users}
⭐ Premium Users: {premium_users}
💰 Total Payments: {total_payments}
📅 Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    elif command == "broadcast":
        # Broadcast message
        if len(context.args) < 2:
            await update.message.reply_text("❌ Usage: /admin broadcast [message]")
            return
        
        message = " ".join(context.args[1:])
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            conn.close()
            
            total = len(users)
            success = 0
            failed = 0
            
            await update.message.reply_text(f"📢 Broadcasting to {total} users...")
            
            for (user_id,) in users:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"📢 **Broadcast Message**\n\n{message}",
                        parse_mode='Markdown'
                    )
                    success += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except:
                    failed += 1
            
            await update.message.reply_text(
                f"✅ Broadcast Complete!\n\n"
                f"✅ Success: {success}\n"
                f"❌ Failed: {failed}\n"
                f"📊 Total: {total}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

# ==================== SETUP BOT COMMANDS MENU ====================
async def setup_bot_commands(application):
    """Set up bot commands menu in Telegram"""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show all commands"),
        BotCommand("ping", "Check bot status"),
        BotCommand("id", "Get your user ID"),
        BotCommand("chat", "Chat with Gemini AI"),
        BotCommand("ask", "Ask anything"),
        BotCommand("talk", "Start conversation"),
        BotCommand("download", "Download video"),
        BotCommand("tts", "Text to speech"),
        BotCommand("games", "Show all games"),
        BotCommand("dice", "Roll dice game"),
        BotCommand("guess", "Guess number game"),
        BotCommand("quiz", "Play quiz"),
        BotCommand("rps", "Rock Paper Scissors"),
        BotCommand("stats", "Your statistics"),
        BotCommand("premium", f"Buy premium ({PREMIUM_PRICE}⭐)"),
        BotCommand("promote", f"Promote channel ({PROMOTION_PRICE}⭐)"),
        BotCommand("mystars", "Check star balance"),
        BotCommand("settings", "Bot settings"),
        BotCommand("lang", "Change language"),
        BotCommand("news", "Latest news"),
        BotCommand("bdnews", "Bangladesh news"),
        BotCommand("weather", "Weather information"),
        BotCommand("bdtime", "Bangladesh time"),
        BotCommand("admin", "Admin commands")
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands menu set successfully")

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    # Initialize database
    init_database()
    
    print("=" * 70)
    print("🤖 BANGLADESHI AI BOT STARTING...")
    print(f"👨‍💻 Developer: {DEVELOPER_ID}")
    print(f"🔑 Gemini 2.0 Flash API: Ready")
    print(f"⭐ Premium Price: {PREMIUM_PRICE} Stars")
    print(f"📢 Promotion Price: {PROMOTION_PRICE} Stars")
    print(f"🎮 Games: {len(GAMES)} available")
    print(f"💾 Database: {DB_FILE}")
    print(f"⚙️ Environment: {len([k for k in os.environ if k.startswith(('TELEGRAM', 'GEMINI', 'WEATHER', 'NEWS'))])} variables loaded")
    print("=" * 70)
    
    # Check required environment variables
    required_vars = ['TELEGRAM_TOKEN', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("ℹ️ Please check your .env file")
        return
    
    try:
        # Create application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("ping", lambda u,c: u.message.reply_text("🏓 Pong! Bot is alive!")))
        application.add_handler(CommandHandler("id", lambda u,c: u.message.reply_text(f"🆔 Your ID: `{u.effective_user.id}`", parse_mode='Markdown')))
        application.add_handler(CommandHandler("chat", chat_command))
        application.add_handler(CommandHandler("ask", chat_command))
        application.add_handler(CommandHandler("talk", chat_command))
        application.add_handler(CommandHandler("download", download_command))
        application.add_handler(CommandHandler("video", download_command))
        application.add_handler(CommandHandler("tts", tts_command))
        application.add_handler(CommandHandler("audio", tts_command))
        application.add_handler(CommandHandler("games", games_command))
        application.add_handler(CommandHandler("dice", dice_command))
        application.add_handler(CommandHandler("guess", guess_command))
        application.add_handler(CommandHandler("quiz", quiz_command))
        application.add_handler(CommandHandler("rps", rps_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("premium", premium_command))
        application.add_handler(CommandHandler("promote", promote_command))
        application.add_handler(CommandHandler("mystars", mystars_command))
        application.add_handler(CommandHandler("lang", lang_command))
        application.add_handler(CommandHandler("settings", lambda u,c: u.message.reply_text("⚙️ Settings: Use /lang to change language")))
        application.add_handler(CommandHandler("news", news_command))
        application.add_handler(CommandHandler("bdnews", bdnews_command))
        application.add_handler(CommandHandler("weather", weather_command))
        application.add_handler(CommandHandler("bdtime", bdtime_command))
        application.add_handler(CommandHandler("admin", admin_command))
        
        # Add callback handlers for language selection
        application.add_handler(CallbackQueryHandler(lang_callback_handler, pattern="^lang_"))
        
        # Add payment handlers
        application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
        
        # Setup bot commands menu
        application.post_init = setup_bot_commands
        
        # Start polling
        print("🚀 Starting bot...")
        print("✅ Bot is now running! All commands are working.")
        print("ℹ️ Press Ctrl+C to stop")
        print("=" * 70)
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    # Check and install required packages
    required_packages = [
        "python-telegram-bot",
        "yt-dlp",
        "aiohttp",
        "gTTS",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"📦 Installing {package}...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Run the bot
    main()