#!/usr/bin/env python3
"""
Database Schema Creation
Creates the database schema from scratch if no database exists
"""

import sqlite3
import os

def create_database_schema():
    """Create the complete database schema"""
    
    db_path = '../../new_project/db/soccer_data_colab.db'
    
    # Create db directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print("🗄️ Creating database schema...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create sports table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sports (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        name_for_url TEXT,
        draw_support BOOLEAN DEFAULT FALSE,
        image_version INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create countries table  
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        name_for_url TEXT,
        image_version INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create competitions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY,
        country_id INTEGER,
        sport_id INTEGER,
        name TEXT NOT NULL,
        long_name TEXT,
        name_for_url TEXT,
        has_standings BOOLEAN DEFAULT FALSE,
        has_live_standings BOOLEAN DEFAULT FALSE,
        has_standings_groups BOOLEAN DEFAULT FALSE,
        has_brackets BOOLEAN DEFAULT FALSE,
        has_stats BOOLEAN DEFAULT FALSE,
        has_history BOOLEAN DEFAULT FALSE,
        popularity_rank INTEGER,
        image_version INTEGER,
        current_stage_type INTEGER,
        competitors_type INTEGER,
        current_phase_num INTEGER,
        current_season_num INTEGER,
        current_stage_num INTEGER,
        is_international BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries (id),
        FOREIGN KEY (sport_id) REFERENCES sports (id)
    )
    ''')
    
    # Create seasons table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seasons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id INTEGER NOT NULL,
        season_num INTEGER NOT NULL,
        season_name TEXT,
        is_current BOOLEAN DEFAULT FALSE,
        teams_populated BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (competition_id) REFERENCES competitions (id),
        UNIQUE(competition_id, season_num)
    )
    ''')
    
    # Create teams table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        name_for_url TEXT,
        country_id INTEGER,
        main_competition_id INTEGER,
        image_version INTEGER,
        is_national BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries (id),
        FOREIGN KEY (main_competition_id) REFERENCES competitions (id)
    )
    ''')
    
    # Create team_competitions table (many-to-many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER NOT NULL,
        competition_id INTEGER NOT NULL,
        season_num INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES teams (id),
        FOREIGN KEY (competition_id) REFERENCES competitions (id),
        UNIQUE(team_id, competition_id, season_num)
    )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_teams_country ON teams(country_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_teams_competition ON teams(main_competition_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_competitions_country ON competitions(country_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_competitions_popularity ON competitions(popularity_rank)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_competitions_team ON team_competitions(team_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_competitions_comp ON team_competitions(competition_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_seasons_competition ON seasons(competition_id)')
    
    conn.commit()
    conn.close()
    
    print("✅ Database schema created successfully!")
    return db_path

if __name__ == "__main__":
    create_database_schema()
