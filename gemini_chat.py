"""
Gemini AI integration for natural language processing and query understanding.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

load_dotenv()


class GeminiChat:
    """Handles Gemini AI interactions for natural language understanding."""
    
    def __init__(self, model_name: str = "gemini-pro"):
        """Initialize Gemini model."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.conversation_history: List[Dict[str, str]] = []
    
    def get_system_prompt(self) -> str:
        """Get the system prompt explaining the chatbot's capabilities."""
        return """You are a helpful assistant for planning Margazhi season concert schedules in Chennai, India.

You have access to a database of concert schedules with the following information:
- Date and Time
- Artist(s) name
- Instruments/Details
- Venue name
- Source (which organization provided the schedule)

Your capabilities:
1. Search concerts by date (e.g., "December 15", "Dec 15", "2025-12-15")
2. Search concerts by artist name
3. Search concerts by venue name
4. Search concerts by location/area (e.g., "Mylapore", "T. Nagar")
5. Search concerts by time of day (morning, afternoon, evening, night)
6. Combine multiple filters
7. Plan routes between multiple venues
8. Suggest optimal concert sequences based on time and location

When users ask questions, extract the relevant information and provide helpful, natural responses.
Be conversational and helpful. If you need to search for concerts, indicate what you're searching for."""
    
    def process_query(self, user_query: str, context: Optional[Dict] = None) -> str:
        """
        Process a user query and generate a response.
        
        Args:
            user_query: The user's natural language query
            context: Optional context dictionary with available data info
        
        Returns:
            AI-generated response
        """
        # Build prompt with context
        prompt_parts = [self.get_system_prompt()]
        
        if context:
            context_str = f"\n\nAvailable data context:\n"
            if 'date_range' in context:
                context_str += f"- Date range: {context['date_range']}\n"
            if 'total_concerts' in context:
                context_str += f"- Total concerts: {context['total_concerts']}\n"
            if 'venues' in context and len(context['venues']) > 0:
                context_str += f"- Sample venues: {', '.join(context['venues'][:10])}\n"
            prompt_parts.append(context_str)
        
        # Add conversation history
        for msg in self.conversation_history[-5:]:  # Last 5 messages for context
            prompt_parts.append(f"{msg['role']}: {msg['content']}")
        
        # Add current query
        prompt_parts.append(f"User: {user_query}")
        prompt_parts.append("Assistant:")
        
        try:
            full_prompt = "\n".join(prompt_parts)
            response = self.model.generate_content(full_prompt)
            
            # Add to conversation history
            self.conversation_history.append({"role": "User", "content": user_query})
            self.conversation_history.append({"role": "Assistant", "content": response.text})
            
            return response.text
        except Exception as e:
            return f"I encountered an error processing your query: {str(e)}. Please try again."
    
    def extract_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Extract structured query parameters from natural language.
        
        Args:
            user_query: The user's natural language query
        
        Returns:
            Dictionary with extracted query parameters:
            - date: date string if found
            - date_range: tuple of (start, end) if found
            - artist: artist name if found
            - venue: venue name if found
            - location: location/area name if found
            - time_of_day: 'morning', 'afternoon', 'evening', or 'night'
            - intent: 'search', 'route_planning', 'info', etc.
        """
        extraction_prompt = f"""Extract structured query parameters from this user query about concert schedules.

User query: "{user_query}"

Extract the following information if present:
1. Date: specific date mentioned (format as YYYY-MM-DD if year is clear, or just month and day like "Dec 15")
2. Date range: start and end dates if a range is mentioned
3. Artist: artist name(s) mentioned
4. Venue: venue name(s) mentioned
5. Location: area/location name (e.g., Mylapore, T. Nagar)
6. Time of day: morning, afternoon, evening, or night
7. Intent: what the user wants to do (search, route_planning, info, etc.)
8. Is this a follow-up query? Look for words like "filter", "only", "those", "these", "the ones", "them" that suggest the user is refining previous results.

Respond in JSON format only, with keys: date, date_range, artist, venue, location, time_of_day, intent, is_followup.
If a field is not found, use null. For date_range, use array [start_date, end_date] or null.
For intent, use one of: "search", "route_planning", "info", "help", or "unknown".
For is_followup, use true if the query references previous results, false otherwise.

Example response:
{{"date": "2025-12-15", "date_range": null, "artist": "T.M. Krishna", "venue": null, "location": null, "time_of_day": "evening", "intent": "search", "is_followup": false}}

Now extract from the user query above:"""
        
        try:
            response = self.model.generate_content(extraction_prompt)
            response_text = response.text.strip()
            
            # Try to parse JSON from response
            import json
            import re
            
            # Extract JSON from response (might have markdown code blocks)
            # Try to find JSON in code blocks first
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
                result = json.loads(json_str)
                return result
            
            # Try to find JSON object in the text
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                return result
            else:
                # Fallback: try to parse the whole response
                result = json.loads(response_text)
                return result
        except Exception as e:
            # Fallback extraction using simple keyword matching
            data_loader = getattr(self, 'data_loader', None)
            return self._fallback_extraction(user_query, data_loader=data_loader)
    
    def _fallback_extraction(self, user_query: str, data_loader=None) -> Dict[str, Any]:
        """Fallback extraction using simple keyword matching."""
        import re
        from datetime import datetime, timedelta
        
        query_lower = user_query.lower()
        result = {
            "date": None,
            "date_range": None,
            "artist": None,
            "venue": None,
            "location": None,
            "time_of_day": None,
            "intent": "search",
            "is_followup": False
        }
        
        # Check for follow-up indicators
        followup_keywords = ['filter', 'only', 'just', 'those', 'these', 'the ones', 'them', 'show me']
        if any(keyword in query_lower for keyword in followup_keywords):
            result["is_followup"] = True
        
        # Try to extract date patterns
        # Look for "December 15", "Dec 15", "15 December", etc.
        date_patterns = [
            (r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})', ['%B %d']),
            (r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})', ['%b %d']),
            (r'(\d{1,2})\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)', ['%d %B']),
            (r'(\d{1,2})\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', ['%d %b']),
            (r'(\d{4}-\d{2}-\d{2})', ['%Y-%m-%d']),  # YYYY-MM-DD format
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', ['%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y']),
        ]
        
        for pattern, formats in date_patterns:
            match = re.search(pattern, user_query, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                try:
                    # Try parsing various date formats
                    for fmt in formats:
                        try:
                            parsed = datetime.strptime(date_str, fmt)
                            # Format as "Dec 15" for month/day or YYYY-MM-DD for full dates
                            if fmt == '%Y-%m-%d':
                                result["date"] = date_str
                            else:
                                result["date"] = parsed.strftime('%b %d')
                            break
                        except:
                            continue
                    if result["date"]:
                        break
                except:
                    pass
        
        # Handle relative dates
        if 'today' in query_lower:
            result["date"] = datetime.now().strftime('%Y-%m-%d')
        elif 'tomorrow' in query_lower:
            result["date"] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'yesterday' in query_lower:
            result["date"] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Extract artist - look for patterns like "by [artist]", "[artist] concert", "when is [artist] singing", etc.
        artist_patterns = [
            r'(?:when|where|what|show|find|is|are).*?(?:is|are|by|singing|performing|concert).*?([A-Z][A-Za-z\s\.&,]+?)(?:\s+singing|\s+performing|\s+concert|\s+at|\s+on|$)',
            r'by\s+([A-Z][A-Za-z\s\.&,]+?)(?:\s+concert|\s+performing|\s+at|$)',
            r'([A-Z][A-Za-z\s\.&,]+?)\s+concert',
            r'concerts?\s+by\s+([A-Z][A-Za-z\s\.&,]+?)(?:\s+at|$)',
            r'([A-Z][A-Za-z\s\.&,]+?)\s+performing',
            r'([A-Z][A-Za-z\s\.&,]+?)\s+singing',
        ]
        
        for pattern in artist_patterns:
            match = re.search(pattern, user_query, re.IGNORECASE)
            if match:
                artist = match.group(1).strip()
                # Clean up common suffixes and prefixes
                artist = re.sub(r'^(when|where|what|show|find|is|are|by)\s+', '', artist, flags=re.IGNORECASE)
                artist = re.sub(r'\s+(concert|performing|singing|at|on|in|by)$', '', artist, flags=re.IGNORECASE)
                # Remove common stop words
                if len(artist) > 2 and artist.lower() not in ['the', 'a', 'an', 'at', 'on', 'in', 'by', 'when', 'where', 'what', 'is', 'are', 'show', 'find']:
                    result["artist"] = artist
                    break
        
        # If no pattern match but query contains "singing" or "performing", try to extract the name before it
        if not result["artist"] and ('singing' in query_lower or 'performing' in query_lower):
            # Look for words that might be artist names (capitalized words before "singing"/"performing")
            name_match = re.search(r'([A-Z][A-Za-z\s\.&,]+?)\s+(?:singing|performing)', user_query, re.IGNORECASE)
            if name_match:
                potential_artist = name_match.group(1).strip()
                # Remove question words
                potential_artist = re.sub(r'^(when|where|what|is|are)\s+', '', potential_artist, flags=re.IGNORECASE)
                if len(potential_artist) > 2:
                    result["artist"] = potential_artist
        
        # Extract venue - look for patterns like "at [venue]", "in [venue]", "[venue] concert"
        venue_patterns = [
            r'at\s+([A-Z][A-Za-z\s\.,&]+?)(?:\s+on|\s+concert|$)',
            r'in\s+([A-Z][A-Za-z\s\.,&]+?)(?:\s+on|\s+concert|$)',
            r'([A-Z][A-Za-z\s\.,&]+?)\s+concert',
            r'concerts?\s+at\s+([A-Z][A-Za-z\s\.,&]+?)(?:\s+on|$)',
        ]
        
        # Common venue names to help with extraction
        common_venues = [
            'music academy', 'krishna gana sabha', 'mylapore fine arts', 
            'narada gana sabha', 'bharatiya vidya bhavan', 'vani mahal',
            'kalakshetra', 'arkay convention', 'sri ygp auditorium'
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, user_query, re.IGNORECASE)
            if match:
                venue = match.group(1).strip()
                # Clean up common suffixes
                venue = re.sub(r'\s+(concert|on|at|in)$', '', venue, flags=re.IGNORECASE)
                if len(venue) > 2:
                    result["venue"] = venue
                    break
        
        # If no pattern match, try matching against common venues
        if not result["venue"]:
            for venue_name in common_venues:
                if venue_name in query_lower:
                    result["venue"] = venue_name.title()
                    break
        
        # Extract location (area names like Mylapore, T. Nagar)
        location_keywords = ['mylapore', 't. nagar', 't nagar', 'nagar', 'adyar', 'besant nagar']
        for loc in location_keywords:
            if loc in query_lower:
                result["location"] = loc.title()
                break
        
        # Extract time of day
        if any(word in query_lower for word in ['morning', 'am', 'early']):
            result["time_of_day"] = "morning"
        elif any(word in query_lower for word in ['afternoon', 'pm']):
            result["time_of_day"] = "afternoon"
        elif any(word in query_lower for word in ['evening']):
            result["time_of_day"] = "evening"
        elif any(word in query_lower for word in ['night', 'late']):
            result["time_of_day"] = "night"
        
        # Extract intent
        if any(word in query_lower for word in ['route', 'plan', 'directions', 'travel']):
            result["intent"] = "route_planning"
        elif any(word in query_lower for word in ['help', 'what can', 'how can']):
            result["intent"] = "help"
        elif any(word in query_lower for word in ['info', 'information', 'tell me about']):
            result["intent"] = "info"
        
        return result
    
    def generate_natural_response(self, query_results: Dict[str, Any], user_query: str) -> str:
        """
        Generate a natural language response based on query results.
        
        Args:
            query_results: Dictionary with search results and metadata
            user_query: Original user query
        
        Returns:
            Natural language response
        """
        num_results = query_results.get('count', 0)
        concerts = query_results.get('concerts', [])
        
        if num_results == 0:
            response_prompt = f"""The user asked: "{user_query}"

No concerts were found matching this query. Generate a helpful, friendly response explaining that no concerts were found and suggest ways to refine the search (e.g., try a different date, artist name, or venue)."""
        else:
            # Format concert list for context
            concert_list = "\n".join([
                f"- {c.get('Date', '')} {c.get('Time', '')}: {c.get('Artist(s)', '')} at {c.get('Venue', '')}"
                for c in concerts[:10]  # First 10 for context
            ])
            
            response_prompt = f"""The user asked: "{user_query}"

Found {num_results} concert(s) matching the query. Here are the results:

{concert_list}

Generate a helpful, natural response summarizing the results. Mention the number of concerts found, highlight key information (dates, artists, venues), and offer to help with route planning if multiple venues are involved."""
        
        try:
            response = self.model.generate_content(response_prompt)
            return response.text
        except Exception as e:
            # Fallback response
            if num_results == 0:
                return "I couldn't find any concerts matching your query. Try searching by a different date, artist, or venue."
            else:
                return f"I found {num_results} concert(s) matching your query. Please check the results below."
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

