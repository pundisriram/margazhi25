"""
Main Streamlit application for Margazhi season concert schedule planning chatbot.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Page configuration - must be first
st.set_page_config(
    page_title="Margazhi Season Planner",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our modules
try:
    from data_loader import ConcertDataLoader
    from geocoding import VenueGeocoder
    from gemini_chat import GeminiChat
    from query_processor import QueryProcessor
    from route_planner import RoutePlanner
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'data_loader' not in st.session_state:
    st.session_state.data_loader = None
if 'geocoder' not in st.session_state:
    st.session_state.geocoder = None
if 'gemini_chat' not in st.session_state:
    st.session_state.gemini_chat = None
if 'query_processor' not in st.session_state:
    st.session_state.query_processor = None
if 'route_planner' not in st.session_state:
    st.session_state.route_planner = None
if 'previous_results' not in st.session_state:
    st.session_state.previous_results = None
if 'previous_filters' not in st.session_state:
    st.session_state.previous_filters = {}


def initialize_components():
    """Initialize all components."""
    try:
        data_loader = ConcertDataLoader("combined_schedules.csv")
        geocoder = VenueGeocoder()
        
        try:
            gemini_chat = GeminiChat()
        except Exception as e:
            print(f"Warning: Error initializing Gemini: {e}")
            gemini_chat = None
        
        query_processor = QueryProcessor(data_loader, gemini_chat) if gemini_chat else None
        route_planner = RoutePlanner(geocoder, data_loader)
        
        return data_loader, geocoder, gemini_chat, query_processor, route_planner
    except Exception as e:
        print(f"Error initializing components: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None


def display_concert_results(results_df: pd.DataFrame, concerts: list):
    """Display concert results in a formatted table."""
    if len(results_df) == 0:
        st.info("No concerts found matching your query.")
        return
    
    # Display summary
    st.success(f"Found {len(results_df)} concert(s)")
    
    # Create a formatted display
    try:
        # Include Instruments/Details column
        columns_to_show = ['Date', 'Time', 'Artist(s)', 'Instruments/Details', 'Venue', 'Source']
        # Check which columns exist
        available_columns = [col for col in columns_to_show if col in results_df.columns]
        display_df = results_df[available_columns].copy()
        display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
    except KeyError as e:
        st.error(f"Error displaying results: Missing column {e}")
        return
    
    # Display table
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def create_venue_map(concerts: list, geocoder: VenueGeocoder):
    """Create a map showing venue locations."""
    if not concerts or not geocoder:
        return None
    
    # Get unique venues
    venues = {}
    for concert in concerts:
        venue = concert.get('Venue', '')
        if venue and venue not in venues:
            try:
                coords = geocoder.geocode(venue)
                if coords:
                    venues[venue] = coords
            except Exception as e:
                print(f"Error geocoding {venue}: {e}")
                continue
    
    if not venues:
        return None
    
    # Create map centered on Chennai
    m = folium.Map(location=[13.0827, 80.2707], zoom_start=12)
    
    # Add markers for each venue
    for venue, coords in venues.items():
        # Find concerts at this venue
        venue_concerts = [c for c in concerts if c.get('Venue') == venue]
        
        # Create popup text
        popup_text = f"<b>{venue}</b><br>"
        for concert in venue_concerts[:5]:  # Show first 5 concerts
            popup_text += f"{concert.get('Date', '')} {concert.get('Time', '')} - {concert.get('Artist(s)', '')[:30]}<br>"
        if len(venue_concerts) > 5:
            popup_text += f"... and {len(venue_concerts) - 5} more"
        
        folium.Marker(
            coords,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=venue,
            icon=folium.Icon(color='blue', icon='music', prefix='fa')
        ).add_to(m)
    
    return m


def main():
    """Main application function."""
    # Title and header
    st.title("🎵 Margazhi Season Planner")
    st.markdown("**Your AI-powered assistant for planning your concert schedule**")
    
    # Sidebar with info
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This chatbot helps you:
        - Search concerts by date, artist, or venue
        - Find concerts in specific areas
        - Get personalized recommendations
        
        **Example queries:**
        - "Show me concerts on December 15"
        - "Find concerts by T.M. Krishna"
        - "What's at Music Academy on Dec 20?"
        """)
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.previous_results = None
            st.session_state.previous_filters = {}
            st.rerun()
    
    # Initialize components
    if st.session_state.data_loader is None:
        init_placeholder = st.empty()
        with init_placeholder.container():
            st.info("🔄 Initializing application...")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            status_text.text("Loading concert data...")
            progress_bar.progress(20)
            
            data_loader, geocoder, gemini_chat, query_processor, route_planner = initialize_components()
            progress_bar.progress(60)
            
            if data_loader is None:
                init_placeholder.error("Failed to load data. Please check that combined_schedules.csv exists.")
                st.stop()
            
            status_text.text(f"✓ Loaded {len(data_loader.df)} concerts")
            progress_bar.progress(80)
            
            st.session_state.data_loader = data_loader
            st.session_state.geocoder = geocoder
            st.session_state.gemini_chat = gemini_chat
            st.session_state.query_processor = query_processor
            st.session_state.route_planner = route_planner
            
            progress_bar.progress(100)
            status_text.text("✓ Initialization complete!")
            
            # Clear the initialization message
            init_placeholder.empty()
            
        except Exception as e:
            init_placeholder.error(f"Error during initialization: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
            st.stop()
    
    # Check if initialization was successful
    if st.session_state.data_loader is None:
        st.error("Failed to initialize. Please check your data file and API keys.")
        st.info("Make sure combined_schedules.csv exists in the project directory.")
        return
    
    if st.session_state.gemini_chat is None:
        st.warning("⚠️ Gemini AI is not available. Please set GEMINI_API_KEY in your .env file for full functionality.")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about concerts..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.query_processor:
                    # Process with AI (pass previous results for conversational context)
                    try:
                        result = st.session_state.query_processor.process(
                            prompt, 
                            previous_results=st.session_state.previous_results
                        )
                        
                        # Display AI response
                        st.markdown(result.get('response', 'I found some concerts for you.'))
                        
                        # Debug: show extracted parameters (can be removed later)
                        with st.expander("🔍 Debug: Extracted Query Parameters", expanded=False):
                            st.json(result.get('query_params', {}))
                            if st.session_state.previous_results is not None:
                                st.info(f"Previous results: {len(st.session_state.previous_results)} concerts")
                        
                        # Display results if any
                        if result.get('count', 0) > 0:
                            concerts = result.get('concerts', [])
                            results_df = result.get('results', pd.DataFrame())
                            
                            # Store results for next query (conversational context)
                            st.session_state.previous_results = results_df.copy()
                            st.session_state.previous_filters = result.get('query_params', {})
                            
                            # Display results table
                            display_concert_results(results_df, concerts)
                        else:
                            # If no results, suggest trying a text search
                            st.info("💡 Tip: Try searching with specific terms like 'December 15', an artist name, or a venue name.")
                            # Clear previous results if no matches
                            st.session_state.previous_results = None
                        
                        # Add assistant response to history
                        response_text = result.get('response', '')
                        if result.get('count', 0) > 0:
                            response_text += f"\n\nFound {result.get('count', 0)} concert(s)."
                        
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    except Exception as e:
                        st.error(f"Error processing query: {e}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
                        # Fallback to simple search
                        if st.session_state.data_loader:
                            results_df = st.session_state.query_processor.search_by_text(prompt)
                            if len(results_df) > 0:
                                st.success(f"Found {len(results_df)} concert(s) using text search")
                                display_df = results_df[['Date', 'Time', 'Artist(s)', 'Venue', 'Source']].head(20)
                                st.dataframe(display_df, use_container_width=True)
                else:
                    # Fallback: simple text search using data loader
                    if st.session_state.data_loader:
                        # Try searching in different fields
                        artist_results = st.session_state.data_loader.search_by_artist(prompt)
                        venue_results = st.session_state.data_loader.search_by_venue(prompt)
                        location_results = st.session_state.data_loader.search_by_location(prompt)
                        
                        # Combine results
                        all_results = pd.concat([artist_results, venue_results, location_results]).drop_duplicates()
                        results_df = all_results.sort_values(['Date', 'TimeParsed'])
                    else:
                        results_df = pd.DataFrame()
                    
                    if len(results_df) > 0:
                        st.success(f"Found {len(results_df)} concert(s)")
                        display_df = results_df[['Date', 'Time', 'Artist(s)', 'Venue', 'Source']].head(20)
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.info("No concerts found. Please try a different search term or ensure Gemini API is configured for better search.")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Found {len(results_df)} concert(s) matching your query."
                    })
    
    # Display initial greeting if no messages
    if len(st.session_state.messages) == 0:
        with st.chat_message("assistant"):
            greeting = """Hello! I'm your Margazhi season planning assistant. 🎵

I can help you:
- Search for concerts by date, artist, venue, or location
- Find concerts in specific areas of Chennai
- Get recommendations based on your preferences

Try asking me something like:
- "Show me concerts on December 15"
- "Find concerts by T.M. Krishna"
- "What's happening at Music Academy?"

What would you like to know?"""
            st.markdown(greeting)
            st.session_state.messages.append({"role": "assistant", "content": greeting})


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Fatal error: {e}")
        import traceback
        st.code(traceback.format_exc())

