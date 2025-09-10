#!/usr/bin/env python3
"""
Directly injects sample facilitator data into the uc.js file for the attendance summary section.
"""

import re
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

def generate_sample_facilitator_data(num_facilitators: int = 12) -> List[Dict[str, Any]]:
    """
    Generate sample facilitator data for the attendance summary.
    
    Args:
        num_facilitators: Number of facilitators to generate
        
    Returns:
        List of facilitator dictionaries with attendance data
    """
    
    # Sample facilitator names
    first_names = [
        "John", "Sarah", "Mike", "Lisa", "David", "Emma", "Alex", "Maria",
        "James", "Sophie", "Ryan", "Olivia", "Tom", "Anna", "Chris", "Nina",
        "Mark", "Elena", "Paul", "Kate", "Steve", "Maya", "Ben", "Zoe"
    ]
    
    last_names = [
        "Smith", "Johnson", "Davis", "Wilson", "Brown", "Rodriguez", "Chen", "Garcia",
        "Martinez", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris", "Martin",
        "Thompson", "Moore", "Young", "Allen", "King", "Wright", "Scott", "Torres"
    ]
    
    # Status options relevant to facilitators
    statuses = [
        {"name": "Active", "color": "green", "bg": "green"},
        {"name": "Available", "color": "blue", "bg": "blue"},
        {"name": "Assigned", "color": "purple", "bg": "purple"},
        {"name": "On Duty", "color": "orange", "bg": "orange"}
    ]
    
    facilitators = []
    
    for i in range(num_facilitators):
        # Generate random name
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        name = f"{first_name} {last_name}"
        
        # Generate random session count (1-10)
        session_count = random.randint(1, 10)
        
        # Generate random assigned hours (1-8)
        assigned_hours = random.randint(1, 8)
        
        # Generate total hours (assigned_hours + 0-3 extra)
        total_hours = assigned_hours + random.randint(0, 3)
        
        # Select random status
        status = random.choice(statuses)
        
        # Generate random date within the current week
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        random_day = week_start + timedelta(days=random.randint(0, 6))
        date_str = random_day.strftime("%Y-%m-%d")
        
        facilitator = {
            "name": name,
            "session_count": session_count,
            "status": status["name"],
            "status_color": status["color"],
            "status_bg": status["bg"],
            "assigned_hours": assigned_hours,
            "total_hours": total_hours,
            "date": date_str,
            "email": f"{first_name.lower()}.{last_name.lower()}@university.edu",
            "phone": f"04{random.randint(10000000, 99999999)}"
        }
        
        facilitators.append(facilitator)
    
    return facilitators

def generate_javascript_data(facilitators: List[Dict[str, Any]]) -> str:
    """
    Generate JavaScript code to inject the facilitator data.
    
    Args:
        facilitators: List of facilitator dictionaries
        
    Returns:
        JavaScript code as string
    """
    
    js_code = "  // Sample facilitator data for attendance summary\n"
    js_code += "  const sampleFacilitatorData = [\n"
    
    for i, facilitator in enumerate(facilitators):
        js_code += f"    {{\n"
        js_code += f"      name: \"{facilitator['name']}\",\n"
        js_code += f"      session_count: {facilitator['session_count']},\n"
        js_code += f"      status: \"{facilitator['status']}\",\n"
        js_code += f"      status_color: \"{facilitator['status_color']}\",\n"
        js_code += f"      status_bg: \"{facilitator['status_bg']}\",\n"
        js_code += f"      assigned_hours: {facilitator['assigned_hours']},\n"
        js_code += f"      total_hours: {facilitator['total_hours']},\n"
        js_code += f"      date: \"{facilitator['date']}\",\n"
        js_code += f"      email: \"{facilitator['email']}\",\n"
        js_code += f"      phone: \"{facilitator['phone']}\"\n"
        js_code += f"    }}{',' if i < len(facilitators) - 1 else ''}\n"
    
    js_code += "  ];\n\n"
    js_code += "  // Inject sample data into attendance summary\n"
    js_code += "  if (window.__attData) {\n"
    js_code += "    window.__attData.sampleFacilitators = sampleFacilitatorData;\n"
    js_code += "    console.log('Sample facilitator data injected:', sampleFacilitatorData.length, 'facilitators');\n"
    js_code += "  }\n\n"
    js_code += "  // Auto-populate attendance summary if empty\n"
    js_code += "  setTimeout(() => {\n"
    js_code += "    const tableBody = document.querySelector('#activityLogCard .max-h-80.overflow-y-auto.divide-y');\n"
    js_code += "    if (tableBody && tableBody.textContent.includes('No facilitator data available')) {\n"
    js_code += "      console.log('Auto-populating attendance summary with sample data...');\n"
    js_code += "      renderActivityLog(sampleFacilitatorData);\n"
    js_code += "    }\n"
    js_code += "  }, 1000);\n"
    
    return js_code

def inject_into_js_file(js_file_path: str = "static/js/uc.js") -> None:
    """
    Inject sample data directly into the uc.js file.
    
    Args:
        js_file_path: Path to the uc.js file
    """
    
    print("Generating sample facilitator data...")
    facilitators = generate_sample_facilitator_data()
    
    print(f"Generated {len(facilitators)} facilitators")
    
    # Generate JavaScript code
    js_code = generate_javascript_data(facilitators)
    
    try:
        # Read the current uc.js file
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove any existing sample data injection
        pattern = r'  // Sample facilitator data for attendance summary.*?  }, 1000\);\n'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Find the end of the file (before the last closing brace if any)
        # Insert our code before the end
        if content.strip().endswith('}'):
            # Insert before the last closing brace
            content = content.rstrip()[:-1] + js_code + '\n}'
        else:
            # Just append to the end
            content += '\n' + js_code
        
        # Write back to file
        with open(js_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Successfully injected data into {js_file_path}")
        print("Attendance summary will auto-populate with sample data")
        
        # Print sample of generated data
        print("\nSample Generated Data:")
        print("-" * 50)
        for i, facilitator in enumerate(facilitators[:5]):
            print(f"{i+1:2d}. {facilitator['name']:<20} | "
                  f"{facilitator['status']:<10} | "
                  f"{facilitator['assigned_hours']:2d}h/{facilitator['total_hours']:2d}h")
        
        if len(facilitators) > 5:
            print(f"    ... and {len(facilitators) - 5} more facilitators")
        
    except FileNotFoundError:
        print(f"Error: {js_file_path} not found!")
        print("Make sure you're running this script from the project root directory")
    except Exception as e:
        print(f"Error injecting data: {e}")

def main():
    """
    Main function to inject attendance summary data.
    """
    print("Attendance Summary Data Injector")
    print("=" * 50)
    
    # Inject data into uc.js
    inject_into_js_file()
    
    print("\n" + "=" * 50)
    print("Data injection complete!")
    print("Refresh your dashboard to see the sample data")
    print("The attendance summary will auto-populate when empty")
    print("=" * 50)

if __name__ == "__main__":
    main()