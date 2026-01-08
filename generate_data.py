"""
FedEx DCA System - Data Generator
Generates 1000 realistic debt collection case samples
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_CASES = 1000

# Sample data pools
CUSTOMER_NAMES = [
    "TechCorp Industries", "Global Logistics Inc", "Retail Solutions LLC", 
    "Manufacturing Co", "Express Shipping Ltd", "Supply Chain Partners",
    "Transport Systems Inc", "Distribution Networks", "Freight Solutions",
    "Warehouse Co", "Cargo Express", "Swift Transport", "Premier Logistics",
    "Metro Shipping", "Alliance Freight", "Continental Express", "Pacific Trade",
    "Atlantic Cargo", "Northern Routes", "Southern Transport", "East Coast Logistics",
    "West Side Shipping", "Central Distribution", "Regional Express", "National Freight"
]

INDUSTRIES = [
    "Technology", "Retail", "Manufacturing", "Healthcare", "Finance",
    "Logistics", "Construction", "Energy", "Telecommunications", "Automotive"
]

DCAS = ["DCA-Alpha", "DCA-Beta", "DCA-Gamma", "DCA-Omega", "DCA-Prime"]

STATUSES = ["Active", "Promised", "Stalled", "Disputed"]

def generate_cases(num_cases=NUM_CASES):
    """Generate realistic debt collection cases"""
    
    cases = []
    
    for i in range(num_cases):
        case_id = f"DCA-{2000 + i}"
        
        # Generate customer name (with some repeats for realism)
        if random.random() < 0.3:  # 30% chance of repeat customer
            customer = random.choice(CUSTOMER_NAMES)
        else:
            base_name = random.choice(CUSTOMER_NAMES)
            suffix = random.choice(["Corp", "Inc", "LLC", "Ltd", "Group", "Solutions"])
            customer = f"{base_name.split()[0]} {suffix}"
        
        # Amount distribution (realistic curve)
        # Most cases are medium value, fewer high-value
        amount_category = np.random.choice(
            ["low", "medium", "high", "critical"],
            p=[0.35, 0.45, 0.15, 0.05]  # Probability distribution
        )
        
        if amount_category == "low":
            amount = np.random.uniform(5000, 25000)
        elif amount_category == "medium":
            amount = np.random.uniform(25000, 75000)
        elif amount_category == "high":
            amount = np.random.uniform(75000, 150000)
        else:  # critical
            amount = np.random.uniform(150000, 300000)
        
        # Days overdue (correlated with amount - high value ages differently)
        if amount > 100000:
            # High-value cases get attention faster OR age badly
            days_overdue = int(np.random.choice(
                [np.random.uniform(15, 45), np.random.uniform(85, 150)],
                p=[0.7, 0.3]
            ))
        else:
            # Medium/low value follows normal aging
            days_overdue = int(np.random.gamma(shape=3, scale=15))
            days_overdue = min(days_overdue, 200)  # Cap at 200 days
        
        # Customer payment history (average days late over last 24 months)
        # Good customers: 0-15 days avg late
        # Medium: 15-45 days
        # Poor: 45+ days
        history_category = np.random.choice(
            ["good", "medium", "poor"],
            p=[0.25, 0.50, 0.25]
        )
        
        if history_category == "good":
            avg_days_late = np.random.uniform(0, 15)
            late_count = np.random.randint(0, 3)
        elif history_category == "medium":
            avg_days_late = np.random.uniform(15, 45)
            late_count = np.random.randint(2, 8)
        else:  # poor
            avg_days_late = np.random.uniform(45, 90)
            late_count = np.random.randint(6, 15)
        
        # Industry
        industry = random.choice(INDUSTRIES)
        
        # Geographic location
        state = random.choice([
            "CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
            "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI"
        ])
        
        # DCA assignment (for now, random - will be optimized by model)
        dca = random.choice(DCAS)
        
        # Status (correlated with days overdue)
        if days_overdue < 30:
            status = np.random.choice(["Active", "Promised"], p=[0.7, 0.3])
        elif days_overdue < 60:
            status = np.random.choice(["Active", "Promised", "Stalled"], p=[0.5, 0.3, 0.2])
        else:
            status = np.random.choice(["Active", "Stalled", "Disputed"], p=[0.3, 0.5, 0.2])
        
        # Last contact (realistic distribution)
        if status == "Active":
            last_contact_days = np.random.randint(1, 5)
        elif status == "Promised":
            last_contact_days = np.random.randint(1, 7)
        elif status == "Stalled":
            last_contact_days = np.random.randint(7, 30)
        else:  # Disputed
            last_contact_days = np.random.randint(3, 14)
        
        # Contact attempts
        contact_attempts = max(1, int(days_overdue / 7)) + np.random.randint(-2, 3)
        contact_attempts = max(1, contact_attempts)
        
        # Invoice date
        invoice_date = datetime.now() - timedelta(days=days_overdue + np.random.randint(30, 90))
        
        # Actual recovery (for training model later)
        # This simulates whether case was eventually recovered
        # Based on: amount, days overdue, history, DCA performance
        recovery_probability = calculate_recovery_probability(
            amount, days_overdue, avg_days_late, dca
        )
        recovered = 1 if random.random() < recovery_probability else 0
        
        # Days to recovery (if recovered)
        if recovered:
            # Inversely related to amount and history quality
            base_days = 15 if amount > 75000 else 25
            days_to_recovery = int(base_days + np.random.exponential(scale=10))
        else:
            days_to_recovery = None
        
        case = {
            "case_id": case_id,
            "customer_name": customer,
            "amount": round(amount, 2),
            "days_overdue": days_overdue,
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "industry": industry,
            "state": state,
            "customer_avg_days_late": round(avg_days_late, 1),
            "customer_late_count_24m": late_count,
            "assigned_dca": dca,
            "status": status,
            "last_contact_days_ago": last_contact_days,
            "contact_attempts": contact_attempts,
            "recovered": recovered,
            "days_to_recovery": days_to_recovery
        }
        
        cases.append(case)
    
    return pd.DataFrame(cases)


def calculate_recovery_probability(amount, days_overdue, avg_days_late, dca):
    """Calculate probability of recovery based on case characteristics"""
    
    # Base probability
    prob = 0.7
    
    # Amount factor (higher amounts slightly harder)
    if amount > 100000:
        prob -= 0.1
    
    # Days overdue factor (exponential decay)
    if days_overdue < 30:
        prob += 0.15
    elif days_overdue < 60:
        prob += 0.05
    elif days_overdue < 90:
        prob -= 0.1
    else:
        prob -= 0.25
    
    # Customer history factor
    if avg_days_late < 15:
        prob += 0.15
    elif avg_days_late < 45:
        prob += 0.0
    else:
        prob -= 0.15
    
    # DCA performance factor (simulated)
    dca_performance = {
        "DCA-Alpha": 0.15,
        "DCA-Omega": 0.10,
        "DCA-Prime": 0.05,
        "DCA-Beta": 0.0,
        "DCA-Gamma": -0.05
    }
    prob += dca_performance.get(dca, 0)
    
    # Ensure probability is between 0 and 1
    return max(0.1, min(0.95, prob))


def main():
    """Generate and save dataset"""
    
    print("🔄 Generating 1000 realistic debt collection cases...")
    
    # Generate data
    df = generate_cases(NUM_CASES)
    
    # Save to CSV
    output_path = "data/cases_1000.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Dataset saved to: {output_path}")
    print(f"\n📊 Dataset Summary:")
    print(f"   Total Cases: {len(df)}")
    print(f"   Total Amount Outstanding: ${df['amount'].sum():,.2f}")
    print(f"   Average Amount: ${df['amount'].mean():,.2f}")
    print(f"   Average Days Overdue: {df['days_overdue'].mean():.1f}")
    print(f"\n📈 Status Distribution:")
    print(df['status'].value_counts())
    print(f"\n🏢 DCA Distribution:")
    print(df['assigned_dca'].value_counts())
    print(f"\n💰 Amount Categories:")
    print(f"   Low (<$25k): {len(df[df['amount'] < 25000])}")
    print(f"   Medium ($25k-$75k): {len(df[(df['amount'] >= 25000) & (df['amount'] < 75000)])}")
    print(f"   High ($75k-$150k): {len(df[(df['amount'] >= 75000) & (df['amount'] < 150000)])}")
    print(f"   Critical (>$150k): {len(df[df['amount'] >= 150000])}")
    print(f"\n✨ Recovery Rate: {df['recovered'].mean()*100:.1f}%")


if __name__ == "__main__":
    main()
