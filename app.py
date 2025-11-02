import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
def configure_gemini():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    
    # Check available models
    available_models = []
    for model in genai.list_models():
        available_models.append(model.name)
        print(f"Available: {model.name}")
    
    return available_models

# Initialize and test the model
def initialize_model():
    try:
        available_models = configure_gemini()
        
        # Try different model names
        model_options = [
            'models/gemini-1.5-pro',
            'models/gemini-1.0-pro', 
            'models/gemini-pro'
        ]
        
        selected_model = None
        for model_name in model_options:
            if any(model_name in avail for avail in available_models):
                selected_model = model_name
                break
        
        if not selected_model:
            # Use the first available model that supports generateContent
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    selected_model = model.name
                    break
        
        if not selected_model:
            raise Exception("No suitable model found for generateContent")
            
        print(f"Using model: {selected_model}")
        return genai.GenerativeModel(selected_model.replace('models/', ''))
        
    except Exception as e:
        print(f"Error initializing model: {e}")
        return None

# Generate content function
def generate_content(prompt):
    try:
        model = initialize_model()
        if not model:
            return "Error: Model not available"
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error generating content: {str(e)}"

# Test the connection
if __name__ == "__main__":
    test_response = generate_content("Hello, are you working?")
    print("Test response:", test_response)
