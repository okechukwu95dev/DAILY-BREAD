#!/usr/bin/env python3
"""
Database Validation Script
Validates the updated database for consistency and completeness
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = '../db/soccer_data_colab.db'

def validate_database():
    """Validate database integrity and completeness"""
    print(f"✅ VALIDATING DATABASE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*60)
    
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    validation_passed = True
    
    # Test 1: Check table existence
    print("🔍 Test 1: Table Structure")
    expected_tables = ['countries', 'competitions', 'teams', 'team_competitions', 'sports', 'seasons']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    for table in expected_tables:
        if table in existing_tables:
            print(f"  ✅ {table} table exists")
        else:
            print(f"  ❌ {table} table missing!")
            validation_passed = False
    
    # Test 2: Check data counts
    print("\n📊 Test 2: Data Completeness")
    
    counts = {}
    for table in expected_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
            print(f"  📋 {table}: {counts[table]:,} records")
    
    # Test 3: Check for critical data
    print("\n🎯 Test 3: Critical Data Validation")
    
    if 'countries' in counts and counts['countries'] < 50:
        print(f"  ⚠️ Only {counts['countries']} countries - expected 100+")
        validation_passed = False
    else:
        print(f"  ✅ Countries count: {counts.get('countries', 0)}")
    
    if 'competitions' in counts and counts['competitions'] < 100:
        print(f"  ⚠️ Only {counts['competitions']} competitions - expected 500+")
        validation_passed = False
    else:
        print(f"  ✅ Competitions count: {counts.get('competitions', 0)}")
    
    if 'teams' in counts and counts['teams'] < 1000:
        print(f"  ⚠️ Only {counts['teams']} teams - expected 3000+")
        validation_passed = False
    else:
        print(f"  ✅ Teams count: {counts.get('teams', 0)}")
    
    # Test 4: Check foreign key relationships
    print("\n🔗 Test 4: Relationship Integrity")
    
    # Teams without countries
    cursor.execute("SELECT COUNT(*) FROM teams WHERE country_id IS NULL")
    teams_without_countries = cursor.fetchone()[0]
    if teams_without_countries > counts.get('teams', 0) * 0.1:  # More than 10% missing
        print(f"  ⚠️ {teams_without_countries} teams without countries ({teams_without_countries/counts.get('teams', 1)*100:.1f}%)")
    else:
        print(f"  ✅ Teams with countries: {counts.get('teams', 0) - teams_without_countries}/{counts.get('teams', 0)}")
    
    # Teams without competitions
    cursor.execute("""
        SELECT COUNT(*) FROM teams t 
        LEFT JOIN team_competitions tc ON t.id = tc.team_id 
        WHERE tc.team_id IS NULL
    """)
    teams_without_competitions = cursor.fetchone()[0]
    if teams_without_competitions > 0:
        print(f"  ⚠️ {teams_without_competitions} teams without competitions")
    else:
        print(f"  ✅ All teams have competition assignments")
    
    # Test 5: Check recent updates
    print("\n⏰ Test 5: Update Recency")
    
    # Check if update_log exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='update_log'")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM update_log ORDER BY timestamp DESC LIMIT 1")
        latest_update = cursor.fetchone()
        if latest_update:
            print(f"  ✅ Latest update: {latest_update[4]} ({latest_update[1]})")
            print(f"  📊 Competitions: {latest_update[2]}, Teams: {latest_update[3]}")
        else:
            print(f"  ⚠️ No update records found")
    else:
        print(f"  ⚠️ Update log table not found")
    
    # Test 6: Check data quality
    print("\n🎯 Test 6: Data Quality")
    
    # Competitions with popularity ranks
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE popularity_rank IS NOT NULL")
    comps_with_popularity = cursor.fetchone()[0]
    print(f"  📈 Competitions with popularity: {comps_with_popularity}/{counts.get('competitions', 0)}")
    
    # Competitions with standings
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE has_standings = 1")
    comps_with_standings = cursor.fetchone()[0]
    print(f"  📊 Competitions with standings: {comps_with_standings}/{counts.get('competitions', 0)}")
    
    conn.close()
    
    # Final result
    print(f"\n{'='*60}")
    if validation_passed:
        print("✅ DATABASE VALIDATION PASSED")
        print("🎯 Database is ready for use!")
    else:
        print("❌ DATABASE VALIDATION FAILED")
        print("⚠️ Some issues detected - check logs above")
    
    return validation_passed

def get_database_stats():
    """Get detailed database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Basic counts
    tables = ['countries', 'competitions', 'teams', 'team_competitions', 'sports', 'seasons']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        except:
            stats[f"{table}_count"] = 0
    
    # Active relationships
    cursor.execute("SELECT COUNT(*) FROM team_competitions WHERE is_active = 1")
    stats['active_team_competitions'] = cursor.fetchone()[0]
    
    # Competitions with features
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE has_standings = 1")
    stats['competitions_with_standings'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM competitions WHERE has_stats = 1")  
    stats['competitions_with_stats'] = cursor.fetchone()[0]
    
    # Top countries by team count
    cursor.execute("""
        SELECT c.name, COUNT(t.id) as team_count 
        FROM countries c 
        LEFT JOIN teams t ON c.id = t.country_id 
        GROUP BY c.id, c.name 
        ORDER BY team_count DESC 
        LIMIT 10
    """)
    stats['top_countries'] = cursor.fetchall()
    
    # Database file size
    stats['db_size_mb'] = round(os.path.getsize(DB_PATH) / 1024 / 1024, 2)
    
    conn.close()
    return stats

if __name__ == "__main__":
    success = validate_database()
    if not success:
        exit(1)
    
    # Print detailed stats
    print(f"\n📊 DETAILED STATISTICS")
    stats = get_database_stats()
    print(f"Database size: {stats['db_size_mb']} MB")
    print(f"Active team-competition relationships: {stats['active_team_competitions']:,}")
    
    print(f"\nTop 5 countries by team count:")
    for country, count in stats['top_countries'][:5]:
        print(f"  {country}: {count} teams")
