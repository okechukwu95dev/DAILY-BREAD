#!/usr/bin/env python3
"""
Full Database Population Script
Populates the entire database with all competitions, teams, and relationships
This is a comprehensive one-time setup script
"""

import sqlite3
import requests
import json
import time
import os
from datetime import datetime

def resolve_db_path():
    workspace = os.getenv("GITHUB_WORKSPACE")
    if workspace:
        return os.path.join(workspace, "new_project", "db", "soccer_data_colab.db")
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "new_project", "db", "soccer_data_colab.db"))

# 365Scores API Configuration
LANG_ID = 9
TZ_NAME = "UTC"
USER_COUNTRY_ID = 331
APP_ID = 5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Origin': 'https://www.365scores.com',
    'Referer': 'https://www.365scores.com/',
    'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'Sec-Ch-Ua-Mobile': '?1',
    'Sec-Ch-Ua-Platform': '"Android"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site'
}

DB_PATH = resolve_db_path()

def make_api_request(url, description=""):
    """Make API request with error handling"""
    try:
        print(f"  🌐 {description}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"    ❌ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    ❌ Error: {str(e)}")
        return None

def fetch_countries_from_api():
    """Fetch all countries from 365Scores API"""
    print("🌍 Fetching countries from API...")
    
    # Get countries from a competition search or standings endpoint
    url = f"https://webws.365scores.com/web/competitions/?appTypeId={APP_ID}&langId={LANG_ID}&timezoneName={TZ_NAME}&userCountryId={USER_COUNTRY_ID}"
    data = make_api_request(url, "Countries from competitions")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    countries_added = 0
    if data and 'countries' in data:
        for country in data['countries']:
            cursor.execute('''
                INSERT OR REPLACE INTO countries 
                (id, name, name_for_url, image_version) 
                VALUES (?, ?, ?, ?)
            ''', (country.get('id'), country.get('name'), country.get('nameForURL'), country.get('imageVersion', 1)))
            countries_added += 1
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Added {countries_added} countries")
    return countries_added

def fetch_all_competitions_from_api():
    """Fetch ALL competitions from 365Scores API"""
    print("🏆 Fetching all competitions from API...")
    
    url = f"https://webws.365scores.com/web/competitions/?appTypeId={APP_ID}&langId={LANG_ID}&timezoneName={TZ_NAME}&userCountryId={USER_COUNTRY_ID}"
    data = make_api_request(url, "All competitions")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    competitions_added = 0
    if data and 'competitions' in data:
        for comp in data['competitions']:
            cursor.execute('''
                INSERT OR REPLACE INTO competitions 
                (id, country_id, sport_id, name, long_name, name_for_url, 
                 has_standings, has_brackets, has_stats, popularity_rank, 
                 image_version, is_international) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comp.get('id'), 
                comp.get('countryId'), 
                comp.get('sportId', 1),  # Default to soccer
                comp.get('name'), 
                comp.get('longName'),
                comp.get('nameForURL'),
                comp.get('hasStandings', False),
                comp.get('hasBrackets', False), 
                comp.get('hasStats', False),
                comp.get('popularityRank', 999),
                comp.get('imageVersion', 1),
                comp.get('isInternational', False)
            ))
            competitions_added += 1
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Added {competitions_added} competitions")
    return competitions_added

def fetch_teams_for_competition(comp_id, comp_name):
    """Fetch all teams for a specific competition"""
    print(f"� Fetching teams for {comp_name}...")
    
    # Try standings first
    url = f"https://webws.365scores.com/web/standings/?competitions={comp_id}&live=false&appTypeId={APP_ID}&langId={LANG_ID}&timezoneName={TZ_NAME}&userCountryId={USER_COUNTRY_ID}"
    data = make_api_request(url, f"Teams for {comp_name}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    teams_added = 0
    
    if data and 'standings' in data:
        for standing_group in data['standings']:
            if 'competitors' in standing_group:
                for team_data in standing_group['competitors']:
                    team_id = team_data.get('id')
                    if team_id:
                        cursor.execute('''
                            INSERT OR REPLACE INTO teams 
                            (id, name, name_for_url, country_id, main_competition_id, image_version, is_national)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            team_id,
                            team_data.get('name'),
                            team_data.get('nameForURL'),
                            team_data.get('countryId'),
                            comp_id,
                            team_data.get('imageVersion', 1),
                            team_data.get('isNational', False)
                        ))
                        
                        # Link team to competition
                        cursor.execute('''
                            INSERT OR REPLACE INTO team_competitions 
                            (team_id, competition_id, is_active)
                            VALUES (?, ?, 1)
                        ''', (team_id, comp_id))
                        
                        teams_added += 1
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Added {teams_added} teams for {comp_name}")
    return teams_added

def populate_from_api():
    """Populate entire database from 365Scores API"""
    
    print("🌐 Populating ENTIRE database from 365Scores API...")
    
    total_countries = 0
    total_competitions = 0
    total_teams = 0
    
    # Step 1: Fetch countries
    total_countries = fetch_countries_from_api()
    time.sleep(2)
    
    # Step 2: Fetch all competitions
    total_competitions = fetch_all_competitions_from_api()
    time.sleep(2)
    
    # Step 3: For each competition with standings, fetch teams
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get competitions that likely have standings
    cursor.execute('''
        SELECT id, name, has_standings, popularity_rank 
        FROM competitions 
        WHERE has_standings = 1 
        ORDER BY popularity_rank ASC NULLS LAST
        LIMIT 50
    ''')
    
    competitions_to_process = cursor.fetchall()
    conn.close()
    
    print(f"📊 Processing {len(competitions_to_process)} competitions for teams...")
    
    for comp_id, comp_name, has_standings, popularity in competitions_to_process:
        teams_count = fetch_teams_for_competition(comp_id, comp_name)
        total_teams += teams_count
        time.sleep(1.5)  # Rate limiting
    
    print(f"\n🎉 API Population complete!")
    print(f"  🌍 Countries: {total_countries}")
    print(f"  🏆 Competitions: {total_competitions}")  
    print(f"  👥 Teams: {total_teams}")
    
    return True

def main():
    """Main population function"""
    
    print(f"🚀 FULL DATABASE POPULATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*70)
    
    if not os.path.exists(DB_PATH):
        print("❌ Database not found! Please run create_schema.py first.")
        return
    
    # Populate entire database from 365Scores API
    print("🌐 Starting comprehensive database population from API...")
    populate_from_api()
    
    # Generate final summary
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM competitions")
    comp_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM teams") 
    team_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM team_competitions")
    tc_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM countries")
    country_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n📈 FINAL SUMMARY:")
    print(f"  🌍 Countries: {country_count}")
    print(f"  🏆 Competitions: {comp_count}")
    print(f"  👥 Teams: {team_count}")  
    print(f"  🔗 Team-Competition links: {tc_count}")
    print("\n🎉 Database is ready for daily updates!")

if __name__ == "__main__":
    main()
