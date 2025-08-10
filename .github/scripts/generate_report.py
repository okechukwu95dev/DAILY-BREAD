#!/usr/bin/env python3
"""
Generate Update Report
Creates a summary report of the database update
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = '../../new_project/db/soccer_data_colab.db'

def generate_report():
    """Generate comprehensive update report"""
    
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"📋 365SCORES DATABASE UPDATE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*60)
    
    # Database Overview
    print("\n🗄️ DATABASE OVERVIEW")
    
    # Get table counts
    tables = {
        'countries': 'Countries/Regions',
        'sports': 'Sports',
        'competitions': 'Competitions/Leagues', 
        'seasons': 'Season Records',
        'teams': 'Teams',
        'team_competitions': 'Team-Competition Relations'
    }
    
    for table, description in tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  📊 {description}: {count:,}")
        except:
            print(f"  ❌ {description}: Table not found")
    
    # Database size
    size_mb = round(os.path.getsize(DB_PATH) / 1024 / 1024, 2)
    print(f"  💾 Database size: {size_mb} MB")
    
    # Latest Updates
    print(f"\n⏰ RECENT UPDATE ACTIVITY")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='update_log'")
    if cursor.fetchone():
        cursor.execute("""
            SELECT update_type, competitions_processed, teams_updated, timestamp 
            FROM update_log 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        updates = cursor.fetchall()
        
        if updates:
            for update in updates:
                update_type, comps, teams, timestamp = update
                print(f"  🔄 {timestamp}: {update_type} - {comps} competitions, {teams} teams")
        else:
            print(f"  ⚠️ No update records found")
    else:
        print(f"  ⚠️ Update log not available")
    
    # Competition Statistics  
    print(f"\n🏆 COMPETITION ANALYSIS")
    
    # Total competitions by feature
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE has_standings = 1")
    standings_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE has_stats = 1")
    stats_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE has_brackets = 1")
    brackets_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM competitions")
    total_comps = cursor.fetchone()[0]
    
    print(f"  📊 With standings: {standings_count}/{total_comps} ({standings_count/total_comps*100:.1f}%)")
    print(f"  📈 With stats: {stats_count}/{total_comps} ({stats_count/total_comps*100:.1f}%)")
    print(f"  🏆 With brackets: {brackets_count}/{total_comps} ({brackets_count/total_comps*100:.1f}%)")
    
    # Most popular competitions
    print(f"\n⭐ TOP 10 MOST POPULAR COMPETITIONS")
    cursor.execute("""
        SELECT name, popularity_rank, has_standings, has_stats 
        FROM competitions 
        WHERE popularity_rank IS NOT NULL 
        ORDER BY popularity_rank ASC 
        LIMIT 10
    """)
    popular = cursor.fetchall()
    
    for i, (name, rank, standings, stats) in enumerate(popular, 1):
        features = []
        if standings: features.append("📊")
        if stats: features.append("📈")
        features_str = "".join(features) if features else "❌"
        print(f"  {i:2d}. {name[:35]:35} | Rank: {rank:,} | {features_str}")
    
    # Team Distribution
    print(f"\n🏃 TEAM DISTRIBUTION BY COUNTRY")
    cursor.execute("""
        SELECT c.name, COUNT(t.id) as team_count
        FROM countries c
        LEFT JOIN teams t ON c.id = t.country_id
        GROUP BY c.id, c.name
        HAVING team_count > 0
        ORDER BY team_count DESC
        LIMIT 10
    """)
    countries = cursor.fetchall()
    
    for country, count in countries:
        print(f"  🏁 {country[:25]:25}: {count:4d} teams")
    
    # Active Relationships
    print(f"\n🔗 ACTIVE TEAM-COMPETITION RELATIONSHIPS")
    cursor.execute("SELECT COUNT(*) FROM team_competitions WHERE is_active = 1")
    active_relations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT team_id) FROM team_competitions WHERE is_active = 1")
    active_teams = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT competition_id) FROM team_competitions WHERE is_active = 1")
    active_competitions = cursor.fetchone()[0]
    
    print(f"  🏃 Teams in active competitions: {active_teams:,}")
    print(f"  🏆 Competitions with active teams: {active_competitions:,}")
    print(f"  🔗 Total active relationships: {active_relations:,}")
    print(f"  📊 Avg teams per competition: {active_relations/active_competitions:.1f}")
    
    # Data Quality Metrics
    print(f"\n✅ DATA QUALITY METRICS")
    
    # Teams without countries
    cursor.execute("SELECT COUNT(*) FROM teams WHERE country_id IS NULL")
    teams_without_countries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM teams")
    total_teams = cursor.fetchone()[0]
    
    coverage = (total_teams - teams_without_countries) / total_teams * 100
    print(f"  🌍 Teams with country data: {total_teams - teams_without_countries:,}/{total_teams:,} ({coverage:.1f}%)")
    
    # Competitions with popularity
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE popularity_rank IS NOT NULL")
    comps_with_popularity = cursor.fetchone()[0]
    popularity_coverage = comps_with_popularity / total_comps * 100
    print(f"  ⭐ Competitions with popularity: {comps_with_popularity}/{total_comps} ({popularity_coverage:.1f}%)")
    
    # Footer
    print(f"\n{'='*60}")
    print(f"🚀 Database ready for use!")
    print(f"📈 Use teams_master.json for frontend integration")
    print(f"🔄 Next update: Tomorrow at 06:00 UTC")
    
    conn.close()

if __name__ == "__main__":
    generate_report()
