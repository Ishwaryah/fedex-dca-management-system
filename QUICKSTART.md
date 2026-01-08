# QUICK START GUIDE
## FedEx DCA Management System 

###  5-Minute Setup (Windows/Mac/Linux)

**Step 1: Install Python (if not installed)**
- Download from: https://www.python.org/downloads/
- Version: 3.8 or higher
- Check: `python --version` in terminal

**Step 2: Open Terminal/Command Prompt**
- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac**: Press `Cmd + Space`, type `terminal`, press Enter
- **Linux**: Press `Ctrl + Alt + T`

**Step 3: Navigate to Project**
```bash
cd path/to/fedex-dca-system
```

**Step 4: Install Dependencies**
```bash
pip install -r requirements.txt
```
⏱️ Takes ~2 minutes

**Step 5: Verify Data & Models Exist**
```bash
# These files should already exist:
ls data/cases_1000.csv
ls models/recovery_model.pkl
ls models/dca_matcher.pkl
```

**Step 6: Start Flask API**
```bash
python app.py
```
 You should see: "Running on http://localhost:5000"
**KEEP THIS TERMINAL OPEN!**

**Step 7: Open Dashboard**
- Open `dashboard.html` in your browser (Chrome, Firefox, Safari, Edge)
- OR: Just double-click the `dashboard.html` file
- Dashboard will automatically connect to API

**Step 8: Test It Works**
- You should see metrics loading
- Try searching for "TechCorp" in the search box
- Click "High Priority" filter button
- Everything should work smoothly!



**1. Live Dashboard 
- "This is our real-time DCA management dashboard"
- Point to the 4 key metrics at top
- "Everything you see is powered by our ML models"

**2. Critical Alerts 
- "The system automatically flags problems"
- Point to the red alerts
- "Managers know immediately what needs attention"

**3. ML Predictions 
- Click on a case in the table
- "Each case has AI-predicted recovery probability"
- "The system recommends the optimal DCA"
- Show priority scores

**4. DCA Performance 
- Point to the leaderboard
- "We rank DCAs objectively based on data"
- "This drives better contracts and accountability"




---

## Troubleshooting

### Dashboard Shows "Loading..." Forever

**Problem**: Flask API not running  
**Solution**: Make sure you ran `python app.py` and it's still running

### "ModuleNotFoundError"

**Problem**: Dependencies not installed  
**Solution**: Run `pip install -r requirements.txt`

### CORS Errors in Browser Console

**Problem**: Browser blocking API calls  
**Solution**: Update line 598 in dashboard.html to match your API URL

### Port 5000 Already in Use

**Problem**: Another app using port 5000  
**Solution**: In `app.py`, change line 586 from `port=5000` to `port=5001`

---

## 📊 Key Numbers to Mention

- **1000 case samples** in dataset
- **74.3% model accuracy** (Phase 1)
- **Target: 85%+** (Phase 2 with Random Forest)
- **5 different DCAs** with performance tracking
- **4 priority levels** (Low, Medium, High, Critical)
- **7 API endpoints** serving data
- **Real-time alerts** for problems

---


**Code Example (Phase 2):**
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Prepare features
X = df[['amount', 'days_overdue', 'customer_avg_days_late']]
y = df['recovered']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = RandomForestClassifier(n_estimators=100, max_depth=10)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Model Accuracy: {accuracy*100:.1f}%")

# Save
import pickle
with open('models/recovery_model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

---


**Git Commands:**
```bash
git init
git add .
git commit -m "Initial commit: FedEx DCA Management System"
git remote add origin <your-repo-url>
git push -u origin main
```

---



---


