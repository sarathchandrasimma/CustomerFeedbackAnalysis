from django.shortcuts import render
from .forms import FeedbackForm
import pandas as pd
import spacy
from wordcloud import WordCloud
import plotly.express as px
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from textblob import TextBlob
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

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

# Generate Plotly 3D pie chart
def generate_plotly_pie_chart(data):
    df = pd.DataFrame(data)
    fig = px.pie(df, names='sentiment', values='count', title='Sentiment Distribution', hole=0.3)
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    return fig.to_html(full_html=False)

# Generate Plotly bar chart
def generate_plotly_bar_chart(data):
    df = pd.DataFrame(data)
    fig = px.bar(df, x='sentiment', y='count', color='sentiment', title='Sentiment Bar Chart', text='count')
    fig.update_layout(xaxis_title='Sentiment', yaxis_title='Count', xaxis=dict(tickangle=-45))
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    return fig.to_html(full_html=False)

# Clean and preprocess feedback data
def clean_feedback(feedback_list):
    cleaned_feedback = []
    for feedback in feedback_list:
        if pd.notnull(feedback):
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

# Identify common issues and areas for improvement
def identify_common_issues(feedback_list):
    # Vectorize feedback and apply LDA
    vectorizer = CountVectorizer(stop_words='english')
    X = vectorizer.fit_transform(feedback_list)
    lda = LatentDirichletAllocation(n_components=5, random_state=0)
    lda.fit(X)

    # Get top words for each topic
    feature_names = vectorizer.get_feature_names_out()
    topics = []
    for topic_idx, topic in enumerate(lda.components_):
        top_words = [feature_names[i] for i in topic.argsort()[-10:]]
        topics.append({'topic': f'Topic {topic_idx + 1}', 'words': ', '.join(top_words)})

    return topics

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
                    
                    # Identify common issues
                    topics = identify_common_issues(feedback_list)
                    
                    # Convert sentiment_counts to list of dicts for chart generation
                    sentiment_data = [{'sentiment': s, 'count': count} for s, count in sentiment_counts.items()]
                    
                    # Generate charts
                    chart_html_pie = generate_plotly_pie_chart(sentiment_data)
                    chart_html_bar = generate_plotly_bar_chart(sentiment_data)
                    
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
                        'chart_html_pie': chart_html_pie,
                        'chart_html_bar': chart_html_bar,
                        'wordcloud': wordcloud_base64,
                        'topics': topics,
                    }
                    return render(request, 'index.html', context)

                except Exception as e:
                    return render(request, 'index.html', {'form': form, 'error': str(e)})
    
    else:
        form = FeedbackForm()

    return render(request, 'index.html', {'form': form})
