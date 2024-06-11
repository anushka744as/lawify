from flask import Flask, render_template, request, jsonify
import openai
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
DetectorFactory.seed = 0

def detect_language(text):
    try:
        language = detect(text)
        return language
    except LangDetectException:
        return 'en'

def classify_query(user_input):
    prompt = f"""
    Determine if the following query is related to legal matters. Respond with "Legal" or "Not Legal".
    Query: {user_input}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional classifier."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=5,
        n=1,
        stop=None,
        temperature=0
    )
    classification = response.choices[0].message['content'].strip()
    return classification

def get_legal_advice(conversation_history):
    prompt = conversation_history + """
    Give a detailed response regarding the query - make it very specific and explicate with at least 500 words. Use solely reputed and official documents for accessing the law. Ensure that your response is very specific to the scenario entered, DON'T MENTION 'CONSULT A LAWYER" in any manner. Rather answer the question in most elaborate manner covering every aspect of it. Also for each relevant piece of information you may cite which reputed/official document it is from. Once again, ensure that all of my relevant rights and applicable laws are mentioned and in many manner do not mention “CONSULT A LAWYER.” ALSO INCLUDE RELEVANT PRECEDENTS.

    Ensure all of these elements, along with specificity and relevant precedents are included, along with mentioned sections from official and reputed legal documents.
    MUST INCLUDE PRECEDENTS.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional Indian lawyer who is extremely well-versed with Indian Constitution, Indian laws, Indian cases in all types of cases, Indian Penal Code, and all the other official legal documents and is supposed to explicate and provide solution in detail."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.7
    )
    return response.choices[0].message['content']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_advice', methods=['POST'])
def get_advice():
    user_input = request.form['query']
    conversation_history = request.form['conversation_history']
    
    classification = classify_query(user_input)
    
    if "Not Legal" in classification:
        legal_advice = "Not a legal query."
        conversation_history += f"\nUser: {user_input}\nLawify: {legal_advice}\n"
        
    else:
        conversation_history += f"\nUser: {user_input}\n"
        legal_advice = get_legal_advice(conversation_history)
        conversation_history += f"Lawify: {legal_advice}\n"

    return jsonify({'response': legal_advice, 'conversation_history': conversation_history})

if __name__ == "__main__":
    app.run(debug=True)


