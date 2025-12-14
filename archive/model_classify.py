import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load the dataset
df = pd.read_csv('reviews.csv')  # Change the file name as needed

# Specify the path to your model
model_path = 'C:\\Users\\Cloudbed\\Desktop\\Harsha\\Projects\\NLP\\project_code\\project_code\\custom_roberta_model'

# Load your tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Example function to preprocess text
def preprocess_text(text):
    # Ensure input is a string, if not, convert to string
    if not isinstance(text, str):
        text = str(text)
    # Tokenize and return input_ids and attention_mask
    return tokenizer.encode_plus(
        text,
        truncation=True,
        padding='max_length',
        max_length=512,
        return_tensors='pt',
        return_attention_mask=True  # Return attention mask
    )

# Apply preprocessing to the Content column
preprocessed = df['Content'].apply(preprocess_text)

# Extract input_ids and attention_mask from the preprocessed results
input_ids = torch.cat([item['input_ids'] for item in preprocessed]).squeeze(1)  # Shape: (N, 512)
attention_masks = torch.cat([item['attention_mask'] for item in preprocessed]).squeeze(1)  # Shape: (N, 512)

# Load your sentiment analysis model
model = AutoModelForSequenceClassification.from_pretrained(model_path)

def classify_sentiment(input_ids, attention_masks):
    # Initialize a list to store predictions
    predictions = []
    # Move model and tensors to GPU if available
    model.eval()  # Set the model to evaluation mode
    with torch.no_grad():
        # Forward pass with input_ids and attention_masks
        outputs = model(input_ids, attention_mask=attention_masks)
        predictions = torch.argmax(outputs.logits, dim=1).tolist()  # Convert predictions to a list
    return predictions

# Apply sentiment classification
df['predictions'] = classify_sentiment(input_ids, attention_masks)

# Map numerical predictions to sentiment labels
sentiment_mapping = {0: 'Negative', 1: 'Positive'}
df['sentiment'] = df['predictions'].map(sentiment_mapping)

# Display the results
print(df[['Name', 'Title', 'Rating', 'Content', 'sentiment']])

# Save results to a new CSV file
df.to_csv('classified_sentiments.csv', index=False)
