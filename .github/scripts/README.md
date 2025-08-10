# 🤖 Daily Database Automation System

## 🎯 Overview

Automated GitHub Actions workflow that keeps your 365Scores database fresh with daily updates. No more Champions League teams disappearing after the season ends!

## 🚀 How It Works

### ⏰ **Daily Schedule**
- **Runs daily at 06:00 UTC** (2:00 AM EST, 7:00 AM CET)
- **Updates current season data** for all active competitions
- **Maintains team-competition relationships** automatically
- **Creates database releases** for easy download

### 🔄 **Update Process**
1. Downloads existing database from latest GitHub release
2. Updates team standings for active competitions 
3. Validates data integrity
4. Commits changes and creates new release
5. Notifies on failures

## 📋 **Files Structure**
```
new_project/db_automation/
├── create_schema.py          # Creates database from scratch
├── update_current_season.py  # Daily team updates (main script)
├── validate_database.py      # Data integrity checks  
├── generate_report.py        # Update summary report
└── README.md                # This file

.github/workflows/
└── daily-db-update.yml      # GitHub Actions workflow
```

## 🎮 **Manual Usage**

### Run Update Locally
```bash
cd new_project/db_automation
python update_current_season.py
```

### Validate Database
```bash
python validate_database.py
```

### Generate Report
```bash 
python generate_report.py
```

### Create New Database
```bash
python create_schema.py
```

## ⚙️ **GitHub Actions Controls**

### Trigger Manual Update
1. Go to **Actions** tab in your GitHub repo
2. Select **Daily Database Update** workflow  
3. Click **Run workflow**
4. Choose update type:
   - `current_season` - Fast daily update (default)
   - `full_refresh` - Complete database rebuild
   - `competitions_only` - Update competition metadata only

## 📊 **What Gets Updated Daily**

### ✅ **High Priority (Daily)**
- **Current season team standings** for active leagues
- **Team-competition relationships** (who plays where now)
- **New teams** (promoted, relegated, newly formed)
- **Competition activity status**

### ⚠️ **Handles Edge Cases**
- **Mid-season transfers** between competitions
- **Cup eliminations** and advancement
- **League restructuring** and mergers
- **Champions League qualification** changes

## 🔍 **Monitoring & Validation**

### **Automatic Checks**
- ✅ Database file integrity
- ✅ Table structure validation
- ✅ Data relationship consistency  
- ✅ Critical data thresholds (min teams/competitions)
- ✅ Foreign key relationships

### **Update Reports**
Each update generates a report showing:
- Teams updated per competition
- New teams discovered
- Data quality metrics
- Coverage statistics

## 📥 **Using Updated Database**

### **Option 1: GitHub Releases (Recommended)**
1. Go to your repo's **Releases** page
2. Download latest `soccer_data_colab.db`
3. Replace your local database file
4. Regenerate `teams_master.json`:
   ```bash
   python generate_teams_master.py
   ```

### **Option 2: Git Pull**
```bash
git pull origin main
python generate_teams_master.py
```

## 🚨 **Troubleshooting**

### **Database Not Found**
If workflow fails with "Database not found":
1. Run manual workflow with `full_refresh` option
2. This creates database from scratch

### **API Rate Limits**
365Scores API has rate limits:
- **1 request per second** maximum
- Workflow includes automatic delays
- On failure, retry after 1 hour

### **Validation Failures**
If validation fails:
1. Check the workflow logs
2. Look for specific error messages
3. May need manual database repair

## 🎯 **Benefits**

### ✅ **Always Current Data**
- Teams don't disappear after season changes
- New signings and transfers reflected
- Competition changes tracked automatically

### ✅ **Zero Maintenance**
- Runs automatically every day
- No manual intervention needed
- Self-healing with validation

### ✅ **Reliable Frontend**
- Your frontend always has fresh data
- No more "team not found" errors
- Competition dropdowns stay current

## 🔧 **Customization**

### **Change Update Schedule**
Edit `.github/workflows/daily-db-update.yml`:
```yaml
schedule:
  - cron: '0 6 * * *'  # Daily at 6 AM UTC
  # Change to: '0 */6 * * *' for every 6 hours
```

### **Focus on Specific Leagues**
Edit `update_current_season.py`, modify the query:
```python
cursor.execute('''
    SELECT DISTINCT c.id, c.name, c.has_standings, c.popularity_rank
    FROM competitions c
    WHERE c.name IN ('Premier League', 'La Liga', 'Serie A')  # Only major leagues
    ORDER BY c.popularity_rank ASC
''')
```

### **Add Notifications**
Add Slack/Discord webhooks to workflow for update notifications.

---

## 🚀 **Ready to Go!**

Your database will now stay fresh automatically. Champions League teams won't vanish, promoted teams will appear, and your frontend will always have current data!

**Next Steps:**
1. Commit these files to your repo
2. Wait for tomorrow's 6 AM UTC update
3. Check the Actions tab to see it running
4. Download fresh database from Releases
