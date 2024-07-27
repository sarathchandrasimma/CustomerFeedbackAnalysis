from django.shortcuts import render
from django.views.decorators.cache import cache_page
from .forms import FeedbackForm
import pandas as pd
import base64
import spacy
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from io import BytesIO

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    buffer = BytesIO()
    wordcloud.to_image().save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
    return sentiment, polarity, subjectivity

def generate_plotly_pie_chart(data):
    df = pd.DataFrame(data)
    fig = go.Figure(go.Pie(labels=df['sentiment'], values=df['count'], hole=.3))
    fig.update_layout(title_text='Sentiment Distribution', annotations=[dict(text='Sentiment', x=0.5, y=0.5, font_size=20, showarrow=False)])
    return fig.to_html(full_html=False)

def generate_plotly_bar_chart(data):
    df = pd.DataFrame(data)
    fig = px.bar(df, x='sentiment', y='count', color='sentiment', title='Sentiment Bar Chart', text='count')
    fig.update_layout(xaxis_title='Sentiment', yaxis_title='Count', xaxis=dict(tickangle=-45))
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    return fig.to_html(full_html=False)

def clean_feedback(feedback_list):
    return [' '.join(word.lower() for word in feedback.split() if word.isalnum() or word.isspace()) for feedback in feedback_list if pd.notnull(feedback)]

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

def identify_common_issues(feedback_list):
    vectorizer = CountVectorizer(stop_words='english', max_features=10000)
    X = vectorizer.fit_transform(feedback_list)
    lda = LatentDirichletAllocation(n_components=5, random_state=0)
    lda.fit(X)
    feature_names = vectorizer.get_feature_names_out()
    topics = [{'topic': f'Topic {idx + 1}', 'words': ', '.join([feature_names[i] for i in topic.argsort()[-10:]])} for idx, topic in enumerate(lda.components_)]
    return topics

def generate_recommendations(topics):
    recommendations = []
    for topic in topics:
        if "delivery" in topic['words']:
            recommendations.append("Improve delivery speed and reliability.")
        if "price" in topic['words']:
            recommendations.append("Review pricing strategy for better competitiveness.")
        if "quality" in topic['words']:
            recommendations.append("Ensure product quality and consistency.")
        if "service" in topic['words']:
            recommendations.append("Enhance customer service responsiveness.")
        if "return" in topic['words']:
            recommendations.append("Simplify the return and refund process.")
    return recommendations

def clean_and_preprocess_feedback(df):
    possible_columns = ['feedback', 'review', 'text']
    column_name = next((col for col in possible_columns if col.lower() in [c.lower() for c in df.columns]), None)
    if not column_name:
        return None, None
    df.dropna(subset=[column_name], inplace=True)
    df['cleaned_feedback'] = df[column_name].apply(lambda x: ' '.join(word.lower() for word in str(x).split() if word.isalnum() or word.isspace()))
    return df, column_name

@cache_page(60 * 15)  # Cache page for 15 minutes
def index(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES.get('file')
            if file:
                try:
                    try:
                        df = pd.read_csv(file)
                    except UnicodeDecodeError:
                        df = pd.read_csv(file, encoding='ISO-8859-1')
                    
                    df, column_name = clean_and_preprocess_feedback(df)
                    if not column_name:
                        return render(request, 'index.html', {'form': form, 'error': 'CSV file must contain one of the columns: "feedback", "review", "text".'})
                    
                    feedback_list = df['cleaned_feedback'].tolist()
                    sentiments, sentiment_counts, sentiment_percentages = analyze_feedback(feedback_list)
                    topics = identify_common_issues(feedback_list)
                    recommendations = generate_recommendations(topics)
                    sentiment_data = [{'sentiment': s, 'count': count} for s, count in sentiment_counts.items()]
                    chart_html_pie = generate_plotly_pie_chart(sentiment_data)
                    chart_html_bar = generate_plotly_bar_chart(sentiment_data)
                    feedback_text = ' '.join(feedback_list)
                    wordcloud_base64 = generate_wordcloud(feedback_text)
                    data_summary = {'num_rows': df.shape[0], 'num_columns': df.shape[1], 'columns': df.columns.tolist()}
                    context = {
                        'form': form,
                        'data_summary': data_summary,
                        'sentiment_percentages': sentiment_percentages,
                        'chart_html_pie': chart_html_pie,
                        'chart_html_bar': chart_html_bar,
                        'wordcloud': wordcloud_base64,
                        'topics': topics,
                        'recommendations': recommendations,
                    }
                    return render(request, 'index.html', context)
                except Exception as e:
                    return render(request, 'index.html', {'form': form, 'error': str(e)})
    else:
        form = FeedbackForm()
    return render(request, 'index.html', {'form': form})

# def home(request):
#     return render(request, 'home.html')

# def about(request):
#     return render(request, 'about.html')

# def contact(request):
#     return render(request, 'contact.html')
