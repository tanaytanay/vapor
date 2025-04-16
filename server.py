from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
import json
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client with explicit API key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files under /static path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    return FileResponse("index.html")

# Store hours and product prices
STORE_HOURS = {
    "monday": "9:00 AM - 6:00 PM",
    "tuesday": "9:00 AM - 6:00 PM",
    "wednesday": "9:00 AM - 6:00 PM",
    "thursday": "9:00 AM - 8:00 PM",
    "friday": "9:00 AM - 8:00 PM",
    "saturday": "10:00 AM - 5:00 PM",
    "sunday": "Closed"
}

PRODUCT_PRICES = {
    "vape": 99.99,
    "cartridge": 699.99,
    "flavor": 199.99,
    "hookah": 299.99
}

INVENTORY = {
    "vape": True,
    "cartridge": True,
    "flavor": False,  # Temporarily out of stock
    "hookah": True
}

def get_store_hours(day: str) -> str:
    day = day.lower()
    if day in STORE_HOURS:
        return f"The store hours for {day} are {STORE_HOURS[day]}"
    return f"Sorry, I couldn't find store hours for {day}"

def get_store_hours_multiple(days: list[str]) -> str:
    results = []
    for day in days:
        day = day.lower()
        if day in STORE_HOURS:
            results.append(f"{day.capitalize()}: {STORE_HOURS[day]}")
    if results:
        return "Here are the store hours for the requested days:\n" + "\n".join(results)
    return "Sorry, I couldn't find store hours for any of the specified days"

def get_product_price(product: str) -> str:
    product = product.lower()
    if product in PRODUCT_PRICES:
        return f"The price of {product} is ${PRODUCT_PRICES[product]}"
    return f"Sorry, I couldn't find the price for {product}"

def check_inventory(product: str) -> str:
    product = product.lower()
    if product in INVENTORY:
        if INVENTORY[product]:
            return f"Yes, we do have {product} in stock!"
        else:
            return f"I'm sorry, but we're currently out of stock for {product}. We expect to have more in next week."
    return f"I'm not sure about the availability of {product}. Let me check with our inventory team."

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize conversation history
    conversation_history = [
        {"role": "system", "content": """You are a friendly and helpful store assistant at Vapor. 
        Your responses should be natural, conversational, and engaging. 
        Use a warm and welcoming tone, and maintain context throughout the conversation.
        When answering questions about store hours or prices, be informative but keep it friendly.
        If you're not sure about something, be honest about it.
        Feel free to ask follow-up questions to better understand the customer's needs.
        When asked about product availability, check the inventory status.
        If a product is out of stock, suggest alternatives or let them know when it might be back in stock."""}
    ]
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add user message to conversation history
            conversation_history.append({"role": "user", "content": message["text"]})
            
            # Process the message with OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation_history,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_store_hours_multiple",
                            "description": "Get the store hours for multiple days",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "days": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "description": "List of days of the week"
                                    }
                                },
                                "required": ["days"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "get_product_price",
                            "description": "Get the price of a specific product",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "product": {
                                        "type": "string",
                                        "description": "The name of the product"
                                    }
                                },
                                "required": ["product"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "check_inventory",
                            "description": "Check if a product is in stock",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "product": {
                                        "type": "string",
                                        "description": "The name of the product to check availability for"
                                    }
                                },
                                "required": ["product"]
                            }
                        }
                    }
                ],
                tool_choice="auto"
            )
            
            # Handle function calls
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "get_store_hours_multiple":
                    result = get_store_hours_multiple(function_args["days"])
                elif function_name == "get_product_price":
                    result = get_product_price(function_args["product"])
                elif function_name == "check_inventory":
                    result = check_inventory(function_args["product"])
                
                # Add assistant's response to conversation history
                conversation_history.append({"role": "assistant", "content": result})
                
                # Send the result back to the client
                await websocket.send_text(json.dumps({"text": result}))
            else:
                # Add assistant's response to conversation history
                assistant_response = response.choices[0].message.content
                conversation_history.append({"role": "assistant", "content": assistant_response})
                
                # Send the response back to the client
                await websocket.send_text(json.dumps({"text": assistant_response}))
                
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()