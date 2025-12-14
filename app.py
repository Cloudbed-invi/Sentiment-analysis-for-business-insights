from flask import Flask, render_template, request, jsonify, url_for, send_from_directory, redirect
from dotenv import load_dotenv
load_dotenv()
import threading
import uuid
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import google.generativeai as genai
from scraper import scrape_reviews

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure Gemini AI
GENAI_KEY = os.getenv("GEMINI_API_KEY")  # Load from env
if not GENAI_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")
try:
    genai.configure(api_key=GENAI_KEY)
except Exception as e:
    print(f"Failed to configure GenAI: {e}")

TASKS = {}
RESULTS_DIR = '.'
STATIC_PLOT_DIR = os.path.join('static', 'plots')
if not os.path.exists(STATIC_PLOT_DIR):
    os.makedirs(STATIC_PLOT_DIR)

@app.route('/')
def index():
    return render_template('index.html')

def background_scrape_task(task_id, url, page_count=1):
    def progress_callback(msg, percent):
        if task_id in TASKS:
            TASKS[task_id]['message'] = msg
            TASKS[task_id]['progress'] = percent
    
    try:
        if task_id in TASKS:
            TASKS[task_id]['status'] = 'running'
            TASKS[task_id]['message'] = f'Starting scraper ({page_count} pages)...'
        
        result = scrape_reviews(url, max_pages=page_count, progress_callback=progress_callback)
        
        if result is None or result[0] is None:
            if task_id in TASKS:
                TASKS[task_id]['status'] = 'error'
                TASKS[task_id]['message'] = 'No reviews found or invalid URL.'
        else:
            csv_filename, review_count = result
            if task_id in TASKS:
                TASKS[task_id]['status'] = 'complete'
                TASKS[task_id]['message'] = f'Completed! Scraped {review_count} reviews.'
                TASKS[task_id]['result_url'] = f'/results/{csv_filename}'
            
    except Exception as e:
        if task_id in TASKS:
            TASKS[task_id]['status'] = 'error'
            TASKS[task_id]['message'] = f'Error: {str(e)}'

@app.route('/scrape', methods=['POST'])
def scrape():
    if request.is_json:
        data = request.get_json()
        url = data.get('url')
        page_count = int(data.get('page_count', 1))
    else:
        url = request.form.get('url')
        page_count = int(request.form.get('page_count', 1))
    
    if not url:
        return jsonify({'error': 'Please provide a valid URL'}), 400

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        'status': 'queued',
        'progress': 0,
        'message': 'Queued...'
    }
    
    thread = threading.Thread(target=background_scrape_task, args=(task_id, url, page_count))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/progress/<task_id>')
def content_progress(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/results/<filename>')
def results(filename):
    if not os.path.exists(filename): return "File not found", 404
    
    try:
        df = pd.read_csv(filename)
        positive = df[df['Rating'] >= 4].to_dict('records')
        negative = df[df['Rating'] <= 3].to_dict('records')
        
        return render_template('results.html', 
                               reviews={'positive': positive, 'negative': negative}, 
                               filename=filename)
    except Exception as e:
        return f"Error reading results: {e}", 500

@app.route('/plot/<filename>')
def plot_results(filename):
    if not os.path.exists(filename): return "File not found", 404
    
    try:
        df = pd.read_csv(filename)
        
        # 1. Rating Counts (1-5)
        # We ensure all indices 1-5 exist even if count is 0
        counts = df['Rating'].value_counts().sort_index()
        rating_counts = [int(counts.get(i, 0)) for i in range(1, 6)]
        
        # 2. Sentiment Counts
        pos = len(df[df['Rating'] >= 4])
        neu = len(df[df['Rating'] == 3]) # Should be rare given scraper ignores 3? No, scraper gets all.
        neg = len(df[df['Rating'] <= 2])
        # Note: If ratings are floats like 4.5, this logic holds (>=4).
        
        plot_data = {
            'ratings': rating_counts,
            'sentiment': [pos, neu, neg]
        }
        
        return render_template('plot_results.html', plot_data=plot_data, filename=filename)

    except Exception as e:
        return f"Error processing data: {e}", 500

@app.route('/analysis/<filename>')
def analysis(filename):
    if not os.path.exists(filename): return "File not found", 404
    
    try:
        df = pd.read_csv(filename)
        
        avg_rating = df['Rating'].mean()
        total_reviews = len(df)
        
        positive_sample = df[df['Rating'] >= 4]['Content'].dropna().head(10).tolist()
        negative_sample = df[df['Rating'] <= 3]['Content'].dropna().head(10).tolist()
        
        prompt = f"""
        You are a senior product analyst for Flipkart/Amazon sellers. Analyze the customer reviews below.
        
        **Stats:**
        - Total: {total_reviews}
        - Avg Rating: {avg_rating:.1f}/5
        
        **Positive Feedback Samples:**
        {chr(10).join(['- ' + str(r) for r in positive_sample])}
        
        **Negative Feedback Samples:**
        {chr(10).join(['- ' + str(r) for r in negative_sample])}
        
        **Analysis Required (HTML Format <div>...</div>):**
        1. **Executive Summary**: 2 sentences on overall sentiment.
        2. **Key Strengths**: Bullet points of what customers love.
        3. **Critical Issues**: Bullet points of main complaints.
        4. **Action Plan**: 3 specific steps to improve the product/listing.
        
        Output valid HTML. Use <h3>, <ul>, <li>, <strong>. No markdown backticks.
        """

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            analysis_result = response.text
            analysis_result = analysis_result.replace('```html', '').replace('```', '')
            
        except Exception as ai_e:
            analysis_result = f"<div class='error'><strong>AI Analysis Failed:</strong> {str(ai_e)}</div>"

        return render_template('analysis.html', 
                               analysis_result=analysis_result, 
                               filename=filename)
        
    except Exception as e:
        return f"Error analyzing: {e}", 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('.', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
