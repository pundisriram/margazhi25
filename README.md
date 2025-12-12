# Margazhi Season Planner 🎵

An AI-powered chatbot interface for planning your Margazhi season concert schedule in Chennai, India. Built with Streamlit and Google Gemini AI.

## Features

- **Natural Language Search**: Ask questions in plain English about concerts
- **Smart Query Understanding**: Uses Gemini AI to understand your intent
- **Route Planning**: Plan optimal routes between multiple concert venues
- **Interactive Maps**: Visualize venue locations on an interactive map
- **Time Conflict Detection**: Get warnings about overlapping concerts
- **Flexible Filtering**: Search by date, artist, venue, location, or time of day

## Setup

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Google Maps API key (optional, for geocoding and route planning)

### Installation

1. Clone or navigate to the project directory:
```bash
cd margazhi25
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Getting API Keys

**Gemini API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

**Google Maps API Key (Optional):**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Geocoding API
   - Directions API
   - Maps JavaScript API (if needed)
4. Create credentials (API key)
5. Copy the key to your `.env` file

Note: The app will work without Google Maps API key, but geocoding and route planning features will be limited.

## Usage

### Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

### Example Queries

Try asking the chatbot:

- "Show me concerts on December 15"
- "Find concerts by T.M. Krishna"
- "What's happening at Music Academy on Dec 20?"
- "Show me concerts near Mylapore"
- "What concerts can I attend on Dec 18 evening?"
- "Plan a route for these concerts"

### Using Route Planning

1. Search for concerts using natural language
2. Select concerts you want to attend using the checkboxes
3. Click "Plan Route for Selected Concerts"
4. View the optimized route with travel times and directions

## Project Structure

```
margazhi25/
├── app.py                 # Main Streamlit application
├── data_loader.py         # Data loading and search functions
├── geocoding.py          # Venue geocoding service
├── gemini_chat.py         # Gemini AI integration
├── query_processor.py     # Query intent extraction
├── route_planner.py      # Route planning logic
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not in git)
├── .gitignore           # Git ignore file
├── combined_schedules.csv # Concert schedule data
└── schedules/           # Original schedule CSV files
```

## Data

The application uses `combined_schedules.csv` which contains concert schedules from multiple venues. The CSV has the following columns:

- `Date`: Concert date
- `Time`: Concert time
- `Artist(s)`: Artist name(s)
- `Instruments/Details`: Performance details
- `Venue`: Venue name
- `Source`: Source organization

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure you've created a `.env` file with your API key
- Check that the key is correct and has no extra spaces

### "No concerts found"
- Try different search terms
- Check that `combined_schedules.csv` exists and has data
- Use more specific queries (e.g., include date or venue name)

### Maps not showing
- Check that you have a valid Google Maps API key
- Ensure the Geocoding API is enabled in Google Cloud Console
- Check browser console for JavaScript errors

### Route planning not working
- Ensure Google Maps API key is set
- Check that Directions API is enabled
- Verify that venues can be geocoded (check geocoding_cache.json)

## Development

### Adding New Features

The codebase is modular:
- `data_loader.py`: Add new search methods here
- `gemini_chat.py`: Customize AI behavior and prompts
- `route_planner.py`: Enhance route optimization algorithms
- `app.py`: Modify UI and user experience

### Testing

Test various query types:
- Date-based queries
- Artist searches
- Venue searches
- Location-based searches
- Route planning with multiple venues

## Deployment

To share this app with others, see [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Quickest option:** Deploy to [Streamlit Cloud](https://streamlit.io/cloud) for free:
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Add API keys as secrets
4. Share the link!

See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for a 5-minute deployment guide.

## License

This project is for personal/educational use.

## Acknowledgments

- Concert schedule data from various Margazhi season organizers
- Built with Streamlit, Google Gemini AI, and Google Maps APIs

