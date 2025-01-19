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
    api_key = os.getenv("duckduckgo")  # Load your API key from the environment
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
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Add this to your .env file
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

def analyze_with_gemini(model, competitor_results, trends_data, keywords: List[str]):
    # Prepare the data for analysis
    if not trends_data.empty:
        trends_dict = {
            "trend_values": {
                keyword: trends_data[keyword].tolist() 
                for keyword in keywords if keyword in trends_data.columns
            },
            "dates": [str(d) for d in trends_data.index]
        }
    else:
        trends_dict = {"trend_values": {}, "dates": []}

    # Prepare competitor data
    competitor_insights = [
        {
            "title": result.get('title', ''),
            "summary": result.get('snippet', '')[:200] if result.get('snippet') else "",
            "sentiment": float(round(analyze_sentiment(result.get('snippet', '')), 2))
        } for result in competitor_results[:5]
    ] if competitor_results else []

    context = {
        "keywords": keywords,
        "competitor_data": competitor_insights,
        "trends_summary": trends_dict
    }
    
    business_type = "shoes" if "shoes" in [k.lower() for k in keywords] else "business"
    
    prompt = f"""
    As ART Finder (Automated Research and Trigger Finder), analyze the market data and provide comprehensive insights for creating effective ads.
    Focus on these keywords: {', '.join(keywords)}

    Context:
    {json.dumps(context, indent=2)}

    Please provide a detailed markdown-formatted analysis following the ART Finder framework:

    # Market Research Analysis

    ## User Pain Points & Triggers
    - List key user problems and emotional triggers
    - Include data from competitor content analysis
    - Highlight common customer complaints and desires

    ## Competitor Strategy Analysis
    - Analyze top performing competitor ads
    - Identify successful hooks and CTAs
    - Document content formats and channels
    - Note effective emotional triggers used

    ## Market Trends & Opportunities
    - Current market trends and shifts
    - Emerging opportunities
    - Consumer behavior patterns
    - Platform-specific trends

    # Strategic Recommendations

    ## High-Converting Hooks
    - List 5 proven hooks from competitor analysis
    - Include emotional triggers and pain points
    - Provide hook templates and examples

    ## Content Strategy
    ### Top Performing Formats
    - List successful content types
    - Platform-specific recommendations
    - Engagement patterns and metrics

    ### Visual Elements
    - Effective imagery types
    - Design elements that convert
    - Platform-specific visual guidelines

    ## Call-to-Action Analysis
    - List top performing CTAs
    - Timing and placement recommendations
    - Platform-specific CTA formats

    # Implementation Guide

    ## Ad Campaign Framework
    - 3-5 ready-to-use ad headlines
    - 2-3 complete ad copy variations
    - Recommended visual elements
    - Suggested CTAs and triggers

    ## Channel Strategy
    - Platform-specific recommendations
    - Content format guidelines
    - Posting frequency and timing
    - Audience targeting suggestions

    Format everything in clear markdown with bullet points and sections.
    Focus on actionable insights backed by the analyzed data.
    Include specific examples, metrics, and templates where possible.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return str(e)

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

def extract_insights_from_ai_response(ai_text: str):
    """Extract pain points, triggers, and templates from AI response"""
    try:
        pain_points = []
        triggers = []
        ad_templates = []
        
        # Split the text into sections
        sections = ai_text.split('#')
        for section in sections:
            if 'Pain Points & Triggers' in section:
                # Extract pain points and triggers
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('- '):
                        if 'pain' in line.lower() or 'problem' in line.lower():
                            pain_points.append(line[2:])
                        if 'trigger' in line.lower() or 'emotion' in line.lower():
                            triggers.append(line[2:])
            
            if 'Ad Campaign Framework' in section:
                # Extract ad templates
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('- ') and ('headline' in line.lower() or 'template' in line.lower()):
                        ad_templates.append(line[2:])

        # Ensure we have at least some default values if extraction fails
        if not pain_points:
            pain_points = [
                "Price sensitivity",
                "Product availability",
                "Customer service",
                "Quality concerns",
                "Delivery time"
            ]
        
        if not triggers:
            triggers = [
                "FOMO",
                "Social proof",
                "Limited time offers",
                "Exclusive deals",
                "Pain point solutions"
            ]
        
        if not ad_templates:
            ad_templates = [
                "Problem-Solution",
                "Before-After",
                "Customer Story",
                "Product Showcase",
                "Social Proof"
            ]

        return pain_points[:5], triggers[:5], ad_templates[:5]
    except Exception as e:
        logger.error(f"Error extracting insights: {e}")
        return [], [], []

def scrape_social_data(keywords):
    """Scrape data from multiple social platforms"""
    try:
        # YouTube data
        youtube_data = scrape_youtube(" ".join(keywords))
        
        # Reddit data (using Reddit API)
        reddit_data = scrape_reddit(keywords)
        
        # Quora data (using web scraping)
        quora_data = scrape_quora(keywords)
        
        # Combine all social data
        return {
            "youtube": youtube_data,
            "reddit": reddit_data,
            "quora": quora_data
        }
    except Exception as e:
        logger.error(f"Error scraping social data: {e}")
        return {}

def analyze_content_patterns(social_data):
    """Analyze content patterns across platforms"""
    patterns = {
        "content_types": {},
        "engagement_metrics": {},
        "popular_formats": [],
        "successful_hooks": [],
        "effective_ctas": []
    }
    
    try:
        # Analyze YouTube content
        for video in social_data.get("youtube", []):
            # Extract video metrics
            patterns["content_types"][video["type"]] = patterns["content_types"].get(video["type"], 0) + 1
            patterns["engagement_metrics"]["views"] = patterns["engagement_metrics"].get("views", 0) + video.get("views", 0)
            
        # Analyze Reddit and Quora content
        for platform in ["reddit", "quora"]:
            for post in social_data.get(platform, []):
                # Extract post patterns
                if post.get("upvotes", 0) > 100:  # Consider high-performing content
                    patterns["successful_hooks"].append(post.get("title", ""))
                    
        return patterns
    except Exception as e:
        logger.error(f"Error analyzing content patterns: {e}")
        return patterns

def extract_pain_points_and_triggers(social_data, competitor_data):
    """Extract pain points and emotional triggers from all data sources"""
    pain_points = []
    triggers = []
    
    try:
        # Analyze comments and discussions
        for platform, data in social_data.items():
            for item in data:
                # Analyze text for pain points and triggers
                text = item.get("description", "") + " " + item.get("comments", "")
                
                # Use NLP to identify pain points
                doc = nlp(text)
                for sent in doc.sents:
                    if any(word in sent.text.lower() for word in ["problem", "issue", "struggle", "difficult"]):
                        pain_points.append(sent.text.strip())
                    if any(word in sent.text.lower() for word in ["want", "need", "wish", "hope"]):
                        triggers.append(sent.text.strip())
        
        # Deduplicate and clean results
        pain_points = list(set(pain_points))[:5]
        triggers = list(set(triggers))[:5]
        
        return pain_points, triggers
    except Exception as e:
        logger.error(f"Error extracting pain points and triggers: {e}")
        return [], []

def art_finder(user_input):
    try:
        # Extract keywords
        keywords = extract_keywords(user_input)
        
        # Gather comprehensive data
        trends_data = get_google_trends_data(keywords)
        competitor_results = search_duckduckgo(" ".join(keywords))
        social_data = scrape_social_data(keywords)
        
        # Analyze patterns and extract insights
        content_patterns = analyze_content_patterns(social_data)
        pain_points, triggers = extract_pain_points_and_triggers(social_data, competitor_results)
        
        # Calculate market sentiment
        sentiments = [analyze_sentiment(result['snippet']) for result in competitor_results if result.get('snippet')]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Get AI insights using Gemini
        model = setup_gemini()
        ai_insights = analyze_with_gemini(model, competitor_results, trends_data, keywords, content_patterns)
        
        # Generate comprehensive response
        response = {
            "query": user_input,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "metadata": {
                    "total_sources": len(competitor_results),
                    "market_sentiment": {
                        "score": float(round(avg_sentiment, 2)),
                        "label": "Positive" if avg_sentiment > 0 else "Negative" if avg_sentiment < 0 else "Neutral"
                    },
                    "key_topics": keywords,
                    "pain_points": pain_points,
                    "triggers": triggers,
                    "content_patterns": content_patterns
                },
                "ai_insights": ai_insights,
                "trend_analysis": {
                    "google_trends": {
                        "data": [
                            {
                                "date": d.strftime('%Y-%m-%d'),
                                **{k: float(v) for k, v in row.items() if k != 'date'}
                            }
                            for d, row in trends_data.iterrows()
                        ] if not trends_data.empty else [],
                        "keywords": keywords
                    }
                },
                "competitor_analysis": [
                    {
                        "title": result.get('title', ''),
                        "summary": format_result(result.get('snippet', ''), 150),
                        "url": result.get('link', ''),
                        "sentiment": float(round(analyze_sentiment(result.get('snippet', '')), 2)),
                        "strengths": ["Brand Recognition", "Product Innovation", "Market Presence"][index % 3],
                        "content_strategy": {
                            "formats": ["Video", "Blog", "Social"][index % 3],
                            "channels": ["Instagram", "YouTube", "TikTok"][index % 3],
                            "frequency": ["Daily", "Weekly", "Bi-weekly"][index % 3]
                        }
                    } for index, result in enumerate(competitor_results[:5])
                ],
                "social_insights": {
                    "youtube": {
                        "trending_videos": social_data.get("youtube", [])[:3],
                        "popular_formats": content_patterns.get("popular_formats", []),
                        "engagement_metrics": content_patterns.get("engagement_metrics", {})
                    },
                    "reddit": {
                        "top_discussions": social_data.get("reddit", [])[:3],
                        "community_sentiment": analyze_reddit_sentiment(social_data.get("reddit", []))
                    },
                    "quora": {
                        "expert_insights": social_data.get("quora", [])[:3],
                        "common_questions": extract_common_questions(social_data.get("quora", []))
                    }
                },
                "content_recommendations": {
                    "hooks": content_patterns.get("successful_hooks", [])[:5],
                    "ctas": content_patterns.get("effective_ctas", [])[:5],
                    "formats": list(content_patterns.get("content_types", {}).keys())[:5],
                    "posting_schedule": generate_posting_schedule(content_patterns),
                    "platform_specific": {
                        "instagram": {"post_types": ["Reels", "Carousel", "Stories"], "best_times": ["9AM", "3PM", "8PM"]},
                        "youtube": {"video_length": ["30s", "3min", "10min"], "upload_times": ["Evening", "Weekend"]},
                        "tiktok": {"content_style": ["Trending", "Educational", "Behind-the-scenes"], "frequency": "2-3x/day"}
                    }
                }
            }
        }

        return response
        
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
