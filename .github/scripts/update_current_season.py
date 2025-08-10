#!/usr/bin/env python3
"""
Current Season Database Update
Updates team-competition relationships for current seasons only
This is the main daily update script
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
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print(f"    ❌ Invalid JSON response")
        return None

def get_active_competitions():
    """Get list of competitions that should be updated daily"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First check if we have any competitions in the database
    cursor.execute('SELECT COUNT(*) FROM competitions')
    comp_count = cursor.fetchone()[0]
    
    if comp_count == 0:
        print("📊 No competitions found in database, fetching from API...")
        # If empty database, fetch major competitions from API
        major_competitions = [
            7,    # Premier League
            8,    # La Liga
            13,   # Serie A
            9,    # Bundesliga
            11,   # Ligue 1
            52,   # Champions League
            102,  # Europa League
        ]
        
        competitions = []
        for comp_id in major_competitions:
            # Try to get standings to verify the competition is active
            url = f"https://webws.365scores.com/web/standings/?competitions={comp_id}&live=false&appTypeId={APP_ID}&langId={LANG_ID}&timezoneName={TZ_NAME}&userCountryId={USER_COUNTRY_ID}"
            data = make_api_request(url, f"Checking competition {comp_id}")
            
            if data and 'competitions' in data and len(data['competitions']) > 0:
                comp_data = data['competitions'][0]
                competitions.append((comp_id, comp_data.get('name', f'Competition {comp_id}'), True, comp_data.get('popularityRank', 999)))
                
                # Insert competition into database
                cursor.execute('''
                    INSERT OR REPLACE INTO competitions 
                    (id, name, has_standings, popularity_rank, sport_id, country_id)
                    VALUES (?, ?, ?, ?, 1, ?)
                ''', (comp_id, comp_data.get('name'), True, comp_data.get('popularityRank', 999), comp_data.get('countryId')))
                
                print(f"  ✅ Added {comp_data.get('name')} to database")
                time.sleep(1)  # Rate limit
        
        conn.commit()
    else:
        # Get competitions from database (normal operation)
        cursor.execute('''
            SELECT DISTINCT c.id, c.name, c.has_standings, c.popularity_rank
            FROM competitions c
            WHERE c.has_standings = 1 
            ORDER BY c.popularity_rank ASC NULLS LAST
            LIMIT 100
        ''')
        competitions = cursor.fetchall()
    
    conn.close()
    
    print(f"📊 Found {len(competitions)} active competitions to update")
    return competitions

def update_competition_teams(comp_id, comp_name):
    """Update teams for a specific competition"""
    # Get current standings
    url = f"https://webws.365scores.com/web/standings/?appTypeId={APP_ID}&langId={LANG_ID}&timezoneName={TZ_NAME}&userCountryId={USER_COUNTRY_ID}&competitions={comp_id}"
    
    data = make_api_request(url, f"Fetching {comp_name} standings")
    if not data:
        return 0
    
    standings = data.get('standings', [])
    if not standings or 'rows' not in standings[0]:
        print(f"    ⚠️ No standings data for {comp_name}")
        return 0
    
    teams_data = []
    for row in standings[0]['rows']:
        competitor = row.get('competitor')
        if competitor and 'id' in competitor:
            teams_data.append({
                'team_id': competitor['id'],
                'team_name': competitor.get('name', ''),
                'team_name_for_url': competitor.get('nameForURL', ''),
                'team_country_id': competitor.get('countryId'),
                'image_version': competitor.get('imageVersion'),
                'is_national': competitor.get('isNational', False),
                'competition_id': comp_id,
                'position': row.get('position'),
                'points': row.get('points')
            })
    
    if not teams_data:
        print(f"    ⚠️ No teams found for {comp_name}")
        return 0
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated_teams = 0
    new_teams = 0
    
    for team in teams_data:
        # Update or insert team
        cursor.execute('''
            INSERT OR REPLACE INTO teams (id, name, name_for_url, country_id, main_competition_id, image_version, is_national)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            team['team_id'],
            team['team_name'],
            team['team_name_for_url'],
            team['team_country_id'],
            comp_id,  # Set as main competition
            team['image_version'],
            team['is_national']
        ))
        
        # Check if this is a new team
        if cursor.rowcount > 0:
            new_teams += 1
        
        # Update team_competitions relationship
        cursor.execute('''
            INSERT OR REPLACE INTO team_competitions (team_id, competition_id, season_num, is_active)
            VALUES (?, ?, (SELECT current_season_num FROM competitions WHERE id = ?), 1)
        ''', (team['team_id'], comp_id, comp_id))
        
        updated_teams += 1
    
    conn.commit()
    conn.close()
    
    print(f"    ✅ Updated {updated_teams} teams ({new_teams} new)")
    return updated_teams

def update_current_season():
    """Main function to update current season data"""
    print(f"🚀 DAILY DATABASE UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*60)
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("❌ Database not found! Please run create_schema.py first.")
        return False
    
    # Get active competitions
    competitions = get_active_competitions()
    if not competitions:
        print("❌ No active competitions found in database")
        return False
    
    total_updated = 0
    successful_updates = 0
    
    for i, (comp_id, comp_name, has_standings, popularity_rank) in enumerate(competitions, 1):
        print(f"\n[{i:2d}/{len(competitions)}] {comp_name} (ID: {comp_id})")
        
        if not has_standings:
            print(f"    ⏭️ Skipping - no standings available")
            continue
            
        teams_updated = update_competition_teams(comp_id, comp_name)
        
        if teams_updated > 0:
            total_updated += teams_updated
            successful_updates += 1
        
        # Rate limiting
        time.sleep(1)
        
        # Progress update every 10 competitions
        if i % 10 == 0:
            print(f"\n📊 Progress: {i}/{len(competitions)} competitions processed")
            print(f"   Teams updated: {total_updated}, Successful updates: {successful_updates}")
    
    # Final summary
    print(f"\n🎯 UPDATE COMPLETE")
    print(f"   Competitions processed: {len(competitions)}")
    print(f"   Successful updates: {successful_updates}")
    print(f"   Total teams updated: {total_updated}")
    
    # Update completion timestamp
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS update_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_type TEXT,
            competitions_processed INTEGER,
            teams_updated INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        INSERT INTO update_log (update_type, competitions_processed, teams_updated)
        VALUES (?, ?, ?)
    ''', ('current_season', successful_updates, total_updated))
    conn.commit()
    conn.close()
    
    return True

if __name__ == "__main__":
    success = update_current_season()
    if not success:
        exit(1)
