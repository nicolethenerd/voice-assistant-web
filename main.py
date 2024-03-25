from flask import Flask, request, jsonify
import os
# from dotenv import load_dotenv
from openai import OpenAI
from shoprite import shoprite_tools, call_shoprite_function_by_name
import json

app = Flask(__name__)

# load_dotenv()

# openai_api_key=os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key="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")
model = "gpt-3.5-turbo"

prompt: str = '''
You are a voice activated digital assistant for ordering groceries from ShopRite.
If there is ambiguity about which item a user wants, ask clarifying questions.
Do not ask follow up questions after calling a function.

After adding an item, if the user clarifies and says they meant a different item, remove the original item and add the new one.

The abbreviation 'oz' should be replaced with 'ounces'.
'''

def complete_message(message):
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": message}]

    response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=shoprite_tools,
            # tool_choice=tool_choice,
        )
    response_message = response.choices[0].message
    messages.append(response_message)

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            # Which function call was invoked
            function_name = tool_call.function.name

            # Extracting the arguments
            function_args = json.loads(tool_call.function.arguments)

            function_response = call_shoprite_function_by_name(function_name, function_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response
                }
            )
        response_after_calls = client.chat.completions.create(
            model=model,
            messages=messages
        )
        print(response_after_calls)
        messages.append(response_after_calls.choices[0].message)
        response_message = response_after_calls.choices[0].message

    return response_message

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data['message']
    response_message = complete_message(user_message)
    return response_message.content

if __name__ == '__main__':
    app.run(debug=True)