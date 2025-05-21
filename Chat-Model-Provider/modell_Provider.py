import uvicorn
from fastapi import FastAPI
from method_chat import chatbot_response, function_calling
import json



"""create API"""
app = FastAPI()

"""define API Methods"""
"""add all routers defined in children to UniTwinGenerator app"""

@app.get("/chat/get")
def get_bot_response(msg: str):
    resp = chatbot_response(msg)
    return resp

@app.get("/fctcalling/")
def fctcalling(prompt, tools):
    tools = json.loads(tools)
    output = function_calling(prompt, tools)
    return output


"""rund API server. swagger ui on http://127.0.0.1:5000/docs#/"""
uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")


