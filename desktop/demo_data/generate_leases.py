"""
Generate 10 fake lease agreements with different names
"""
import random
from datetime import datetime, timedelta
import os
from pathlib import Path

# Fake data pools
FIRST_NAMES = [
    "Jennifer", "Michael", "Sarah", "David", "Emily", "James", "Lisa", "Robert",
    "Amanda", "Christopher", "Jessica", "Matthew", "Ashley", "Daniel", "Michelle"
]

LAST_NAMES = [
    "Martinez", "Thompson", "Johnson", "Williams", "Brown", "Davis", "Miller",
    "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris"
]

STREETS = [
    "Mission Street", "Market Street", "Valencia Street", "Howard Street",
    "Folsom Street", "Harrison Street", "Bryant Street", "Brannan Street",
    "Townsend Street", "King Street", "Berry Street", "Channel Street"
]

COMPANIES = [
    "Tech Innovations Inc.", "Digital Solutions LLC", "Cloud Systems Corp.",
    "Data Analytics Group", "Software Dynamics", "AI Research Labs",
    "Web Services International", "Mobile Tech Partners", "Cyber Security Firm",
    "Blockchain Ventures"
]

POSITIONS = [
    "Senior Software Engineer", "Product Manager", "Data Scientist",
    "UX Designer", "Marketing Director", "Sales Executive", "Financial Analyst",
    "Operations Manager", "Account Manager", "Business Analyst"
]

def generate_ssn():
    """Generate fake SSN"""
    return f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"

def generate_phone():
    """Generate fake phone"""
    return f"(415) 555-{random.randint(1000,9999)}"

def generate_email(first_name, last_name):
    """Generate email"""
    return f"{first_name.lower()}.{last_name.lower()}@email.com"

def generate_address(street):
    """Generate address"""
    unit = random.choice(["A", "B", "C", "D", "1", "2", "3", "4"])
    return f"{random.randint(100,999)} {street}, Unit {random.randint(1,10)}{unit}, San Francisco, CA 941{random.randint(0,9):02d}"

def generate_lease_data(index):
    """Generate complete lease data"""

    # Tenant info
    tenant_first = random.choice(FIRST_NAMES)
    tenant_last = random.choice(LAST_NAMES)

    # Landlord info
    landlord_first = random.choice([n for n in FIRST_NAMES if n != tenant_first])
    landlord_last = random.choice(LAST_NAMES)

    # Emergency contact
    emergency_first = random.choice(FIRST_NAMES)
    emergency_last = random.choice(LAST_NAMES)

    # Notary
    notary_first = random.choice(FIRST_NAMES)
    notary_last = random.choice(LAST_NAMES)

    # Dates
    start_date = datetime(2025, 2, 1) + timedelta(days=random.randint(0, 30))
    end_date = start_date + timedelta(days=365)
    sign_date = start_date - timedelta(days=random.randint(10, 30))
    dob = datetime(1985, 1, 1) + timedelta(days=random.randint(0, 365*15))

    # Financial
    rent = random.choice([2800, 3000, 3200, 3400, 3600, 3800, 4000])
    deposit = rent * 2
    income = rent * 4

    return {
        # Agreement date
        "agreement_date": sign_date.strftime("%B %d, %Y"),

        # Landlord
        "landlord_name": f"{landlord_first} {landlord_last}",
        "landlord_address": f"{random.randint(1000,9999)} {random.choice(STREETS)}, San Francisco, CA 941{random.randint(0,9):02d}",
        "landlord_phone": generate_phone(),
        "landlord_email": generate_email(landlord_first, landlord_last),
        "landlord_ssn": generate_ssn(),

        # Tenant
        "tenant_name": f"{tenant_first} {tenant_last}",
        "tenant_address": f"{random.randint(100,999)} {random.choice(STREETS)}, San Francisco, CA 941{random.randint(0,9):02d}",
        "tenant_phone": generate_phone(),
        "tenant_email": generate_email(tenant_first, tenant_last),
        "tenant_ssn": generate_ssn(),
        "tenant_dob": dob.strftime("%B %d, %Y"),

        # Property
        "property_address": generate_address(random.choice(STREETS)),
        "property_type": random.choice(["1-Bedroom Apartment", "2-Bedroom Apartment", "Studio Apartment"]),
        "square_footage": random.choice([650, 750, 850, 950, 1050]),

        # Term
        "start_date": start_date.strftime("%B %d, %Y"),
        "end_date": end_date.strftime("%B %d, %Y"),
        "duration": "12 months",

        # Rent
        "monthly_rent": f"${rent:,.2f}",
        "due_date": "1st of each month",
        "payment_method": random.choice(["Bank Transfer", "Check", "Online Payment"]),
        "late_fee": f"${random.choice([50, 75, 100])}.00 after 5 days",

        # Deposit
        "deposit_amount": f"${deposit:,.2f}",
        "deposit_due": (sign_date + timedelta(days=5)).strftime("%B %d, %Y"),
        "bank_account": f"Wells Fargo - Account #{random.randint(100000000,999999999)}",

        # Emergency contact
        "emergency_name": f"{emergency_first} {emergency_last}",
        "emergency_relation": random.choice(["Brother", "Sister", "Mother", "Father", "Friend"]),
        "emergency_phone": generate_phone(),
        "emergency_address": f"{random.randint(100,999)} {random.choice(['Oak', 'Pine', 'Elm', 'Maple'])} Street, Oakland, CA 946{random.randint(0,9):02d}",

        # Employer
        "employer_name": random.choice(COMPANIES),
        "position": random.choice(POSITIONS),
        "monthly_income": f"${income:,.2f}",
        "work_phone": generate_phone(),

        # Signatures
        "sign_date": sign_date.strftime("%B %d, %Y"),

        # Notary
        "notary_name": f"{notary_first} {notary_last}",
        "notary_license": f"CA-NOT-{random.randint(100000,999999)}",
        "notary_expiry": "December 31, 2026"
    }

def create_html(data, output_path):
    """Create HTML lease from template"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Residential Lease Agreement</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .section {{
            margin-bottom: 20px;
        }}
        .section-title {{
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .field {{
            display: inline-block;
            border-bottom: 1px solid #000;
            min-width: 200px;
            padding: 0 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        td {{
            padding: 8px;
            border: 1px solid #000;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">RESIDENTIAL LEASE AGREEMENT</div>
        <div>San Francisco, California</div>
    </div>

    <div class="section">
        <div class="section-title">1. PARTIES</div>
        <p>This Lease Agreement ("Agreement") is entered into on <span class="field">{data['agreement_date']}</span></p>

        <p><strong>BETWEEN:</strong></p>
        <p>Landlord: <span class="field">{data['landlord_name']}</span></p>
        <p>Address: <span class="field">{data['landlord_address']}</span></p>
        <p>Phone: <span class="field">{data['landlord_phone']}</span></p>
        <p>Email: <span class="field">{data['landlord_email']}</span></p>
        <p>SSN: <span class="field">{data['landlord_ssn']}</span></p>

        <p><strong>AND:</strong></p>
        <p>Tenant: <span class="field">{data['tenant_name']}</span></p>
        <p>Current Address: <span class="field">{data['tenant_address']}</span></p>
        <p>Phone: <span class="field">{data['tenant_phone']}</span></p>
        <p>Email: <span class="field">{data['tenant_email']}</span></p>
        <p>SSN: <span class="field">{data['tenant_ssn']}</span></p>
        <p>Date of Birth: <span class="field">{data['tenant_dob']}</span></p>
    </div>

    <div class="section">
        <div class="section-title">2. PROPERTY</div>
        <p>The Landlord agrees to rent to the Tenant the following property:</p>
        <p>Address: <span class="field">{data['property_address']}</span></p>
        <p>Type: <span class="field">{data['property_type']}</span></p>
        <p>Square Footage: <span class="field">{data['square_footage']} sq ft</span></p>
    </div>

    <div class="section">
        <div class="section-title">3. TERM</div>
        <p>Lease Start Date: <span class="field">{data['start_date']}</span></p>
        <p>Lease End Date: <span class="field">{data['end_date']}</span></p>
        <p>Lease Duration: <span class="field">{data['duration']}</span></p>
    </div>

    <div class="section">
        <div class="section-title">4. RENT</div>
        <p>Monthly Rent: <span class="field">{data['monthly_rent']}</span></p>
        <p>Due Date: <span class="field">{data['due_date']}</span></p>
        <p>Payment Method: <span class="field">{data['payment_method']}</span></p>
        <p>Late Fee: <span class="field">{data['late_fee']}</span></p>
    </div>

    <div class="section">
        <div class="section-title">5. SECURITY DEPOSIT</div>
        <p>Amount: <span class="field">{data['deposit_amount']}</span></p>
        <p>Due Date: <span class="field">{data['deposit_due']}</span></p>
        <p>Bank Account: <span class="field">{data['bank_account']}</span></p>
    </div>

    <div class="section">
        <div class="section-title">6. UTILITIES</div>
        <table>
            <tr>
                <td><strong>Utility</strong></td>
                <td><strong>Responsibility</strong></td>
            </tr>
            <tr>
                <td>Electricity</td>
                <td>Tenant</td>
            </tr>
            <tr>
                <td>Gas</td>
                <td>Tenant</td>
            </tr>
            <tr>
                <td>Water/Sewer</td>
                <td>Landlord</td>
            </tr>
            <tr>
                <td>Internet/Cable</td>
                <td>Tenant</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">7. EMERGENCY CONTACT</div>
        <p>Name: <span class="field">{data['emergency_name']}</span></p>
        <p>Relationship: <span class="field">{data['emergency_relation']}</span></p>
        <p>Phone: <span class="field">{data['emergency_phone']}</span></p>
        <p>Address: <span class="field">{data['emergency_address']}</span></p>
    </div>

    <div class="section">
        <div class="section-title">8. EMPLOYER INFORMATION</div>
        <p>Employer: <span class="field">{data['employer_name']}</span></p>
        <p>Position: <span class="field">{data['position']}</span></p>
        <p>Monthly Income: <span class="field">{data['monthly_income']}</span></p>
        <p>Work Phone: <span class="field">{data['work_phone']}</span></p>
    </div>

    <div class="section">
        <div class="section-title">9. SIGNATURES</div>
        <p style="margin-top: 50px;">
            <strong>Landlord Signature:</strong><br>
            <span class="field">{data['landlord_name']}</span><br>
            Date: <span class="field">{data['sign_date']}</span>
        </p>

        <p style="margin-top: 30px;">
            <strong>Tenant Signature:</strong><br>
            <span class="field">{data['tenant_name']}</span><br>
            Date: <span class="field">{data['sign_date']}</span>
        </p>
    </div>

    <div class="section" style="margin-top: 50px; font-size: 12px;">
        <p><strong>Notary Public</strong></p>
        <p>Notary Name: <span class="field">{data['notary_name']}</span></p>
        <p>License Number: <span class="field">{data['notary_license']}</span></p>
        <p>Commission Expires: <span class="field">{data['notary_expiry']}</span></p>
    </div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Created: {output_path}")

def main():
    """Generate 10 lease agreements"""
    script_dir = Path(__file__).parent

    print("\nGenerating 10 Fake Lease Agreements...")
    print("=" * 60)

    for i in range(1, 11):
        data = generate_lease_data(i)
        output_path = script_dir / f"lease_{i:02d}_UNREDACTED.html"
        create_html(data, output_path)

    print("\nAll leases generated!")
    print(f"\nLocation: {script_dir}")
    print("\nNext steps:")
    print("1. Convert HTML to PDF using browser 'Print to PDF'")
    print("2. Or use a tool like wkhtmltopdf")
    print("3. Redact lease_01 using standard process")
    print("4. Use redacted lease_01 to teach the system")
    print("5. Batch redact leases 02-10")

if __name__ == "__main__":
    main()
