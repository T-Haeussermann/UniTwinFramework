# https://buffml.com/web-based-chatbot-using-flask-api/
# https://github.com/Karan-Malik/Chatbot/tree/master/chatbot_codes
import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import numpy as np
from keras.models import load_model
import json
import random
from llama_cpp import Llama
from llama_cpp.llama_tokenizer import LlamaHFTokenizer

lemmatizer = WordNetLemmatizer()
nltk.download('popular')
model = load_model('model/model.h5')
intents = json.loads(open('data/data.json').read())
words = pickle.load(open('data/texts.pkl','rb'))
classes = pickle.load(open('data/labels.pkl','rb'))

model_llm = Llama.from_pretrained(repo_id="meetkai/functionary-7b-v2.1-GGUF",
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
        if (i['tag'] == tag):
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
            # Combine the remaining words after "parameters" into a single string
            parameters = ' '.join(words[i + 1:])

    if parameters != []:
        # Split the parameters string into a list based on spaces
        parameters = parameters.split()

        # Filter out words that do not contain '='
        parameters = [word for word in parameters if '=' in word]

    # Return the extracted values
    return {"generic_action": {"child": child, "method": method, "parameters": parameters}}

def chatbot_response(msg):
    ints = predict_class(msg, model)
    # Check if there are predicted intents
    if ints:
        if ints[0]["intent"] == "generic_action":
            return extract_values_simple(msg)
        res = getResponse(ints, intents)
        return {"resp": res}
    else:
        # Handle the case when no intent is predicted
        return "no intention found"


def function_calling(prompt, tools, history=None):
    messages = []
    if history is not None:
        messages.append(history)

    message = {"role": "user", "content": prompt}
    messages.append(message)

    response = model_llm.create_chat_completion(messages, tools=tools, tool_choice="auto")

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
