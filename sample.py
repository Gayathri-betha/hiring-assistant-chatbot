import google.generativeai as genai

genai.configure(api_key="AIzaSyB5BDOkcVR90ffMajgpLjZrWOWfWRl9mYE")
models = genai.list_models()
for model in models:
    print(model.name)
