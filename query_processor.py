"""
Query processor that extracts structured queries from natural language using Gemini.
"""

from typing import Dict, Any, Optional
from data_loader import ConcertDataLoader
from gemini_chat import GeminiChat
import pandas as pd


class QueryProcessor:
    """Processes natural language queries and executes searches."""
    
    def __init__(self, data_loader: ConcertDataLoader, gemini_chat: GeminiChat):
        """Initialize with data loader and Gemini chat."""
        self.data_loader = data_loader
        self.gemini_chat = gemini_chat
        # Pass data_loader reference to gemini_chat for fallback extraction
        if gemini_chat:
            gemini_chat.data_loader = data_loader
    
    def process(self, user_query: str, previous_results: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Process a user query and return results.
        
        Args:
            user_query: Natural language query from user
            previous_results: Optional DataFrame from previous query (for follow-up queries)
        
        Returns:
            Dictionary with:
            - 'intent': extracted intent
            - 'results': DataFrame with search results
            - 'count': number of results
            - 'response': natural language response
            - 'query_params': extracted query parameters
        """
        # Extract query intent and parameters
        query_params = self.gemini_chat.extract_query_intent(user_query)
        intent = query_params.get('intent', 'search')
        
        # Execute search based on intent
        if intent == 'route_planning':
            return self._handle_route_planning(user_query, query_params)
        elif intent == 'help' or intent == 'info':
            return self._handle_info_query(user_query)
        else:
            return self._handle_search_query(user_query, query_params, previous_results)
    
    def _handle_search_query(self, user_query: str, query_params: Dict[str, Any], previous_results: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Handle search queries."""
        # Build filters dictionary
        filters = {}
        
        if query_params.get('date'):
            filters['date'] = query_params['date']
        
        if query_params.get('date_range'):
            date_range = query_params['date_range']
            if isinstance(date_range, list) and len(date_range) == 2:
                filters['date_range'] = tuple(date_range)
        
        if query_params.get('artist'):
            filters['artist'] = query_params['artist']
        
        if query_params.get('venue'):
            filters['venue'] = query_params['venue']
        
        if query_params.get('location'):
            filters['location'] = query_params['location']
        
        if query_params.get('time_of_day'):
            filters['time_of_day'] = query_params['time_of_day']
        
        # If no structured filters but query seems to be about an artist, try artist search first
        if not filters and not previous_results:
            # Check if query contains artist-like patterns (singing, performing, etc.)
            import re
            query_lower = user_query.lower()
            is_artist_query = any(word in query_lower for word in ['singing', 'performing', 'concert by', 'by'])
            
            if is_artist_query:
                # Try to extract artist name using fallback extraction
                if self.gemini_chat:
                    extracted = self.gemini_chat._fallback_extraction(user_query, self.data_loader)
                    if extracted.get('artist'):
                        # Try artist search with extracted name
                        artist_results = self.data_loader.search_by_artist(extracted['artist'])
                        if len(artist_results) > 0:
                            filters['artist'] = extracted['artist']
                        else:
                            # Try with just the first word if it's a common name
                            words = extracted['artist'].split()
                            if len(words) > 0:
                                first_word = words[0]
                                artist_results = self.data_loader.search_by_artist(first_word)
                                if len(artist_results) > 0:
                                    filters['artist'] = first_word
        
        # If we have previous results and this is a follow-up, filter previous results
        if previous_results is not None and query_params.get('is_followup', False):
            results_df = previous_results.copy()
            
            # Apply new filters to previous results
            if filters.get('date'):
                date_results = self.data_loader.search_by_date(filters['date'])
                if len(date_results) > 0:
                    results_df = results_df[results_df.index.isin(date_results.index)]
                else:
                    results_df = pd.DataFrame()
            
            if filters.get('artist') and len(results_df) > 0:
                artist_results = self.data_loader.search_by_artist(filters['artist'])
                if len(artist_results) > 0:
                    results_df = results_df[results_df.index.isin(artist_results.index)]
                else:
                    results_df = pd.DataFrame()
            
            if filters.get('venue') and len(results_df) > 0:
                venue_results = self.data_loader.search_by_venue(filters['venue'])
                if len(venue_results) > 0:
                    results_df = results_df[results_df.index.isin(venue_results.index)]
                else:
                    results_df = pd.DataFrame()
            
            if filters.get('location') and len(results_df) > 0:
                location_results = self.data_loader.search_by_location(filters['location'])
                if len(location_results) > 0:
                    results_df = results_df[results_df.index.isin(location_results.index)]
                else:
                    results_df = pd.DataFrame()
            
            if filters.get('time_of_day') and len(results_df) > 0:
                time_results = self.data_loader.search_by_time_of_day(filters['time_of_day'])
                if len(time_results) > 0:
                    results_df = results_df[results_df.index.isin(time_results.index)]
                else:
                    results_df = pd.DataFrame()
        else:
            # Execute search on full dataset
            if filters:
                results_df = self.data_loader.combine_filters(filters)
            else:
                # If no specific filters, try to search by any text in the query
                # This is a fallback for unclear queries
                results_df = self.search_by_text(user_query)
        
        # Convert to list of dictionaries for easier handling
        concerts = results_df.to_dict('records') if len(results_df) > 0 else []
        
        # Generate natural language response
        if self.gemini_chat:
            response = self.gemini_chat.generate_natural_response({
                'count': len(concerts),
                'concerts': concerts[:20]  # Limit to 20 for response generation
            }, user_query)
        else:
            # Fallback response without Gemini
            if len(concerts) == 0:
                response = "I couldn't find any concerts matching your query. Try searching by a different date, artist, or venue."
            else:
                response = f"I found {len(concerts)} concert(s) matching your query."
        
        return {
            'intent': 'search',
            'results': results_df,
            'count': len(concerts),
            'response': response,
            'query_params': query_params,
            'concerts': concerts
        }
    
    def _handle_route_planning(self, user_query: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route planning queries."""
        # First, try to find concerts mentioned in the query
        # This might involve multiple searches
        search_result = self._handle_search_query(user_query, query_params)
        
        return {
            'intent': 'route_planning',
            'results': search_result.get('results', pd.DataFrame()),
            'count': search_result.get('count', 0),
            'response': f"I found {search_result.get('count', 0)} concert(s). I can help you plan a route between these venues. Please select the concerts you'd like to attend.",
            'query_params': query_params,
            'concerts': search_result.get('concerts', [])
        }
    
    def _handle_info_query(self, user_query: str) -> Dict[str, Any]:
        """Handle informational queries."""
        # Get context about available data
        date_range = self.data_loader.get_date_range()
        venues = self.data_loader.get_all_venues()
        
        context = {
            'date_range': f"{date_range[0]} to {date_range[1]}" if date_range[0] else "Unknown",
            'total_concerts': len(self.data_loader.df) if self.data_loader.df is not None else 0,
            'venues': venues[:20]  # Sample venues
        }
        
        response = self.gemini_chat.process_query(user_query, context)
        
        return {
            'intent': 'info',
            'results': pd.DataFrame(),
            'count': 0,
            'response': response,
            'query_params': {},
            'concerts': []
        }
    
    def search_by_text(self, text: str) -> pd.DataFrame:
        """
        Smart text search that searches across all text fields and tries to extract structured components.
        
        Args:
            text: Text to search for
        
        Returns:
            DataFrame with matching concerts
        """
        if self.data_loader is None or self.data_loader.df is None:
            return pd.DataFrame()
        
        df = self.data_loader.df
        text_lower = text.lower().strip()
        
        # Try to extract date, artist, venue from text using fallback extraction
        if self.gemini_chat:
            extracted = self.gemini_chat._fallback_extraction(text, self.data_loader)
            
            # If we extracted structured components, use them
            if extracted.get('date') or extracted.get('artist') or extracted.get('venue'):
                filters = {}
                if extracted.get('date'):
                    filters['date'] = extracted['date']
                if extracted.get('artist'):
                    filters['artist'] = extracted['artist']
                if extracted.get('venue'):
                    filters['venue'] = extracted['venue']
                if extracted.get('location'):
                    filters['location'] = extracted['location']
                if extracted.get('time_of_day'):
                    filters['time_of_day'] = extracted['time_of_day']
                
                if filters:
                    return self.data_loader.combine_filters(filters)
        
        # Fallback: smart text search - prioritize Artist column for artist-like queries
        try:
            # Check if query seems to be about an artist (contains "singing", "performing", "by", etc.)
            import re
            is_artist_query = any(word in text_lower for word in ['singing', 'performing', 'concert by', 'by', 'when is', 'where is', 'who is'])
            
            # Split text into words for better matching
            words = [w for w in text_lower.split() if len(w) > 2]  # Filter short words
            
            if is_artist_query and words:
                # For artist queries, ONLY search in Artist column - NEVER search Instruments/Details
                # This prevents matching "Sanjay Suresh" (violinist) when searching for "Sanjay" (vocalist)
                artist_mask = pd.Series([False] * len(df))
                for word in words:
                    artist_mask = artist_mask | df['Artist(s)'].astype(str).str.lower().str.contains(word, na=False, regex=False)
                
                # Return only Artist column matches
                results = df[artist_mask].sort_values(['Date', 'TimeParsed']).copy()
                return results
            
            # General text search across multiple columns (but exclude Instruments/Details for artist queries)
            mask = pd.Series([False] * len(df))
            for word in words:
                if is_artist_query:
                    # For artist queries, ONLY search Artist column (not Instruments/Details)
                    word_mask = df['Artist(s)'].astype(str).str.lower().str.contains(word, na=False, regex=False)
                else:
                    # For general queries, search Artist, Venue, but NOT Instruments/Details
                    # (Instruments/Details often contains accompanist names which cause false matches)
                    word_mask = (
                        df['Artist(s)'].astype(str).str.lower().str.contains(word, na=False, regex=False) |
                        df['Venue'].astype(str).str.lower().str.contains(word, na=False, regex=False)
                    )
                mask = mask | word_mask
            
            return df[mask].sort_values(['Date', 'TimeParsed']).copy()
        except Exception as e:
            print(f"Error in search_by_text: {e}")
            return pd.DataFrame()

