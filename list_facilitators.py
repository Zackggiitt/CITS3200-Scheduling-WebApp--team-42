#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, User, UserRole, UnitFacilitator, Unavailability
from application import app

def list_facilitators():
    with app.app_context():
        # Find all facilitators
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
        
        print(f"📋 Found {len(facilitators)} facilitators:")
        print()
        
        for facilitator in facilitators:
            print(f"✅ {facilitator.email}")
            print(f"   Name: {facilitator.first_name} {facilitator.last_name}")
            print(f"   Skills: {facilitator.skills_with_levels}")
            
            # Check unit associations
            unit_associations = UnitFacilitator.query.filter_by(user_id=facilitator.id).all()
            print(f"   Units: {[assoc.unit_id for assoc in unit_associations]}")
            
            # Check unavailability records
            unavailability_count = Unavailability.query.filter_by(user_id=facilitator.id).count()
            print(f"   Unavailability records: {unavailability_count}")
            print()

if __name__ == "__main__":
    list_facilitators()