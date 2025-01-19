import requests
import os
from dotenv import load_dotenv
import time
from pytrends.request import TrendReq
import spacy
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import google.generativeai as genai
from typing import List, Dict
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
from db import db_manager
import logging
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load spaCy's small English model
nlp = spacy.load('en_core_web_sm')

# Initialize Google Trends API
pytrends = TrendReq(hl='en-US', tz=360)

# Function to extract keywords from business owner input
def extract_keywords(text):
    doc = nlp(text)
    # Filter out duplicates and limit to most relevant keywords
    keywords = list(set([token.text.lower() for token in doc 
                        if token.pos_ in ['NOUN', 'PROPN'] 
                        and not token.is_stop]))[:5]
    return keywords

# Function to search DuckDuckGo and gather competitor data
def search_duckduckgo(query):
    api_key = os.getenv("duck-duck-go")  # Load your API key from the environment
    url = "https://serpapi.com/search"
    
    params = {
        'api_key': api_key,
        'engine': 'duckduckgo',
        'q': query,
        'num': 30  # Request more results to ensure we get at least 20
    }
    
    try:
        print(f"Searching for: {query}")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Extract organic results
            for result in data.get('organic_results', []):
                summary = result.get('snippet', '')
                if result.get('description'):
                    summary += ' ' + result.get('description', '')
                
                results.append({
                    'title': result.get('title', ''),
                    'snippet': summary,
                    'link': result.get('link', ''),
                    'displayed_link': result.get('displayed_link', ''),
                    'date': result.get('date', '')
                })
                
                if len(results) >= 25:
                    break
            
            print(f"Found {len(results)} results")
            return results
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Error message: {response.text[:200]}")
            return []
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

# Function to get Google Trends data for extracted keywords
def get_google_trends_data(keywords):
    # Limit to 5 keywords maximum
    keywords = keywords[:5]
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe='today 12-m', geo='', gprop='')
        trends_data = pytrends.interest_over_time()
        
        # Convert all numeric data to native Python types
        if not trends_data.empty:
            # Convert int64/float64 to native Python types
            trends_data = trends_data.astype(float)
            # Drop isPartial column as it's not needed
            if 'isPartial' in trends_data.columns:
                trends_data = trends_data.drop('isPartial', axis=1)
            print("Google Trends Data Retrieved Successfully")
        else:
            print("No trends data available.")
        
        return trends_data
    except Exception as e:
        logger.error(f"Error getting trends data: {e}")
        return pd.DataFrame()

# Function to analyze the sentiment of the text (competitor ads, snippets, etc.)
def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity  # Returns sentiment polarity (-1 to 1)

# Function to create a word cloud of frequent terms
def generate_wordcloud(texts):
    text = " ".join(texts)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()

# Function to format result text
def format_result(text, max_length=300):
    if not text:
        return ""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

# Function to display results and actionable insights
def display_results(results, trends_data):
    if not results:
        print("\nNo results found! Try modifying your search terms.")
    else:
        print("\nSearch Results:")
        print("=" * 100)
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Title: {result['title']}")
            print(f"Summary: {format_result(result['snippet'])}")
            if result['date']:
                print(f"Date: {result['date']}")
            print(f"URL: {result['link']}")
            print("=" * 100)
        
        print("\nGoogle Trends Insights:")
        if not trends_data.empty:
            print(trends_data.head())  # Display trends data

        # Sentiment Analysis on Snippets
        sentiments = [analyze_sentiment(result['snippet']) for result in results]
        avg_sentiment = sum(sentiments) / len(sentiments)
        print(f"\nAverage Sentiment of Competitor Ads: {avg_sentiment:.2f}")

        # Generate Word Cloud of Common Words
        snippets = [result['snippet'] for result in results]
        generate_wordcloud(snippets)

# Configure Gemini
def setup_gemini():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Add this to your .env file
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel('gemini-pro')

def scrape_youtube(query, num_results=5):
    """Scrape YouTube search results including video details."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        url = f'https://www.youtube.com/results?search_query={quote_plus(query)}'
        print(f"Searching YouTube for: {query}")
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', string=re.compile('var ytInitialData = '))
        
        if not script_tag:
            return []
            
        data_text = re.search(r'var ytInitialData = (.+?);</script>', str(script_tag)).group(1)
        data = json.loads(data_text)
        
        videos = []
        video_data = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [{}])[0].get('itemSectionRenderer', {}).get('contents', [])
        
        for video in video_data:
            if 'videoRenderer' in video:
                video_info = video['videoRenderer']
                try:
                    video_data = {
                        'title': video_info.get('title', {}).get('runs', [{}])[0].get('text', ''),
                        'url': f"https://youtube.com/watch?v={video_info.get('videoId', '')}",
                        'channel_name': video_info.get('ownerText', {}).get('runs', [{}])[0].get('text', ''),
                        'description': video_info.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', ''),
                        'views': video_info.get('viewCountText', {}).get('simpleText', '0 views'),
                        'duration': video_info.get('lengthText', {}).get('simpleText', 'N/A'),
                        'published': video_info.get('publishedTimeText', {}).get('simpleText', 'N/A'),
                    }
                    videos.append(video_data)
                    
                    if len(videos) >= num_results:
                        break
                except Exception as e:
                    print(f"Error parsing video data: {str(e)}")
                    continue
        
        return videos
        
    except Exception as e:
        print(f"Error fetching YouTube results: {str(e)}")
        return []

def analyze_with_gemini(model, results: List[Dict], trends_data, keywords: List[str]):
    # Prepare the data for analysis
    if not trends_data.empty:
        trends_dict = {
            "trend_values": {
                keyword: trends_data[keyword].tolist() 
                for keyword in keywords if keyword in trends_data.columns
            },
            "dates": [d.strftime("%Y-%m-%d") for d in trends_data.index]
        }
    else:
        trends_dict = {"trend_values": {}, "dates": []}

    # Get YouTube content
    youtube_query = " ".join(keywords) + " marketing tips trends"
    youtube_results = scrape_youtube(youtube_query)

    context = {
        "keywords": keywords,
        "competitor_data": [
            {
                "title": r["title"],
                "snippet": r["snippet"][:200]
            } for r in results[:5]
        ],
        "trends_summary": trends_dict,
        "youtube_insights": youtube_results
    }
    
    # Customize prompt based on keywords
    business_type = "shoes" if "shoes" in [k.lower() for k in keywords] else "business"
    
    prompt = f"""
    As a Marketing Expert, analyze this market research data for a {business_type} business and provide actionable insights for creating effective ads.
    Focus specifically on the provided keywords: {', '.join(keywords)}

    Context:
    {json.dumps(context, indent=2)}

    Please provide a detailed analysis in the following format:

    1. Industry-Specific Analysis:
       - Current trends in the {business_type} market
       - Key customer segments and their preferences
       - Popular {business_type} categories and styles
       - Insights from YouTube content creators in this space

    2. Competitor Analysis:
       - Top competing brands in the {business_type} space
       - Their marketing strategies
       - Unique selling propositions
       - Popular marketing channels and content types

    3. Marketing Recommendations:
       - Key Pain Points: Main customer problems and needs
       - Effective Hooks: Compelling hooks for {business_type} ads
       - Content Strategy: Best performing content formats
       - Visual Elements: Photography, design, and presentation tips
       - Messaging: Communication style that resonates with target audience
       - Video Marketing: Tips based on successful YouTube content

    4. Ad Campaign Suggestions:
       - 3 Creative Ad Headlines specific to {business_type}
       - 2-3 Ad Copy Variations
       - Video Ad Concepts
       - Call-to-Action Examples
       - Hashtag Suggestions
       - Platform-specific Recommendations

    5. Seasonal Opportunities:
       - Upcoming seasonal trends
       - Event-based marketing opportunities
       - Special promotions timing
       - Content calendar suggestions

    Format the response in clear sections with bullet points for easy reading.
    Focus specifically on {business_type}-related insights and trends.
    Include specific examples from successful YouTube content where relevant.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating insights: {e}"

def generate_insights_dashboard(results, trends_data, keywords):
    """Generate a comprehensive insights dashboard in JSON format"""
    try:
        print("🔍 Starting insights generation...")  # Console log
        
        # Calculate high-level metrics
        total_results = len(results)
        sentiments = [analyze_sentiment(result['snippet']) for result in results]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Get AI insights
        model = setup_gemini()
        ai_insights = analyze_with_gemini(model, results, trends_data, keywords)
        
        # Convert trends data to JSON-serializable format
        if not trends_data.empty:
            trends_dict = {
                "data": trends_data.reset_index().to_dict(orient='records'),
                "keywords": keywords
            }
            # Convert datetime objects to string format
            for record in trends_dict["data"]:
                record["date"] = record["date"].strftime("%Y-%m-%d")
        else:
            trends_dict = {"data": [], "keywords": keywords}
        
        # Create response data
        dashboard_data = {
            "metadata": {
                "total_sources": total_results,
                "market_sentiment": {
                    "score": round(avg_sentiment, 2),
                    "label": "Positive" if avg_sentiment > 0 else "Negative"
                },
                "key_topics": keywords
            },
            "ai_insights": ai_insights,
            "trend_analysis": {
                "google_trends": trends_dict
            },
            "competitor_analysis": [
                {
                    "title": result['title'],
                    "summary": format_result(result['snippet'], 150),
                    "url": result['link'],
                    "sentiment": round(analyze_sentiment(result['snippet']), 2)
                } for result in results[:5]
            ]
        }

        print("📊 Dashboard data generated successfully")  # Console log

        # Insert into database
        try:
            print("💾 Attempting to save to database...")  # Console log
            formatted_data = {
                "query": " ".join(keywords),
                "timestamp": datetime.now().isoformat(),
                "analysis": dashboard_data,
                "charts_data": prepare_chart_data(dashboard_data)
            }
            
            # Debug print the data being sent to database
            print("📝 Data being sent to database:")
            print(json.dumps(formatted_data, indent=2))
            
            result = db_manager.insert_document(formatted_data)
            if result:
                print("✅ Successfully saved to database")
            else:
                print("❌ Failed to save to database")
                print("Database result:", result)
        except Exception as db_error:
            print(f"❌ Database error: {str(db_error)}")
            print(f"Error type: {type(db_error)}")
            print(f"Error details: {str(db_error)}")
        
        return dashboard_data
        
    except Exception as e:
        print(f"❌ Error in generate_insights_dashboard: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        return None

def prepare_chart_data(analysis):
    """Prepare chart-friendly data from analysis"""
    try:
        # Extract trends data for time series chart
        trends_data = analysis.get('trend_analysis', {}).get('google_trends', {}).get('data', [])
        
        # Prepare data for charts
        charts_data = {
            'trends_chart': {
                'labels': [item['date'] for item in trends_data],
                'datasets': [
                    {
                        'label': 'Search Interest',
                        'data': [item.get(key, 0) for item in trends_data]
                    } for key in analysis.get('metadata', {}).get('key_topics', [])
                ]
            },
            'sentiment_chart': {
                'labels': ['Positive', 'Neutral', 'Negative'],
                'data': [
                    len([r for r in analysis.get('competitor_analysis', []) if r.get('sentiment', 0) > 0.2]),
                    len([r for r in analysis.get('competitor_analysis', []) if -0.2 <= r.get('sentiment', 0) <= 0.2]),
                    len([r for r in analysis.get('competitor_analysis', []) if r.get('sentiment', 0) < -0.2])
                ]
            },
            'competitor_sentiment': {
                'labels': [comp.get('title', '').split('|')[0][:30] for comp in analysis.get('competitor_analysis', [])],
                'data': [comp.get('sentiment', 0) for comp in analysis.get('competitor_analysis', [])]
            },
            'topic_distribution': {
                'labels': analysis.get('metadata', {}).get('key_topics', []),
                'data': [
                    sum(1 for comp in analysis.get('competitor_analysis', [])
                        if any(topic.lower() in comp.get('title', '').lower() 
                        for topic in analysis.get('metadata', {}).get('key_topics', [])))
                ]
            }
        }
        return charts_data
    except Exception as e:
        logger.error(f"Error preparing chart data: {str(e)}")
        return {}

def art_finder(user_input):
    try:
        # Extract keywords
        keywords = extract_keywords(user_input)
        if not keywords:
            return {
                "error": True,
                "message": "No valid keywords extracted from input",
                "status": "failed"
            }
        
        # Get trends data
        trends_data = get_google_trends_data(keywords)
        
        # Generate insights dashboard
        dashboard_data = {
            "metadata": {
                "key_topics": keywords,
                "timestamp": datetime.now().isoformat()
            },
            "trend_analysis": {
                "google_trends": {
                    "data": [],
                    "keywords": keywords
                }
            }
        }

        # Process trends data if available
        if not trends_data.empty:
            try:
                trends_list = []
                for index, row in trends_data.iterrows():
                    data_point = {
                        'date': index.strftime('%Y-%m-%d'),
                    }
                    # Convert all numeric values to native Python float
                    for col in trends_data.columns:
                        # Explicitly convert numpy types to native Python types
                        value = row[col]
                        if hasattr(value, 'item'):  # Check if it's a numpy type
                            value = value.item()  # Convert to native Python type
                        data_point[col] = float(value)
                    trends_list.append(data_point)
                
                dashboard_data["trend_analysis"]["google_trends"]["data"] = trends_list
            except Exception as e:
                logger.error(f"Error processing trends data: {e}")

        # Get AI insights
        try:
            model = setup_gemini()
            ai_insights = analyze_with_gemini(model, [], trends_data, keywords)
            dashboard_data["ai_insights"] = ai_insights
        except Exception as e:
            logger.error(f"Error getting AI insights: {e}")
            dashboard_data["ai_insights"] = str(e)

        # Prepare chart data
        try:
            charts_data = prepare_chart_data(dashboard_data)
            # Ensure all numeric values are native Python types
            for chart_type, chart in charts_data.items():
                if 'data' in chart:
                    chart['data'] = [float(x) if isinstance(x, (int, float)) else x for x in chart['data']]
                if 'datasets' in chart:
                    for dataset in chart['datasets']:
                        if 'data' in dataset:
                            dataset['data'] = [float(x) if isinstance(x, (int, float)) else x for x in dataset['data']]
            dashboard_data["charts_data"] = charts_data
        except Exception as e:
            logger.error(f"Error preparing chart data: {e}")
            dashboard_data["charts_data"] = {}

        # Verify JSON serialization before returning
        try:
            # Convert any remaining numpy types to native Python types
            dashboard_data_serializable = json.loads(json.dumps(dashboard_data, default=lambda x: x.item() if hasattr(x, 'item') else str(x)))
            return dashboard_data_serializable
        except Exception as json_error:
            logger.error(f"JSON serialization error: {str(json_error)}")
            return {
                "error": True,
                "message": "Data serialization error",
                "status": "failed",
                "keywords": keywords
            }
            
    except Exception as e:
        logger.error(f"Error in art_finder: {str(e)}")
        return {
            "error": True,
            "message": str(e),
            "status": "failed"
        }

if __name__ == "__main__":
    while True:
        try:
            user_input = input("\n🎯 Describe your business and ad goals (or type 'exit' to quit): ")
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
                
            if not user_input.strip():
                print("Please provide a valid input!")
                continue
                
            results = art_finder(user_input)
            
            # Pretty print the JSON results
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
        except Exception as e:
            error_response = {
                "error": True,
                "message": str(e),
                "status": "failed"
            }
            print(json.dumps(error_response, indent=2))
