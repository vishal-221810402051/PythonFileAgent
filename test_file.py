import googlemaps
from datetime import datetime, timedelta
import time
import pandas as pd
import matplotlib.pyplot as plt
import os
import folium
import folium.plugins as plugins
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import numpy as np
import warnings
import traceback

# Suppress warnings
warnings.filterwarnings('ignore')

# Initialize Google Maps client
API_KEY = 'AIzaSyABycn2HPoNr5as5TnTr39sd0TvIhi8HQE'
gmaps = googlemaps.Client(key=API_KEY)

# Location coordinates for mapping
LOCATION_COORDS = {
    "Patna Junction, Patna": [25.6155, 85.1354],
    "Bailey Road, Patna": [25.6129, 85.1588],
    "Ashok Rajpath, Patna": [25.6093, 85.1239],
    "Gandhi Maidan, Patna": [25.6115, 85.1444]
}

def get_traffic_data(location):
    """Fetch traffic data with enhanced error handling"""
    try:
        now = datetime.now()
        result = gmaps.directions(
            origin=location,
            destination=location,
            mode="driving",
            departure_time=now,
            traffic_model="best_guess"
        )
        
        if result and 'legs' in result[0] and result[0]['legs']:
            leg = result[0]['legs'][0]
            # Ensure all required fields exist
            duration = leg.get('duration', {}).get('value', 0)
            traffic_duration = leg.get('duration_in_traffic', {}).get('value', duration)
            distance = leg.get('distance', {}).get('value', 1000)  # Default 1km
            
            return {
                'timestamp': now,
                'location': location,
                'normal_duration_sec': duration,
                'traffic_duration_sec': traffic_duration,
                'delay_sec': max(0, traffic_duration - duration),  # Prevent negative
                'distance_m': distance
            }
        return {
            'timestamp': now,
            'location': location,
            'normal_duration_sec': 0,
            'traffic_duration_sec': 0,
            'delay_sec': 0,
            'distance_m': 1000
        }
    except Exception as e:
        print(f"API Error for {location}: {str(e)}")
        return {
            'timestamp': datetime.now(),
            'location': location,
            'normal_duration_sec': 0,
            'traffic_duration_sec': 0,
            'delay_sec': 0,
            'distance_m': 1000
        }

def collect_data(locations, interval=300, duration=1800):
    """Collect data with progress tracking"""
    data = []
    start_time = time.time()
    end_time = start_time + duration
    cycle = 1
    total_cycles = max(1, duration // interval)
    
    print(f"\n{'='*50}")
    print(f"🚦 Starting Traffic Data Collection for Patna City")
    print(f"⏱ Duration: {duration//60} minutes | 🔄 Interval: {interval//60} minutes")
    print(f"📍 Locations: {', '.join([loc.split(',')[0] for loc in locations])}")
    print(f"{'='*50}\n")
    
    while time.time() < end_time and cycle <= total_cycles:
        print(f"\n🔁 Collection Cycle #{cycle}/{total_cycles}")
        print("-"*40)
        cycle_data = []
        for location in locations:
            traffic_data = get_traffic_data(location)
            if traffic_data:
                delay_min = traffic_data['delay_sec'] / 60
                data.append(traffic_data)
                cycle_data.append((location, delay_min))
                print(f"  - {location.split(',')[0]}: {delay_min:.1f} min delay")
        
        # Print summary for current cycle
        if cycle_data:
            avg_delay = sum(d[1] for d in cycle_data) / len(cycle_data)
            max_delay = max(d[1] for d in cycle_data)
            max_loc = [d[0].split(',')[0] for d in cycle_data if d[1] == max_delay][0]
            print(f"\n📊 Cycle Summary: Avg delay = {avg_delay:.1f} min | Max delay = {max_delay:.1f} min at {max_loc}")
        
        cycle += 1
        if time.time() + interval < end_time:
            time.sleep(interval)
    
    print("\n✅ Data collection complete!")
    return pd.DataFrame(data)

def analyze_and_visualize(df):
    
    """Generate enhanced visualizations with detailed map"""
    if df.empty:
        print("⚠️ No data to visualize")
        return None
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"patna_traffic_report_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Data Cleaning
    # Remove rows with NaN values in critical columns
    df = df.dropna(subset=['delay_sec', 'distance_m'])
    
    # Handle zero distance cases to avoid division errors
    df['distance_m'] = df['distance_m'].replace(0, 1)
    
    # 2. Convert delay to minutes and add descriptive columns
    df['delay_min'] = df['delay_sec'] / 60
    
    # Handle negative delays (shouldn't occur but safe-guard)
    df['delay_min'] = df['delay_min'].clip(lower=0)
    
    # Create delay categories
    df['delay_category'] = pd.cut(
        df['delay_min'],
        bins=[-1, 0, 2, 5, 10, 30, 1000],
        labels=[
            "No Delay (0 min)",
            "Minor Delay (<2 min)", 
            "Moderate Delay (2-5 min)",
            "Significant Delay (5-10 min)",
            "Severe Delay (10-30 min)",
            "Extreme Delay (>30 min)"
        ]
    )
    
    # Calculate speed
    df['speed_kmh'] = (df['distance_m'] / 1000) / (df['traffic_duration_sec'] / 3600)
    df['speed_kmh'] = df['speed_kmh'].clip(upper=120)  # Cap at highway speed
    
    df['distance_km'] = df['distance_m'] / 1000
    df['short_location'] = df['location'].apply(lambda x: x.split(',')[0])
    
    # 3. Enhanced Interactive Traffic Map
    map_center = [25.5941, 85.1376]
    m = folium.Map(
        location=map_center, 
        zoom_start=13, 
        tiles='cartodbpositron',
        control_scale=True
    )
    
    # Color coding based on delay severity
    delay_colors = {
        "No Delay (0 min)": "#2c7bb6",
        "Minor Delay (<2 min)": "#abd9e9",
        "Moderate Delay (2-5 min)": "#ffffbf",
        "Significant Delay (5-10 min)": "#fdae61",
        "Severe Delay (10-30 min)": "#d7191c",
        "Extreme Delay (>30 min)": "#800026"
    }
    
    # Add markers with detailed popups
    for _, row in df.iterrows():
        coords = LOCATION_COORDS.get(row['location'])
        if not coords:
            continue
            
        delay_min = row['delay_min']
        category = row['delay_category']
        
        # Handle NaN categories gracefully
        if pd.isna(category):
            color = "#888888"
            category = "Unknown Delay"
        else:
            color = delay_colors.get(category, "#888888")
        
        # Create custom popup content
        popup_html = f"""
        <div style="font-family: Arial; min-width: 300px">
            <h3 style="margin:0; border-bottom: 2px solid #333; padding-bottom:5px; color:{color}">
                {row['short_location']}
            </h3>
            <table style="width:100%; border-collapse: collapse; margin-top:10px">
                <tr>
                    <td style="padding:4px; font-weight:bold">Delay Status</td>
                    <td style="padding:4px; text-align:right; font-weight:bold; color:{color}">
                        {category}
                    </td>
                </tr>
                <tr>
                    <td style="padding:4px; font-weight:bold">Actual Delay</td>
                    <td style="padding:4px; text-align:right; font-weight:bold">
                        {delay_min:.1f} min
                    </td>
                </tr>
                <tr style="background-color:#f9f9f9">
                    <td style="padding:4px">Distance</td>
                    <td style="padding:4px; text-align:right">
                        {row['distance_km']:.1f} km
                    </td>
                </tr>
                <tr>
                    <td style="padding:4px">Avg Speed</td>
                    <td style="padding:4px; text-align:right">
                        {row['speed_kmh']:.0f} km/h
                    </td>
                </tr>
                <tr style="background-color:#f9f9f9">
                    <td style="padding:4px">Time</td>
                    <td style="padding:4px; text-align:right">
                        {row['timestamp'].strftime('%H:%M:%S')}
                    </td>
                </tr>
                <tr>
                    <td style="padding:4px">Normal Duration</td>
                    <td style="padding:4px; text-align:right">
                        {row['normal_duration_sec']//60} min
                    </td>
                </tr>
                <tr style="background-color:#f9f9f9">
                    <td style="padding:4px">Actual Duration</td>
                    <td style="padding:4px; text-align:right">
                        {row['traffic_duration_sec']//60} min
                    </td>
                </tr>
            </table>
        </div>
        """
        
        # Add marker with custom icon
        folium.CircleMarker(
            location=coords,
            radius=8 + min(30, delay_min * 1.5),  # Cap max size
            color=color,
            fill=True,
            fill_opacity=0.8,
            weight=1,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{row['short_location']}: {delay_min:.1f} min delay"
        ).add_to(m)
    
    # Add traffic layer
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.de/{z}/{x}/{y}.png',
        attr='OpenStreetMap DE',
        name='Detailed Streets',
        overlay=False
    ).add_to(m)
    
    # Create custom legend
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 50px; 
        left: 50px; 
        width: 250px; 
        height: auto; 
        background: white;
        border: 2px solid grey;
        z-index: 9999;
        padding: 15px;
        font-size: 14px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
        font-family: Arial;
    ">
        <h3 style="margin-top:0; margin-bottom:10px; border-bottom:1px solid #ccc; padding-bottom:5px">
            <i class="fa fa-map-marker"></i> Delay Legend
        </h3>
        <div style="display:flex; align-items:center; margin:8px 0">
            <div style="background:#2c7bb6; width:22px; height:22px; border-radius:50%; margin-right:12px"></div>
            <span>No Delay (0 min)</span>
        </div>
        <div style="display:flex; align-items:center; margin:8px 0">
            <div style="background:#abd9e9; width:22px; height:22px; border-radius:50%; margin-right:12px"></div>
            <span>Minor Delay (<2 min)</span>
        </div>
        <div style="display:flex; align-items:center; margin:8px 0">
            <div style="background:#ffffbf; width:22px; height:22px; border-radius:50%; margin-right:12px"></div>
            <span>Moderate Delay (2-5 min)</span>
        </div>
        <div style="display:flex; align-items:center; margin:8px 0">
            <div style="background:#fdae61; width:22px; height:22px; border-radius:50%; margin-right:12px"></div>
            <span>Significant Delay (5-10 min)</span>
        </div>
        <div style="display:flex; align-items:center; margin:8px 0">
            <div style="background:#d7191c; width:22px; height:22px; border-radius:50%; margin-right:12px"></div>
            <span>Severe Delay (10-30 min)</span>
        </div>
        <div style="display:flex; align-items:center; margin:8px 0">
            <div style="background:#800026; width:22px; height:22px; border-radius:50%; margin-right:12px"></div>
            <span>Extreme Delay (>30 min)</span>
        </div>
        <div style="margin-top:15px; font-size:12px; color:#666">
            <i>Data collected: {}</i>
        </div>
    </div>
    """.format(datetime.now().strftime("%d %b %Y %H:%M"))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add title
    title_html = """
    <h3 align="center" style="font-size:18pt; margin:10px; font-family:Arial; color:#2c3e50">
        <i class="fa fa-car"></i> Patna City Traffic Analysis
    </h3>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    map_path = os.path.join(output_dir, 'patna_traffic_map.html')
    m.save(map_path)
    print(f"🗺️ Saved enhanced interactive map: {map_path}")
    
    # [Keep the rest of your visualization code as before]
    # ... (time series plot, boxplot, etc.)
    
    return output_dir

def build_prediction_model(df):
    """Create traffic prediction model"""
    if df.empty or len(df) < 10:
        print("⚠️ Insufficient data for modeling")
        return None
    
    try:
        # Feature engineering
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_peak'] = df['hour'].apply(lambda x: 1 if (7 <= x <= 10) or (17 <= x <= 20) else 0)
        
        # Prepare data
        X = df[['hour', 'day_of_week', 'is_peak', 'distance_m']]
        y = df['delay_sec']
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
        model.fit(X_train, y_train)
        
        # Evaluate
        score = model.score(X_test, y_test)
        print(f"\n🔮 Model Performance:")
        print(f"- R² Score: {score:.2f}")
        print(f"- Features: {list(X.columns)}")
        
        return model
    except Exception as e:
        print(f"❌ Modeling failed: {str(e)}")
        return None

def generate_optimization_recommendations(df, model):
    """Generate actionable traffic optimization suggestions"""
    if model is None:
        return []
    
    recommendations = []
    peak_hours = [7, 8, 9, 17, 18, 19]
    
    for location in df['location'].unique():
        loc_df = df[df['location'] == location]
        if loc_df.empty:
            continue
            
        # Predict for peak hours
        peak_delays = []
        for hour in peak_hours:
            sample = pd.DataFrame([{
                'hour': hour,
                'day_of_week': 4,  # Friday
                'is_peak': 1,
                'distance_m': loc_df['distance_m'].median()
            }])
            prediction = model.predict(sample)[0]
            peak_delays.append(max(0, prediction))  # Ensure non-negative
        
        if not peak_delays:
            continue
            
        avg_delay = np.mean(peak_delays) / 60  # in minutes
        loc_name = location.split(',')[0]
        
        # Generate recommendations
        if avg_delay > 5:
            rec = {
                'location': loc_name,
                'severity': 'High',
                'problem': f"Average peak delay: {avg_delay:.1f} min",
                'recommendation': (
                    "1. Increase green light duration by 30-40% during 7-10 AM & 5-8 PM\n"
                    "2. Deploy traffic police for manual flow control\n"
                    "3. Implement dedicated turning lanes"
                )
            }
        elif avg_delay > 2:
            rec = {
                'location': loc_name,
                'severity': 'Medium',
                'problem': f"Average peak delay: {avg_delay:.1f} min",
                'recommendation': (
                    "1. Optimize traffic light cycles using adaptive timing\n"
                    "2. Install traffic monitoring cameras\n"
                    "3. Add pedestrian crossing signals"
                )
            }
        else:
            rec = {
                'location': loc_name,
                'severity': 'Low',
                'problem': f"Average peak delay: {avg_delay:.1f} min",
                'recommendation': "Maintain current operations with periodic reviews"
            }
            
        recommendations.append(rec)
    
    return recommendations

def main():
    """Main execution function"""
    try:
        # Configure parameters
        locations = list(LOCATION_COORDS.keys())
        collection_minutes = 0.5  # 30 seconds for testing
        interval_minutes = 0.1    # 6 seconds between checks
        
        # Run data collection
        traffic_df = collect_data(
            locations,
            interval=interval_minutes * 60,
            duration=collection_minutes * 60
        )
        
        if traffic_df.empty:
            print("❌ No data collected. Exiting.")
            return
            
        # Generate visualizations and save data
        report_dir = analyze_and_visualize(traffic_df)
        
        # Build prediction model
        model = build_prediction_model(traffic_df)
        
        # Generate recommendations
        recommendations = generate_optimization_recommendations(traffic_df, model)
        
        # Print recommendations
        if recommendations:
            print("\n🚀 Traffic Optimization Recommendations for Patna:")
            print("="*70)
            for rec in recommendations:
                print(f"\n📍 Location: {rec['location']} | Severity: {rec['severity']}")
                print(f"   🔍 Problem: {rec['problem']}")
                print(f"   💡 Recommendations:\n{rec['recommendation']}")
                print("-"*70)
        
        print(f"\n📁 Full report generated in: {os.path.abspath(report_dir)}")
        print("✅ Script completed successfully!")
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()