from django.shortcuts import render
from .forms import FeedbackForm
import pandas as pd
import spacy
from wordcloud import WordCloud
import plotly.express as px
import seaborn as sns
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from textblob import TextBlob
from collections import Counter

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

# Analyze sentiment using TextBlob and return detailed analysis
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_polarity = blob.sentiment.polarity
    sentiment_subjectivity = blob.sentiment.subjectivity
    
    if sentiment_polarity > 0:
        sentiment = "Positive"
    elif sentiment_polarity < 0:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return sentiment, sentiment_polarity, sentiment_subjectivity

# Generate word cloud
def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    return wordcloud

# Convert word cloud to base64 string
def wordcloud_to_base64(wordcloud):
    buffer = BytesIO()
    wordcloud.to_image().save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str

# Generate Plotly chart
def generate_plotly_chart(data, chart_type='histogram'):
    df = pd.DataFrame(data, columns=['sentiment', 'count'])
    
    if chart_type == 'histogram':
        fig = px.histogram(df, x='sentiment', title='Sentiment Histogram')
    elif chart_type == 'pie':
        fig = px.pie(df, names='sentiment', values='count', title='Sentiment Distribution')
    
    return fig.to_html(full_html=False)

# Generate Seaborn chart
def generate_seaborn_chart(data, chart_type='bar'):
    df = pd.DataFrame(data)
    
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'bar':
        sns.barplot(x='sentiment', y='count', data=df, palette='viridis')
        plt.title('Sentiment Count')
        plt.xlabel('Sentiment')
        plt.ylabel('Count')
    elif chart_type == 'pie':
        df.set_index('sentiment', inplace=True)
        df['count'].plot(kind='pie', autopct='%1.1f%%', figsize=(8, 8), colors=sns.color_palette('viridis', n_colors=len(df)))
        plt.title('Sentiment Distribution')
    
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str

# Clean and preprocess feedback data
def clean_feedback(feedback_list):
    cleaned_feedback = []
    for feedback in feedback_list:
        if pd.notnull(feedback):
            # Remove non-alphanumeric characters, except for spaces
            cleaned_feedback.append(' '.join(word for word in feedback.split() if word.isalnum() or word.isspace()))
    return cleaned_feedback

# Analyze sentiment for a list of texts and return statistics
def analyze_feedback(feedback_list):
    cleaned_feedback = clean_feedback(feedback_list)
    sentiments = []
    sentiment_counts = Counter()

    for feedback in cleaned_feedback:
        sentiment, polarity, subjectivity = analyze_sentiment(feedback)
        sentiments.append({'feedback': feedback, 'sentiment': sentiment, 'polarity': polarity, 'subjectivity': subjectivity})
        sentiment_counts[sentiment] += 1

    sentiment_total = sum(sentiment_counts.values())
    sentiment_percentages = {sentiment: (count / sentiment_total) * 100 for sentiment, count in sentiment_counts.items()}

    return sentiments, sentiment_counts, sentiment_percentages

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
                    }
                    return render(request, 'index.html', context)

                except Exception as e:
                    return render(request, 'index.html', {'form': form, 'error': str(e)})
    
    else:
        form = FeedbackForm()

    return render(request, 'index.html', {'form': form})
