# https://buffml.com/web-based-chatbot-using-flask-api/
# https://github.com/Karan-Malik/Chatbot/tree/master/chatbot_codes
from fastapi import FastAPI
import uvicorn
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import numpy as np
from keras.models import load_model
import json
import random
from llama_cpp import Llama
from llama_cpp.llama_tokenizer import LlamaHFTokenizer


nltk.download('popular')
lemmatizer = WordNetLemmatizer()
model = load_model('model/model.h5')
intents = json.loads(open('data/data.json').read())
words = pickle.load(open('data/texts.pkl', 'rb'))
classes = pickle.load(open('data/labels.pkl', 'rb'))

# llm model
llm_model = Llama.from_pretrained(repo_id="meetkai/functionary-7b-v2.1-GGUF",
                              filename="functionary-7b-v2.1.f16.gguf",
                              local_dir="models", cache_dir="models/cache",
                              chat_format="functionary-v2",
                              tokenizer=LlamaHFTokenizer.from_pretrained("meetkai/functionary-7b-v2.1-GGUF"),
                              n_gpu_layers=-1,
                              n_ctx=2048)

def clean_up_sentence(sentence):
    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result


def extract_values_simple(input_string):
    # Split the input string into words
    words = input_string.split()

    # Initialize variables to store extracted values
    child = None
    method = None
    parameters = []

    # Iterate through the words to find the relevant information
    for i, word in enumerate(words):
        if word.lower() == "child" and i < len(words) - 1:
            child = words[i + 1]
        elif word.lower() == "method" and i < len(words) - 1:
            method = words[i + 1]
        elif word.lower() == "parameters" and i < len(words) - 1:
            print(words[i + 1:])
            parameters = words[i + 1:]

    # remove wrong words from parameters
    parameters_exchange = []
    for word in parameters:
        if "=" in word:
            parameters_exchange.append(word)

    parameters = parameters_exchange

    # Return the extracted values
    return {"generic_action": {"child": child, "method": method, "parameters": parameters}}

def chatbot_response(msg):
    ints = predict_class(msg, model)
    # Check if there are predicted intents
    if ints:
        if ints[0]["intent"] == "generic_action":
            return extract_values_simple(msg)
        res = getResponse(ints, intents)
        return res
    else:
        # Handle the case when no intent is predicted
        return extract_values_simple(msg)

def function_calling(prompt, tools, history=None):
    messages = []
    if history is not None:
        messages.append(history)

    message = {"role": "user", "content": prompt}
    messages.append(message)

    response = llm_model.create_chat_completion(messages, tools=tools, tool_choice="auto")

    if response["choices"][0]["message"]["tool_calls"] is not None:
        # Filter out items with empty arguments
        filtered_choices = []
        for item in response["choices"][0]["message"]["tool_calls"]:
            if item["function"]["arguments"] == "{":
                print("found")
            else:
                print("not")
                filtered_choices.append(item)

        # Update the 'choices' in the response
        response['choices'][0]["message"]["tool_calls"] = filtered_choices

        # call function
        tool_call = response["choices"][0]["message"]["tool_calls"][0]

        function_name = tool_call["function"]["name"].strip()
        function_params = tool_call["function"]["arguments"]
        function_params = json.loads(function_params)
        call = {"call": {"function_name": function_name, "function_params": function_params}}
        return call

    else:
        llm_message = response["choices"][0]["message"]["content"]
        message = {"message": llm_message}
        return message

App = FastAPI()
App.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@App.get("/chat", response_class=HTMLResponse)
# def mainpage(request: Request):
#     return templates.TemplateResponse("index-working.html", {"request": request})
async def read_item(request: Request):
    return templates.TemplateResponse("index-working.html", {"request": request})

@App.get("/chat/get")
def get_bot_response(msg: str):
    print(msg)
    return chatbot_response(msg)

@App.get("/fctcalling/")
def fctcalling(msg, tools):
    print(msg)
    tools = json.loads(tools)
    output = function_calling(msg, tools)
    return output


"""rund API server. swagger ui on http://127.0.0.1:7000/docs#/"""
uvicorn.run(App, host="0.0.0.0", port=7000, log_level="info")