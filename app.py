"""
FedEx DCA System - Flask Backend API
Serves data to the dashboard via RESTful endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import pickle
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard to access API

# Load models and data
print("🚀 Loading models and data...")

try:
    with open("models/recovery_model.pkl", "rb") as f:
        recovery_model = pickle.load(f)
    print("   ✅ Recovery model loaded")
except:
    print("   ⚠️  Recovery model not found - run train_model.py first")
    recovery_model = None

try:
    with open("models/dca_matcher.pkl", "rb") as f:
        dca_matcher = pickle.load(f)
    print("   ✅ DCA matcher loaded")
except:
    print("   ⚠️  DCA matcher not found - run train_model.py first")
    dca_matcher = None

try:
    df_cases = pd.read_csv("data/cases_1000.csv")
    print(f"   ✅ Loaded {len(df_cases)} cases")
except:
    print("   ⚠️  Dataset not found - run generate_data.py first")
    df_cases = pd.DataFrame()


@app.route('/')
def home():
    """API home page"""
    return jsonify({
        "service": "FedEx DCA Management API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/metrics",
            "/api/cases",
            "/api/alerts",
            "/api/dcas",
            "/api/charts/distribution",
            "/api/charts/recovery-trend",
            "/api/case/<case_id>"
        ]
    })


@app.route('/api/metrics')
def get_metrics():
    """Get top-level dashboard metrics"""
    
    if df_cases.empty:
        return jsonify({"error": "No data available"}), 500
    
    # Calculate key metrics
    total_outstanding = df_cases['amount'].sum()
    critical_cases = len(df_cases[
        (df_cases['amount'] > 50000) & 
        (df_cases['days_overdue'] > 80)
    ])
    
    # This month recovery (simulated)
    this_month_recovery = df_cases[df_cases['recovered'] == 1]['amount'].sum() * 0.35
    
    # Recovery rate
    recovery_rate = (df_cases['recovered'].mean() * 100)
    
    metrics = {
        "total_outstanding": round(total_outstanding, 2),
        "total_outstanding_formatted": f"${total_outstanding/1000000:.1f}M",
        "critical_cases": critical_cases,
        "this_month_recovery": round(this_month_recovery, 2),
        "this_month_recovery_formatted": f"${this_month_recovery/1000000:.1f}M",
        "recovery_rate": round(recovery_rate, 1),
        "recovery_rate_change": "+14%",
        "outstanding_change": "-8.2%",
        "recovery_change": "+34.5%",
        "critical_change": "+12"
    }
    
    return jsonify(metrics)


@app.route('/api/cases')
def get_cases():
    """Get all cases with predictions"""
    
    if df_cases.empty or recovery_model is None:
        return jsonify({"error": "Data or model not available"}), 500
    
    # Get query parameters
    limit = request.args.get('limit', 100, type=int)
    status_filter = request.args.get('status', None)
    priority_filter = request.args.get('priority', None)
    search = request.args.get('search', None)
    
    # Apply filters
    df_filtered = df_cases.copy()
    
    if status_filter:
        df_filtered = df_filtered[df_filtered['status'].str.lower() == status_filter.lower()]
    
    if search:
        df_filtered = df_filtered[
            df_filtered['customer_name'].str.contains(search, case=False, na=False) |
            df_filtered['case_id'].str.contains(search, case=False, na=False) |
            df_filtered['assigned_dca'].str.contains(search, case=False, na=False)
        ]
    
    # Add predictions to each case
    cases_list = []
    
    for idx, row in df_filtered.head(limit).iterrows():
        # Get ML predictions
        recovery_prob = recovery_model.predict_recovery_probability(
            row['amount'],
            row['days_overdue'],
            row['customer_avg_days_late'],
            row['assigned_dca']
        )
        
        days_to_recovery = recovery_model.predict_days_to_recovery(
            row['amount'],
            row['days_overdue'],
            recovery_prob
        )
        
        priority_score = recovery_model.get_priority_score(
            row['amount'],
            row['days_overdue'],
            recovery_prob
        )
        
        # Determine priority level
        if priority_score >= 7:
            priority = "high"
        elif priority_score >= 4:
            priority = "medium"
        else:
            priority = "low"
        
        # Apply priority filter if specified
        if priority_filter and priority != priority_filter.lower():
            continue
        
        case = {
            "case_id": row['case_id'],
            "customer_name": row['customer_name'],
            "amount": round(row['amount'], 2),
            "amount_formatted": f"${row['amount']:,.0f}",
            "days_overdue": int(row['days_overdue']),
            "invoice_date": row['invoice_date'],
            "industry": row['industry'],
            "state": row['state'],
            "assigned_dca": row['assigned_dca'],
            "status": row['status'],
            "last_contact_days_ago": int(row['last_contact_days_ago']),
            "last_contact": f"{int(row['last_contact_days_ago'])} days ago",
            "contact_attempts": int(row['contact_attempts']),
            "recovery_probability": recovery_prob,
            "expected_days_to_recovery": days_to_recovery,
            "priority": priority,
            "priority_score": priority_score,
            "customer_history": {
                "avg_days_late": row['customer_avg_days_late'],
                "late_count_24m": int(row['customer_late_count_24m'])
            }
        }
        
        cases_list.append(case)
    
    return jsonify({
        "total": len(cases_list),
        "cases": cases_list
    })


@app.route('/api/alerts')
def get_alerts():
    """Generate critical alerts based on case analysis"""
    
    if df_cases.empty:
        return jsonify({"error": "No data available"}), 500
    
    alerts = []
    
    # Alert 1: High-value stalled cases
    stalled_high_value = df_cases[
        (df_cases['status'] == 'Stalled') &
        (df_cases['amount'] > 75000)
    ].sort_values('amount', ascending=False).head(3)
    
    for idx, row in stalled_high_value.iterrows():
        alerts.append({
            "priority": "high",
            "title": "High-Value Case Stalled",
            "details": f"Case #{row['case_id']} (${row['amount']:,.0f}) - No contact in {row['last_contact_days_ago']} days by {row['assigned_dca']}",
            "time": f"{random.randint(5, 60)} mins ago",
            "case_id": row['case_id']
        })
    
    # Alert 2: Approaching 90-day threshold
    approaching_threshold = df_cases[
        (df_cases['days_overdue'] >= 85) &
        (df_cases['days_overdue'] < 95) &
        (df_cases['status'] != 'Stalled')
    ].head(2)
    
    for idx, row in approaching_threshold.iterrows():
        alerts.append({
            "priority": "high",
            "title": "SLA Breach Imminent",
            "details": f"Case #{row['case_id']} approaching 90-day threshold (currently {row['days_overdue']} days)",
            "time": f"{random.randint(30, 120)} mins ago",
            "case_id": row['case_id']
        })
    
    # Alert 3: Missed payment promises
    promised_cases = df_cases[
        (df_cases['status'] == 'Promised') &
        (df_cases['last_contact_days_ago'] > 5)
    ].head(2)
    
    for idx, row in promised_cases.iterrows():
        alerts.append({
            "priority": "medium",
            "title": "Payment Promise Overdue",
            "details": f"Customer {row['customer_name']} - Promised payment of ${row['amount']:,.0f} not received",
            "time": f"{random.randint(60, 180)} mins ago",
            "case_id": row['case_id']
        })
    
    # Alert 4: DCA performance issues
    dca_stats = df_cases.groupby('assigned_dca').agg({
        'recovered': 'mean',
        'case_id': 'count'
    }).reset_index()
    
    low_performers = dca_stats[dca_stats['recovered'] < 0.6]
    
    for idx, row in low_performers.iterrows():
        alerts.append({
            "priority": "medium",
            "title": "DCA Performance Drop",
            "details": f"{row['assigned_dca']} recovery rate at {row['recovered']*100:.0f}% (target: 65%+)",
            "time": f"{random.randint(120, 300)} mins ago",
            "case_id": None
        })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda x: priority_order[x["priority"]])
    
    return jsonify({
        "total": len(alerts),
        "alerts": alerts[:10]  # Return top 10
    })


@app.route('/api/dcas')
def get_dcas():
    """Get DCA performance rankings"""
    
    if df_cases.empty or dca_matcher is None:
        return jsonify({"error": "Data or model not available"}), 500
    
    # Get rankings from model
    rankings = dca_matcher.get_dca_rankings()
    
    # Enhance with actual case stats
    dca_stats = df_cases.groupby('assigned_dca').agg({
        'case_id': 'count',
        'amount': 'sum',
        'recovered': 'mean',
        'days_to_recovery': 'mean'
    }).reset_index()
    
    enhanced_rankings = []
    
    for i, dca_info in enumerate(rankings, 1):
        dca_name = dca_info['dca_name']
        stats = dca_stats[dca_stats['assigned_dca'] == dca_name].iloc[0] if len(dca_stats[dca_stats['assigned_dca'] == dca_name]) > 0 else None
        
        if stats is not None:
            enhanced_rankings.append({
                "rank": i,
                "name": dca_name,
                "score": f"{dca_info['success_rate']:.0f}%",
                "success_rate": dca_info['success_rate'],
                "avg_days": dca_info['avg_days'],
                "total_cases": int(stats['case_id']),
                "total_recovered": round(stats['amount'] * stats['recovered'], 2),
                "total_recovered_formatted": f"${stats['amount'] * stats['recovered'] / 1000000:.1f}M",
                "stats": f"{int(stats['case_id'])} cases • Avg {dca_info['avg_days']} days • ${stats['amount'] * stats['recovered'] / 1000000:.1f}M recovered",
                "strengths": dca_info['strengths']
            })
    
    return jsonify({
        "total": len(enhanced_rankings),
        "dcas": enhanced_rankings
    })


@app.route('/api/charts/distribution')
def get_case_distribution():
    """Get case distribution by status for chart"""
    
    if df_cases.empty:
        return jsonify({"error": "No data available"}), 500
    
    distribution = df_cases['status'].value_counts().to_dict()
    
    return jsonify({
        "labels": list(distribution.keys()),
        "data": list(distribution.values())
    })


@app.route('/api/charts/recovery-trend')
def get_recovery_trend():
    """Get 30-day recovery trend for chart"""
    
    # Simulated weekly trend data
    trend = {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "data": [0.5, 0.8, 1.2, 2.8]  # Millions
    }
    
    return jsonify(trend)


@app.route('/api/case/<case_id>')
def get_case_detail(case_id):
    """Get detailed information for a specific case"""
    
    if df_cases.empty or recovery_model is None:
        return jsonify({"error": "Data or model not available"}), 500
    
    case_row = df_cases[df_cases['case_id'] == case_id]
    
    if len(case_row) == 0:
        return jsonify({"error": "Case not found"}), 404
    
    row = case_row.iloc[0]
    
    # Get predictions
    recovery_prob = recovery_model.predict_recovery_probability(
        row['amount'],
        row['days_overdue'],
        row['customer_avg_days_late'],
        row['assigned_dca']
    )
    
    days_to_recovery = recovery_model.predict_days_to_recovery(
        row['amount'],
        row['days_overdue'],
        recovery_prob
    )
    
    priority_score = recovery_model.get_priority_score(
        row['amount'],
        row['days_overdue'],
        recovery_prob
    )
    
    # Get recommended DCA
    recommended_dca = dca_matcher.recommend_dca(
        row['amount'],
        row['days_overdue'],
        row['customer_avg_days_late']
    )
    
    case_detail = {
        "case_id": row['case_id'],
        "customer_name": row['customer_name'],
        "amount": round(row['amount'], 2),
        "days_overdue": int(row['days_overdue']),
        "invoice_date": row['invoice_date'],
        "industry": row['industry'],
        "state": row['state'],
        "assigned_dca": row['assigned_dca'],
        "recommended_dca": recommended_dca,
        "status": row['status'],
        "last_contact_days_ago": int(row['last_contact_days_ago']),
        "contact_attempts": int(row['contact_attempts']),
        "customer_history": {
            "avg_days_late": row['customer_avg_days_late'],
            "late_count_24m": int(row['customer_late_count_24m'])
        },
        "predictions": {
            "recovery_probability": recovery_prob,
            "expected_days_to_recovery": days_to_recovery,
            "priority_score": priority_score
        },
        "recommendations": {
            "action": "Immediate escalation" if priority_score > 7 else "Continue monitoring",
            "reason": f"High priority case with {recovery_prob}% recovery probability"
        }
    }
    
    return jsonify(case_detail)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 FedEx DCA Management API Server")
    print("="*60)
    print("\n📡 API Endpoints:")
    print("   • http://localhost:5000/api/metrics")
    print("   • http://localhost:5000/api/cases")
    print("   • http://localhost:5000/api/alerts")
    print("   • http://localhost:5000/api/dcas")
    print("   • http://localhost:5000/api/charts/distribution")
    print("   • http://localhost:5000/api/charts/recovery-trend")
    print("   • http://localhost:5000/api/case/<case_id>")
    print("\n🌐 Open dashboard.html in browser to view UI")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
