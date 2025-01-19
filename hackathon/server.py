from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from scrap import art_finder
from db import db_manager
from datetime import datetime
import json
import logging
import google.generativeai as genai
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    message: str

class QueryResponse(BaseModel):
    query: str
    timestamp: str
    analysis: dict

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

def prepare_chart_data(analysis):
    """Prepare chart-friendly data from analysis"""
    
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

@app.get("/")
async def root():
    return {"message": "Welcome to the Market Research API"}

@app.post("/analyze")
async def analyze_query(request: QueryRequest):
    try:
        print(f"📝 Received analysis request: {request.message}")
        
        # Get analysis using art_finder from scrap.py
        analysis = art_finder(request.message)
        
        if not analysis:
            print("❌ No analysis generated")
            raise HTTPException(status_code=400, detail="Could not generate analysis")
        
        print("✅ Analysis completed successfully")
        return analysis
        
    except Exception as e:
        print(f"❌ Error in analyze_query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    try:
        documents = db_manager.get_all_documents()
        return {"history": documents}
    except Exception as e:
        print(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Separate chat handler class
class ChatHandler:
    def __init__(self):
        self.model = None
        self.setup_model()
    
    def setup_model(self):
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def clean_response(self, text: str) -> str:
        # Remove common prefixes and meta-references
        phrases_to_remove = [
            "Hi,", "Hello,", "Greetings,",
            "Based on", "According to", "The data shows",
            "Research indicates", "Analysis suggests",
            "Looking at", "ARTFinder here"
        ]
        
        cleaned = text.strip()
        for phrase in phrases_to_remove:
            cleaned = cleaned.replace(phrase, "").strip()
        
        return cleaned
    
    async def get_response(self, question: str, context_data: list) -> str:
        # Extract only essential insights from context
        insights = []
        for doc in context_data:
            if isinstance(doc, dict) and doc.get("analysis"):
                insight = doc.get("analysis", {}).get("ai_insights", "")
                if insight:
                    insights.append(insight)
        
        prompt = f"""
        Context (use this information but don't mention it):
        {' '.join(insights[-3:])}  # Only use last 3 insights

        Question: {question}

        Rules:
        - Give a direct answer in 1-2 sentences
        - No greetings or introductions
        - No emojis or formatting
        - No data or statistics
        - If you can't answer from context, say "I don't have that information"
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.clean_response(response.text)
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "Sorry, I couldn't process that request."

# Initialize chat handler
chat_handler = ChatHandler()

# Simplified chat endpoint
@app.post("/chat")
async def chat_analysis(request: ChatMessage):
    try:
        # Get last 3 documents from database
        historical_data = db_manager.get_all_documents()[-3:]
        
        # Get response using chat handler
        response_text = await chat_handler.get_response(
            request.message,
            historical_data
        )
        
        return ChatResponse(response=response_text)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions for data analysis
def extract_market_trends(historical_data: List[dict]) -> dict:
    """Extract market trends from historical data"""
    try:
        all_topics = []
        for doc in historical_data:
            topics = doc.get("analysis", {}).get("metadata", {}).get("key_topics", [])
            all_topics.extend(topics)
        
        # Count frequency of topics
        topic_frequency = {}
        for topic in all_topics:
            topic_frequency[topic] = topic_frequency.get(topic, 0) + 1
        
        # Sort by frequency
        sorted_trends = dict(sorted(topic_frequency.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:5])
        
        return {
            "top_trends": sorted_trends,
            "total_topics": len(all_topics)
        }
    except Exception as e:
        print(f"❌ Error extracting market trends: {str(e)}")
        return {}

def extract_competitor_strategies(historical_data: List[dict]) -> dict:
    """Extract competitor strategies from historical data"""
    try:
        all_strategies = []
        for doc in historical_data:
            competitors = doc.get("analysis", {}).get("competitor_analysis", [])
            for comp in competitors:
                if comp.get("summary"):
                    all_strategies.append({
                        "summary": comp.get("summary"),
                        "sentiment": comp.get("sentiment", 0)
                    })
        
        # Sort by sentiment to get top performing strategies
        sorted_strategies = sorted(all_strategies, 
                                 key=lambda x: x.get("sentiment", 0), 
                                 reverse=True)[:5]
        
        return {
            "top_strategies": sorted_strategies,
            "total_analyzed": len(all_strategies)
        }
    except Exception as e:
        print(f"❌ Error extracting competitor strategies: {str(e)}")
        return {}

def calculate_average_sentiment(historical_data: List[dict]) -> dict:
    """Calculate average sentiment from historical data"""
    try:
        sentiments = []
        for doc in historical_data:
            sentiment = doc.get("analysis", {}).get("metadata", {}).get("market_sentiment", {}).get("score", 0)
            sentiments.append(sentiment)
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            "average_score": round(avg_sentiment, 2),
            "label": "Positive" if avg_sentiment > 0 else "Negative",
            "total_analyzed": len(sentiments)
        }
    except Exception as e:
        print(f"❌ Error calculating average sentiment: {str(e)}")
        return {}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
