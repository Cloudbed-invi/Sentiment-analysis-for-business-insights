import google.generativeai as genai


# Configure your Google API key
genai.configure(api_key='AIzaSyBi4gFlTpLtTpuYpU5PGqFOEo0iMczrZCk')

def read_feedback_data(file_path):
    """Read the feedback data from a text file."""
    with open(file_path, 'r') as file:
        content = file.read().strip().split("\n")
    positive_elements = content[0].replace("Positive elements: ", "")
    negative_elements = content[1].replace("Negative elements: ", "")
    return positive_elements, negative_elements

def analyze_product_feedback(positive_elements, negative_elements):
    """Analyze product feedback and provide actionable insights."""
    prompt = f"""
    You are a product analyst for leading technology companies like Mac, Asus, Vivo, and Redmi. Based on the following data, provide a comprehensive analysis of how to improve the product and recommend actionable first steps to take for professional sellers.

    Positive elements: {positive_elements}
    Negative elements: {negative_elements}
    There are some elements in both postive and negative, based on count of elements, you can get biased towards one.
    give professional response.
    """


    # Initialize the chat model
    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat(history=[])

    # Send the prompt to the model and get a response
    response = chat.send_message(prompt)
    
    # Convert response to HTML-friendly format

    print(response.text)

    # Convert the prompt from a Markdown-like format to HTML
    
    formatted_response = response.text.replace('\n', '<br>')
    formatted_response = formatted_response.replace('##', '')
    formatted_response = formatted_response.replace('**', '')
    # Handle list items and descriptions
    formatted_response = formatted_response.replace('* ', '<li>')  # Convert list items to <li>

    return f"<div>{formatted_response}</div>"



    

def perform_analysis(file_path):
    # Load feedback data from the text file
    file_path = 'top_keywords.txt'
    positive_elements, negative_elements = read_feedback_data(file_path)

    # Analyze the product feedback
    analysis_result = analyze_product_feedback(positive_elements, negative_elements)

    return analysis_result
    print("Enhanced Analysis and Recommendations:\n", analysis)
