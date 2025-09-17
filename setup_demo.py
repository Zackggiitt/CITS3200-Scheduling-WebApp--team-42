#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示环境设置脚本
包含所有必要的测试数据和用户账户创建
"""

import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application import app, db
from models import User, Unit, Module, Session, Facilitator, Unavailability

def setup_demo_environment():
    """设置完整的演示环境"""
    print("开始设置演示环境...")
    
    with app.app_context():
        # 1. 清理现有数据
        print("清理现有数据...")
        db.drop_all()
        db.create_all()
        
        # 2. 创建管理员用户
        print("创建管理员用户...")
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        db.session.add(admin_user)
        
        # 3. 创建Unit Coordinator用户
        print("创建Unit Coordinator用户...")
        uc_user = User(
            username='unitcoordinator',
            email='uc@example.com',
            password_hash=generate_password_hash('uc123'),
            role='unit_coordinator',
            first_name='Unit',
            last_name='Coordinator'
        )
        db.session.add(uc_user)
        
        # 4. 创建测试单元
        print("创建测试单元...")
        test_unit = Unit(
            unit_code='TEST101',
            unit_name='Test Unit for Demo',
            semester='Semester 2',
            year=2024
        )
        db.session.add(test_unit)
        
        eeg_unit = Unit(
            unit_code='EEG110',
            unit_name='Engineering Graphics',
            semester='Semester 2', 
            year=2024
        )
        db.session.add(eeg_unit)
        
        db.session.commit()
        
        # 5. 将UC分配到TEST101单元
        print("分配Unit Coordinator到TEST101单元...")
        uc_user.units.append(test_unit)
        
        # 6. 创建模块
        print("创建模块...")
        modules = []
        for i in range(1, 4):
            module = Module(
                module_name=f'Module {i}',
                unit_id=test_unit.id
            )
            modules.append(module)
            db.session.add(module)
        
        db.session.commit()
        
        # 7. 创建facilitators
        print("创建facilitators...")
        facilitators = []
        facilitator_names = [
            ('Alice', 'Johnson'),
            ('Bob', 'Smith'), 
            ('Carol', 'Davis'),
            ('David', 'Wilson'),
            ('Emma', 'Brown'),
            ('Frank', 'Miller'),
            ('Grace', 'Taylor'),
            ('Henry', 'Anderson')
        ]
        
        for first_name, last_name in facilitator_names:
            username = f'{first_name.lower()}.{last_name.lower()}'
            facilitator_user = User(
                username=username,
                email=f'{username}@example.com',
                password_hash=generate_password_hash('facilitator123'),
                role='facilitator',
                first_name=first_name,
                last_name=last_name
            )
            db.session.add(facilitator_user)
            db.session.commit()
            
            facilitator = Facilitator(
                user_id=facilitator_user.id,
                employee_id=f'EMP{1000 + len(facilitators)}',
                max_hours_per_week=20
            )
            facilitators.append(facilitator)
            db.session.add(facilitator)
        
        db.session.commit()
        
        # 8. 创建会话
        print("创建测试会话...")
        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        sessions = []
        for i in range(10):
            # 分布在不同的日期和时间
            day_offset = i % 5  # 5天内
            hour_offset = (i // 5) * 2  # 每天2个时间段
            
            session_date = base_date + timedelta(days=day_offset, hours=hour_offset)
            
            session = Session(
                session_name=f'Tutorial {i+1}',
                session_type='Tutorial',
                start_time=session_date,
                end_time=session_date + timedelta(hours=2),
                venue=f'Room {101 + i}',
                capacity=25,
                unit_id=test_unit.id,
                module_id=modules[i % len(modules)].id
            )
            sessions.append(session)
            db.session.add(session)
        
        db.session.commit()
        
        # 9. 创建一些unavailability数据（模拟真实情况）
        print("创建unavailability数据...")
        for i, facilitator in enumerate(facilitators[:4]):  # 前4个facilitator有一些不可用时间
            # 每个facilitator在某些时间段不可用
            unavail_date = base_date + timedelta(days=i % 3)
            unavailability = Unavailability(
                facilitator_id=facilitator.id,
                start_time=unavail_date,
                end_time=unavail_date + timedelta(hours=2),
                reason='Personal appointment'
            )
            db.session.add(unavailability)
        
        db.session.commit()
        
        print("演示环境设置完成！")
        print("\n=== 登录信息 ===")
        print("管理员账户:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\nUnit Coordinator账户:")
        print("  用户名: unitcoordinator")
        print("  密码: uc123")
        print("\nFacilitator账户 (示例):")
        print("  用户名: alice.johnson")
        print("  密码: facilitator123")
        print("\n=== 测试数据 ===")
        print(f"创建了 {len(facilitators)} 个facilitators")
        print(f"创建了 {len(sessions)} 个测试会话")
        print(f"TEST101单元包含 {len(modules)} 个模块")
        print("\n可以使用Unit Coordinator账户登录并测试Auto Assign功能！")

if __name__ == '__main__':
    setup_demo_environment()