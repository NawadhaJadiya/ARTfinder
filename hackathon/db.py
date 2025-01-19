from astrapy.db import AstraDB
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize the client
db = AstraDB(
    token = os.getenv("token_astra"),
    api_endpoint=os.getenv("api_endpoint")
)

class DatabaseManager:
    def __init__(self):
        try:
            self.collection = db.collection("market_research")
            print("✅ Connected to AstraDB collection: market_research")
        except Exception as e:
            print(f"❌ Failed to connect to database: {str(e)}")
            raise
    
    def clear_collection(self):
        """Clear all data from the collection"""
        try:
            print("🗑️ Clearing collection...")
            # Delete all documents in the collection
            result = self.collection.delete_many({})
            count = result.deleted_count if result else 0
            print(f"✅ Cleared {count} documents from collection")
            return True
        except Exception as e:
            print(f"❌ Error clearing collection: {str(e)}")
            return False
    
    def insert_document(self, data):
        """Insert a single document into the collection"""
        try:
            print("📥 Starting document insertion...")
            
            # First, clear the collection
            self.clear_collection()
            
            # Verify data structure
            print("📋 Verifying data structure...")
            required_fields = ["query", "timestamp", "analysis", "charts_data"]
            for field in required_fields:
                if field not in data:
                    print(f"❌ Missing required field: {field}")
                    return None
            
            # Debug print the data being inserted
            print("📝 Data being inserted:")
            print(json.dumps(data, indent=2))
            
            # Insert the document
            print("💾 Inserting document into database...")
            result = self.collection.insert_one(data)
            
            if result:
                print(f"✅ Document inserted successfully with ID: {result}")
                
                # Verify the document was inserted
                inserted_doc = self.collection.find_one({"_id": result.inserted_id})
                if inserted_doc:
                    print("✅ Document verified in database")
                    print(json.dumps(inserted_doc, indent=2))
                else:
                    print("⚠️ Could not verify inserted document")
            else:
                print("❌ No result returned from database insertion")
            
            return result
                
        except Exception as e:
            print(f"❌ Error inserting document: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            return None
    
    def get_all_documents(self):
        """Get all documents from the collection"""
        try:
            print("📚 Fetching all documents...")
            response = self.collection.find({})
            
            print("🔍 Raw response type:", type(response))
            print("🔍 Raw response structure:", json.dumps(response, indent=2))
            
            # Extract documents from AstraDB response structure
            if isinstance(response, dict):
                # Handle AstraDB response format
                documents = response.get('data', {}).get('documents', [])
            else:
                documents = []
            
            results = []
            for doc in documents:
                if isinstance(doc, dict):
                    # Document is already a dictionary
                    results.append(doc)
                elif isinstance(doc, str):
                    try:
                        parsed_doc = json.loads(doc)
                        results.append(parsed_doc)
                    except json.JSONDecodeError:
                        print(f"⚠️ Could not parse document: {doc[:100]}...")
                        continue
                    
            print(f"✅ Retrieved {len(results)} valid documents")
            
            # Debug print first document if available
            if results:
                print("📝 First document structure:")
                print(json.dumps(results[0], indent=2))
            else:
                print("⚠️ No valid documents found")
            
            return results
            
        except Exception as e:
            print(f"❌ Error fetching documents: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            return []

# Create a single instance of DatabaseManager
db_manager = DatabaseManager()