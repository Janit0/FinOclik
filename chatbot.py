from flask import Flask, render_template, request
import openai

#Applying API key from OpenAI to integarte it with our Chat Bot
openai.api_key = "your own key"

#################Creation of app Folder to store our data#########################
app = Flask(__name__, static_folder='C:/Users/Janit/.spyder-py3/AIP/static')

# File to store conversation history
conversation_file = r'C:/Users/Janit/.spyder-py3/AIP/conversation_history.txt'

def load_conversation_history():
    try:
        with open(conversation_file, 'r') as file:
            return eval(file.read())
    except (IOError, SyntaxError):  # Handle file not found or invalid content
        return []

def save_conversation_history():
    with open(conversation_file, 'w') as file:
        file.write(repr(conversation_history))

# Initialize conversation history
conversation_history = load_conversation_history()

def reset_conversation_history():
    global conversation_history
    conversation_history = []
    save_conversation_history()

# Reset conversation history when the Flask application starts
reset_conversation_history()

#Creating the default message 
if not conversation_history:
    conversation_history.append({"chatbot_response": "Hi, How can I assist you?"})
    save_conversation_history()

def get_chatbot_response(user_input):
    # Simple chatbot logic
    #Creating Query Text to give limited words answer
    QueryAsked = user_input.lower() + "  in less than 10 words in each number point restrict to 3 points "
    if user_input.lower() == "hi":
        response = "Hi there! How can I help you?"
    elif "how are you" in user_input.lower():
        response = "I'm good, thank you! How about you?"
    else :
        
        #Calling the 3.5GPT Turbo
        CommonListofWords = ["crytocurrency","crypto","","invest","investment strategies","investment options","investment","bonds","portfolio","real estate","risk","diversification","diversify","retirement","retire","stocks","stock"]
        UserInputText = user_input.lower()
        UserInputText = UserInputText.split()
        
        #Creation of list comprehension
        DataListForCheckof_FinancialTerm = [item for item in UserInputText if item in CommonListofWords]
        
        if len(DataListForCheckof_FinancialTerm) > 0:
            completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": QueryAsked}])
            
            #Message Extracted From Chat GPT
            Message_ExtractedData = completion.choices[0].message.content
            
            response =  Message_ExtractedData
        
        else:
            response = "Sorry we only deal with financial queries. Please do try again."
    # Add the user input and chatbot response to the conversation history
    conversation_history.append({"user_input": user_input, "chatbot_response": response})
    
    # Save the updated conversation history
    save_conversation_history()
 
    return response

@app.route('/', methods=['GET', 'POST'])
def chat():
    chatbot_response = None

    if request.method == 'POST':
        user_input = request.form['user_input']
        chatbot_response = get_chatbot_response(user_input)

    return render_template('chatbot.html', chatbot_response=chatbot_response, conversation_history=conversation_history)

if __name__ == '__main__':
    app.run(debug=True)
