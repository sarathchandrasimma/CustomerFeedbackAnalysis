# Customer Feedback Analysis

This project provides a tool to analyze customer feedback from CSV files. It performs sentiment analysis and generates various visualizations, including histograms, pie charts, and word clouds. Additionally, it integrates a chatbot or AI to generate suggestions and insights based on the feedback.

## Features

- Upload CSV files containing customer feedback.
- Analyze feedback using sentiment analysis.
- Generate visualizations including:
  - Sentiment histogram
  - Sentiment pie chart
  - Word clouds
  - Seaborn bar and pie charts
- Generate AI-driven suggestions and insights for each feedback entry.

## Technologies Used

- Django
- Pandas
- Plotly
- Seaborn
- WordCloud
- SpaCy
- TextBlob
- Tweepy
- Transformers

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/customer-feedback-analysis.git
    cd customer-feedback-analysis
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Apply migrations and start the Django server:

    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

5. Open your browser and navigate to `http://127.0.0.1:8000`.

## Usage

1. Upload a CSV file containing customer feedback. Ensure the CSV file has a column named `feedback`.
2. Click on "Analyze Feedback" to process the file.
3. View the data summary, sentiment analysis, and generated visualizations.
4. See AI-driven suggestions and insights for each feedback entry.

## Project Structure

- `customer_feedback_analysis/`
  - `templates/`
    - `index.html` - Main template file.
  - `static/` - Static files for CSS, JS, etc.
  - `forms.py` - Form handling file.
  - `views.py` - Main view file containing logic for processing feedback and generating visualizations.

## Sample `views.py`

```python
# Import necessary libraries
from django.shortcuts import render
import pandas as pd
from .forms import FeedbackForm
from .analysis import analyze_feedback, generate_plotly_chart, generate_seaborn_chart, generate_wordcloud, wordcloud_to_base64, generate_suggestions

# Django view
def index(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES.get('file')
            
            if file:
                try:
                    # Read CSV file into DataFrame with error handling for encoding issues
                    try:
                        df = pd.read_csv(file)
                    except UnicodeDecodeError:
                        df = pd.read_csv(file, encoding='ISO-8859-1')
                    
                    # Ensure the 'feedback' column exists
                    if 'feedback' not in df.columns:
                        return render(request, 'index.html', {'form': form, 'error': 'CSV file must contain a "feedback" column.'})
                    
                    # Drop missing values in the 'feedback' column
                    df.dropna(subset=['feedback'], inplace=True)
                    
                    # Get the feedback list
                    feedback_list = df['feedback'].tolist()
                    
                    # Analyze feedback
                    sentiments, sentiment_counts, sentiment_percentages = analyze_feedback(feedback_list)
                    
                    # Generate suggestions
                    suggestions = generate_suggestions(feedback_list)
                    
                    # Convert sentiment_counts to list of dicts for chart generation
                    sentiment_data = [{'sentiment': s, 'count': count} for s, count in sentiment_counts.items()]
                    
                    # Generate charts
                    chart_html_histogram = generate_plotly_chart(sentiment_data, 'histogram')
                    chart_html_pie = generate_plotly_chart(sentiment_data, 'pie')
                    seaborn_chart_bar = generate_seaborn_chart(sentiment_data, 'bar')
                    seaborn_chart_pie = generate_seaborn_chart(sentiment_data, 'pie')
                    
                    # Generate word cloud for entire feedback
                    feedback_text = ' '.join(feedback_list)
                    wordcloud = generate_wordcloud(feedback_text)
                    wordcloud_base64 = wordcloud_to_base64(wordcloud)
                    
                    # Get data summary
                    data_summary = {
                        'num_rows': df.shape[0],
                        'num_columns': df.shape[1],
                        'columns': df.columns.tolist()
                    }
                    
                    context = {
                        'form': form,
                        'data_summary': data_summary,
                        'sentiment_percentages': sentiment_percentages,
                        'chart_html_histogram': chart_html_histogram,
                        'chart_html_pie': chart_html_pie,
                        'seaborn_chart_bar': seaborn_chart_bar,
                        'seaborn_chart_pie': seaborn_chart_pie,
                        'wordcloud': wordcloud_base64,
                        'suggestions': suggestions,  # Pass suggestions to the template
                    }
                    return render(request, 'index.html', context)

                except Exception as e:
                    return render(request, 'index.html', {'form': form, 'error': str(e)})
    
    else:
        form = FeedbackForm()

    return render(request, 'index.html', {'form': form})
