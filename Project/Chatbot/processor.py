import nltk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

import pickle
import numpy as np
import random
import json
import os

from keras.models import load_model
from gtts import gTTS
from pygame import mixer

# Load model and data
model = load_model('Chatbot/chatbot_model.h5')
intents = json.loads(open('Chatbot/intents.json', encoding='utf-8').read())
words = pickle.load(open('Chatbot/words.pkl','rb'))
classes = pickle.load(open('Chatbot/classes.pkl','rb'))

# -------------------------------
# CLEAN INPUT SENTENCE
# -------------------------------
def clean_up_sentence(sentence):
    # tokenize
    sentence_words = nltk.word_tokenize(sentence)
    
    # lemmatize
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    
    return sentence_words


# -------------------------------
# BAG OF WORDS
# -------------------------------
def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentence(sentence)

    bag = [0] * len(words)

    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("found in bag:", w)

    return np.array(bag)


# -------------------------------
# PREDICT INTENT
# -------------------------------
def predict_class(sentence, model):
    p = bow(sentence, words, show_details=False)

    res = model.predict(np.array([p]))[0]

    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    # sort by probability
    results.sort(key=lambda x: x[1], reverse=True)

    return_list = []

    for r in results:
        return_list.append({
            "intent": classes[r[0]],
            "probability": str(r[1])
        })

    return return_list


# -------------------------------
# GET RESPONSE
# -------------------------------
def getResponse(ints, intents_json, save_path="Responses/response.mp3"):

    if len(ints) == 0:
        return "Sorry, I didn't understand that. Please try again."

    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']

    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])

            # 🔊 TEXT TO SPEECH
            try:
                tts = gTTS(text=result, lang='en')
                tts.save(save_path)

                mixer.init()
                sound = mixer.Sound(save_path)
                # sound.play()  # optional
            except:
                print("Audio generation failed")

            return result

    return "Sorry, I didn't understand that."


# -------------------------------
# MAIN CHATBOT FUNCTION
# -------------------------------
def chatbot_response(msg):
    ints = predict_class(msg, model)
    res = getResponse(ints, intents)
    return res