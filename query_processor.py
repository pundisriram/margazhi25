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
        if self.gemini_chat:
            query_params = self.gemini_chat.extract_query_intent(user_query)
        else:
            # Fallback extraction when Gemini is unavailable
            query_params = self._fallback_extract_query_intent(user_query)
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
        
        # Handle ticketed status filter
        if query_params.get('ticketed'):
            filters['ticketed'] = query_params['ticketed']
        
        # Detect if this is a follow-up query (even if not explicitly marked)
        is_followup = query_params.get('is_followup', False)
        if previous_results is not None and len(previous_results) > 0:
            # Check if query seems to be filtering previous results
            query_lower = user_query.lower()
            followup_indicators = ['only', 'just', 'those', 'these', 'the ones', 'them', 'which', 'filter', 'show me']
            if any(indicator in query_lower for indicator in followup_indicators):
                is_followup = True
        
        # If we have previous results and this is a follow-up, filter previous results
        if previous_results is not None and is_followup:
            results_df = previous_results.copy()
            
            # Detect what type of filter is being applied
            filter_type = self._detect_followup_intent(user_query)
            
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
            
            # Handle ticketed status filtering on previous results
            if filters.get('ticketed') and len(results_df) > 0:
                if 'Ticketed' in results_df.columns:
                    if filters['ticketed'] == 'Free':
                        results_df = results_df[results_df['Ticketed'] == 'Free']
                    elif filters['ticketed'] == 'Ticketed':
                        results_df = results_df[results_df['Ticketed'] == 'Ticketed']
            elif filter_type == 'ticketed' and len(results_df) > 0 and 'Ticketed' in results_df.columns:
                # Auto-detect from query if not explicitly extracted
                query_lower = user_query.lower()
                if 'free' in query_lower:
                    results_df = results_df[results_df['Ticketed'] == 'Free']
                elif 'ticketed' in query_lower or 'paid' in query_lower:
                    results_df = results_df[results_df['Ticketed'] == 'Ticketed']
        else:
            # Execute search on full dataset
            # If query looks like an artist name, prioritize artist search
            query_lower = user_query.lower()
            words = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]
            original_words = user_query.split()
            has_capitalized = any(w and len(w) > 0 and w[0].isupper() for w in original_words)
            import re
            location_keywords = ['at', 'on', 'in', 'the', 'and', 'or', 'venue', 'hall', 'sabha', 'academy']
            has_location_keyword = any(
                re.search(r'\b' + re.escape(keyword) + r'\b', query_lower) 
                for keyword in location_keywords
            )
            looks_like_artist_name = (
                len(words) >= 2 and
                not has_location_keyword and
                ('-' in user_query or has_capitalized)
            )
            
            # If it looks like an artist name but no artist was extracted, try text search first
            if looks_like_artist_name and not filters.get('artist'):
                results_df = self.search_by_text(user_query)
                # Then apply other filters if any
                if len(results_df) > 0 and filters:
                    # Remove artist from filters since we already searched by artist
                    other_filters = {k: v for k, v in filters.items() if k != 'artist'}
                    if other_filters:
                        # Apply other filters to the artist results
                        for filter_key, filter_value in other_filters.items():
                            if filter_key == 'time_of_day':
                                time_results = self.data_loader.search_by_time_of_day(filter_value)
                                if len(time_results) > 0:
                                    results_df = results_df[results_df.index.isin(time_results.index)]
                                else:
                                    results_df = pd.DataFrame()
                            elif filter_key == 'ticketed' and 'Ticketed' in results_df.columns:
                                if filter_value == 'Free':
                                    results_df = results_df[results_df['Ticketed'] == 'Free']
                                elif filter_value == 'Ticketed':
                                    results_df = results_df[results_df['Ticketed'] == 'Ticketed']
            elif filters:
                results_df = self.data_loader.combine_filters(filters)
            else:
                # If no specific filters, try to search by any text in the query
                # This is a fallback for unclear queries
                results_df = self.search_by_text(user_query)
            
            # Apply ticketed filter if specified
            if filters.get('ticketed') and len(results_df) > 0:
                if 'Ticketed' in results_df.columns:
                    if filters['ticketed'] == 'Free':
                        results_df = results_df[results_df['Ticketed'] == 'Free']
                    elif filters['ticketed'] == 'Ticketed':
                        results_df = results_df[results_df['Ticketed'] == 'Ticketed']
        
        # Convert to list of dictionaries for easier handling
        concerts = results_df.to_dict('records') if len(results_df) > 0 else []
        
        # Generate natural language response
        if self.gemini_chat:
            response = self.gemini_chat.generate_natural_response({
                'count': len(concerts),
                'concerts': concerts[:20],  # Limit to 20 for response generation
                'query_params': query_params
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
        
        if self.gemini_chat:
            response = self.gemini_chat.process_query(user_query, context)
        else:
            # Fallback response when Gemini is unavailable
            response = f"I can help you search for concerts. The database contains {context['total_concerts']} concerts from {context['date_range']}. Try asking about specific artists, dates, or venues."
        
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
        Uses tiered matching strategy for artist names to prevent false positives.
        
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
        
        # Check if query seems to be about an artist
        import re
        is_artist_query = any(word in text_lower for word in [
            'singing', 'performing', 'concert by', 'by', 'when is', 'where is', 'who is',
            'concerts', "'s concerts", 'artist', 'vocalist'
        ])
        
        # Detect if query looks like an artist name (two or more words, possibly hyphenated)
        # This helps catch queries like "Ranjani gayatri" even without explicit keywords
        words = [w.strip() for w in text_lower.split() if len(w.strip()) > 2]
        # Check if original text has capitalized words (preserve original case)
        original_words = text.split()
        has_capitalized = any(w and len(w) > 0 and w[0].isupper() for w in original_words)
        
        # Check for location/venue keywords as whole words (not substrings)
        import re
        location_keywords = ['at', 'on', 'in', 'the', 'and', 'or', 'venue', 'hall', 'sabha', 'academy']
        has_location_keyword = any(
            re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) 
            for keyword in location_keywords
        )
        
        looks_like_artist_name = (
            len(words) >= 2 and  # At least 2 words
            not has_location_keyword and  # Not a location/venue query
            ('-' in text or has_capitalized)  # Has hyphen or capitalized words
        )
        
        # If it looks like an artist name OR has artist keywords, use tiered matching
        if is_artist_query or looks_like_artist_name:
            # Tier 1: Try exact phrase matching
            exact_results = self._match_artist_name_exact(df, text)
            if len(exact_results) > 0:
                return exact_results
            
            # Tier 2: Word boundary matching with AND logic (all words must match)
            word_results = self._match_artist_name_words(df, text)
            if len(word_results) > 0:
                return word_results
        
        # Fallback: general text search
        try:
            # For multi-word queries that could be artist names, always use AND logic in Artist column
            # This handles cases like "sanjay subramaniam" even if detection didn't trigger
            if len(words) > 1 and not has_location_keyword:
                # Multi-word query: use AND logic with word boundaries in Artist column only
                artist_mask = pd.Series([True] * len(df))
                for word in words:
                    # Use word boundary to prevent substring matches
                    pattern = r'\b' + re.escape(word) + r'\b'
                    word_mask = df['Artist(s)'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)
                    artist_mask = artist_mask & word_mask
                
                results = df[artist_mask].sort_values(['Date', 'TimeParsed']).copy()
                if len(results) > 0:
                    return results
            
            if is_artist_query or looks_like_artist_name:
                # For artist queries, ONLY search in Artist column with AND logic for multi-word
                if len(words) > 1:
                    # Multi-word: use AND logic with word boundaries (all words must appear)
                    artist_mask = pd.Series([True] * len(df))
                    for word in words:
                        pattern = r'\b' + re.escape(word) + r'\b'
                        word_mask = df['Artist(s)'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)
                        artist_mask = artist_mask & word_mask
                    
                    results = df[artist_mask].sort_values(['Date', 'TimeParsed']).copy()
                    return results
                elif len(words) == 1:
                    # Single word: use word boundary
                    pattern = r'\b' + re.escape(words[0]) + r'\b'
                    artist_mask = df['Artist(s)'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)
                    results = df[artist_mask].sort_values(['Date', 'TimeParsed']).copy()
                    return results
                # If words is empty (all filtered out), fall through to general search
            
            # General text search across multiple columns (but exclude Instruments/Details)
            mask = pd.Series([False] * len(df))
            for word in words:
                # For general queries, search Artist, Venue, but NOT Instruments/Details
                word_mask = (
                    df['Artist(s)'].astype(str).str.lower().str.contains(word, na=False, regex=False) |
                    df['Venue'].astype(str).str.lower().str.contains(word, na=False, regex=False)
                )
                mask = mask | word_mask
            
            return df[mask].sort_values(['Date', 'TimeParsed']).copy()
        except Exception as e:
            print(f"Error in search_by_text: {e}")
            return pd.DataFrame()
    
    def _normalize_name_separators(self, name: str) -> str:
        """Normalize name separators (hyphen, &, space) for matching."""
        import re
        # Replace hyphens and "&" with spaces, then normalize whitespace
        normalized = re.sub(r'[-&]', ' ', name)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized.lower()
    
    def _match_artist_name_exact(self, df: pd.DataFrame, query: str) -> pd.DataFrame:
        """Try to match artist name as exact phrase (highest priority)."""
        import re
        
        query_normalized = self._normalize_name_separators(query)
        
        # Handle spelling variations in query
        def normalize_with_variations(text):
            """Normalize text and handle common spelling variations."""
            normalized = self._normalize_name_separators(text)
            # Handle Gayatri/Gayathri variation
            normalized = re.sub(r'\bgayathri\b', 'gayatri', normalized)
            return normalized
        
        query_normalized_variations = normalize_with_variations(query)
        
        # Try exact phrase match (normalized, with spelling variations)
        def matches_exact(artist_str):
            if pd.isna(artist_str):
                return False
            artist_normalized = normalize_with_variations(str(artist_str))
            query_variations = normalize_with_variations(query_normalized)
            return query_variations in artist_normalized or artist_normalized in query_variations
        
        mask = df['Artist(s)'].apply(matches_exact)
        results = df[mask].sort_values(['Date', 'TimeParsed']).copy()
        return results
    
    def _match_artist_name_words(self, df: pd.DataFrame, query: str) -> pd.DataFrame:
        """Match artist name using word boundaries with AND logic (all words must match)."""
        import re
        
        # Normalize and split into words
        query_normalized = self._normalize_name_separators(query)
        words = [w.strip() for w in query_normalized.split() if len(w.strip()) > 2]
        
        if not words:
            return pd.DataFrame()
        
        # Handle common spelling variations
        def get_word_variations(word):
            """Get spelling variations of a word."""
            variations = [word]
            # Handle Gayatri/Gayathri variation
            if word == 'gayatri':
                variations.append('gayathri')
            elif word == 'gayathri':
                variations.append('gayatri')
            return variations
        
        # For each word, create word boundary regex patterns with variations
        masks = []
        for word in words:
            variations = get_word_variations(word)
            # Create pattern that matches any variation with word boundaries
            patterns = [r'\b' + re.escape(var) + r'\b' for var in variations]
            pattern = '|'.join(patterns)
            
            word_mask = df['Artist(s)'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)
            masks.append(word_mask)
        
        # Combine with AND logic (all words must match)
        if masks:
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask = combined_mask & mask
            
            results = df[combined_mask].sort_values(['Date', 'TimeParsed']).copy()
            return results
        
        return pd.DataFrame()
    
    def _fallback_extract_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Fallback query intent extraction when Gemini is unavailable.
        Uses simple keyword matching similar to GeminiChat._fallback_extraction.
        
        Args:
            user_query: Natural language query from user
        
        Returns:
            Dictionary with extracted query parameters
        """
        import re
        from datetime import datetime, timedelta
        from date_utils import parse_relative_date, parse_date_range
        
        query_lower = user_query.lower()
        result = {
            "date": None,
            "date_range": None,
            "artist": None,
            "venue": None,
            "location": None,
            "time_of_day": None,
            "ticketed": None,
            "intent": "search",
            "is_followup": False
        }
        
        # Check for follow-up indicators
        followup_keywords = ['filter', 'only', 'just', 'those', 'these', 'the ones', 'them', 'show me', 'which']
        if any(keyword in query_lower for keyword in followup_keywords):
            result["is_followup"] = True
        
        # Try to extract date range first
        date_range = parse_date_range(user_query)
        if date_range:
            start_date, end_date = date_range
            result["date_range"] = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        else:
            # Special case: "next week" should be kept as-is (not converted to date string)
            # so that search_by_date can handle it as a date range
            if 'next week' in query_lower:
                result["date"] = "next week"
            else:
                # Handle relative dates
                relative_date = parse_relative_date(user_query)
                if relative_date:
                    result["date"] = relative_date.strftime('%Y-%m-%d')
                elif 'today' in query_lower:
                    result["date"] = datetime.now().strftime('%Y-%m-%d')
                elif 'tomorrow' in query_lower:
                    result["date"] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                elif 'yesterday' in query_lower:
                    result["date"] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Extract ticketed status
        if any(word in query_lower for word in ['free', 'no ticket', 'no charge', 'complimentary']):
            result["ticketed"] = "Free"
        elif any(word in query_lower for word in ['ticketed', 'paid', 'ticket', 'tickets']):
            result["ticketed"] = "Ticketed"
        
        # Extract time of day (use word boundaries to avoid false matches)
        if re.search(r'\bmorning\b', query_lower) or re.search(r'\bam\b', query_lower) or re.search(r'\bearly\b', query_lower):
            result["time_of_day"] = "morning"
        elif re.search(r'\bafternoon\b', query_lower) or re.search(r'\bpm\b', query_lower):
            result["time_of_day"] = "afternoon"
        elif re.search(r'\bevening\b', query_lower):
            result["time_of_day"] = "evening"
        elif re.search(r'\bnight\b', query_lower) or re.search(r'\blate\b', query_lower):
            result["time_of_day"] = "night"
        
        # Extract intent
        if any(word in query_lower for word in ['route', 'plan', 'directions', 'travel']):
            result["intent"] = "route_planning"
        elif any(word in query_lower for word in ['help', 'what can', 'how can']):
            result["intent"] = "help"
        elif any(word in query_lower for word in ['info', 'information', 'tell me about']):
            result["intent"] = "info"
        
        return result
    
    def _detect_followup_intent(self, user_query: str) -> str:
        """
        Detect what type of filter is being applied in a follow-up query.
        
        Args:
            user_query: The follow-up query
        
        Returns:
            Type of filter: 'ticketed', 'time', 'venue', 'date', or 'unknown'
        """
        query_lower = user_query.lower()
        
        # Check for ticketed status
        if any(word in query_lower for word in ['free', 'ticketed', 'paid', 'ticket']):
            return 'ticketed'
        
        # Check for time of day
        if any(word in query_lower for word in ['morning', 'afternoon', 'evening', 'night', 'am', 'pm']):
            return 'time'
        
        # Check for venue
        if any(word in query_lower for word in ['at', 'venue', 'hall', 'sabha', 'academy']):
            return 'venue'
        
        # Check for date
        if any(word in query_lower for word in ['tomorrow', 'today', 'weekend', 'friday', 'monday', 'date']):
            return 'date'
        
        return 'unknown'

