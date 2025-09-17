#!/usr/bin/env python3

from application import app
from models import db, User, Unit, UnitFacilitator

def fix_uc_units():
    with app.app_context():
        # 获取UC用户
        uc_user = User.query.filter_by(email='uc_demo@example.com').first()
        if not uc_user:
            
            return
        
        print(f"UC用户ID: {uc_user.id}")
        
        # 获取所有单元
        all_units = Unit.query.all()
        
        
        # 检查UC用户当前关联的单元（作为facilitator）
        current_associations = UnitFacilitator.query.filter_by(user_id=uc_user.id).all()
        current_unit_ids = [assoc.unit_id for assoc in current_associations]
       
        
        # 为UC用户分配所有单元（作为facilitator，这样可以看到单元）
        added_count = 0
        for unit in all_units:
            if unit.id not in current_unit_ids:
                unit_facilitator = UnitFacilitator(user_id=uc_user.id, unit_id=unit.id)
                db.session.add(unit_facilitator)
              
                added_count += 1
        
        if added_count > 0:
            db.session.commit()
        
        else:
            print("UC用户已经关联了所有单元")
        
        # 验证结果
        final_associations = UnitFacilitator.query.filter_by(user_id=uc_user.id).all()
       
if __name__ == '__main__':
    fix_uc_units()