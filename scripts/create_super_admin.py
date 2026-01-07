import os
import sys
import asyncio
from sqlalchemy.orm import Session

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.core.security import get_password_hash
from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.permission import Permission
from app.models.objects.organization_type import OrganizationType
from app.models.relationships.role_permission import RolePermission
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.services.governance.crud.governance_crud import governance_rule_crud
from app.domains.services.governance.schemas.governance_rule import GovernanceRuleCreate


# 시스템에 필수적인 기본 권한들 정의
ESSENTIAL_PERMISSIONS = {
    "organization:create": "Create a new organization",
    "organizations:read": "Read the list of organizations",
    "organization_type:create": "Create a new organization type",
    "role:read": "Read role definitions",
    "role:update": "Update role definitions",
    "role:create": "Create a new role", # System_Admin 전용
    "role:delete": "Delete an existing role", # System_Admin 전용
    "role:assign_system": "Assign a system-level role to a user",
    "role:assign_organization": "Assign an organization-level role to a user",
    "permission:read": "Read permission definitions",
    "system:context_switch": "Allows switching to an organization context from the system context.",
}

# T0 역할 최대 인원 수 정의
MAX_PRIME_ADMIN = 3
MAX_SYSTEM_ADMIN = 2

async def create_initial_data():
    """
    개발/테스트 환경을 위해, 최상위 관리자 역할과 사용자를 생성합니다.
    """
    db: Session = SessionLocal()
    try:
        print("--- Starting Initial Data Setup ---")

        # 1. 기본 조직 유형 시딩
        print("Seeding default organization type...")
        org_type_name = "General Corporation"
        org_type = db.query(OrganizationType).filter(OrganizationType.name == org_type_name).first()
        if not org_type:
            print(f"Creating organization type: '{org_type_name}'...")
            db.add(OrganizationType(name=org_type_name, description="A standard corporate entity."))
            db.commit()

        # 2. 필수 권한 시딩
        print("Seeding essential permissions...")
        permission_objects = {}
        for name, desc in ESSENTIAL_PERMISSIONS.items():
            perm = db.query(Permission).filter(Permission.name == name).first()
            if not perm:
                print(f"Creating permission: '{name}'...")
                perm = Permission(name=name, description=desc)
                db.add(perm)
            permission_objects[name] = perm
        db.commit()
        print("Permission seeding complete.")

        # 3. 최상위 관리자 역할(T0) 정의, 권한 할당 및 인원수 설정
        roles_in_db = {}
        t0_role_configs = {
            "System_Admin": {"max_headcount": MAX_SYSTEM_ADMIN},
            "Prime_Admin": {"max_headcount": MAX_PRIME_ADMIN}
        }

        for role_name, config in t0_role_configs.items():
            role = db.query(Role).filter(Role.name == role_name, Role.scope == 'SYSTEM').first()
            if not role:
                print(f"Role '{role_name}' not found. Creating it...")
                role = Role(name=role_name, description=f"{role_name} for the system", scope='SYSTEM', tier=0, max_headcount=config['max_headcount'])
                db.add(role)
                db.commit()
                db.refresh(role)
            elif role.max_headcount != config['max_headcount']:
                print(f"Updating max_headcount for role '{role_name}'...")
                role.max_headcount = config['max_headcount']
                db.commit()

            roles_in_db[role_name] = role

            # 권한 할당
            print(f"Assigning permissions to '{role_name}'...")
            existing_perms = {rp.permission_id for rp in role.permissions}
            perms_to_add = []
            for perm_name, perm_obj in permission_objects.items():
                if perm_obj.id in existing_perms:
                    continue

                # 일반 권한 할당: 특별 취급 권한들은 제외
                if perm_name not in ["role:create", "role:delete", "system:context_switch"]:
                    perms_to_add.append(RolePermission(role_id=role.id, permission_id=perm_obj.id))

            # System_Admin에게만 role:create 및 role:delete 권한 부여
            if role_name == "System_Admin":
                if permission_objects["role:create"].id not in existing_perms:
                    perms_to_add.append(RolePermission(role_id=role.id, permission_id=permission_objects["role:create"].id))
                if permission_objects["role:delete"].id not in existing_perms:
                    perms_to_add.append(RolePermission(role_id=role.id, permission_id=permission_objects["role:delete"].id))
            
            # Prime_Admin에게만 system:context_switch 권한 부여
            if role_name == "Prime_Admin" and permission_objects["system:context_switch"].id not in existing_perms:
                perms_to_add.append(RolePermission(role_id=role.id, permission_id=permission_objects["system:context_switch"].id))

            if perms_to_add:
                db.bulk_save_objects(perms_to_add)
                db.commit()
                print(f"Assigned {len(perms_to_add)} new permissions to the role '{role_name}'.")

        # 4. 거버넌스 규칙 시딩 (T0 규칙)
        print("Seeding governance rules...")
        governance_rules = [

            # 규칙 2: System_Admin의 Prime_Admin 선임/해임 (일반 상황)
            GovernanceRuleCreate(
                rule_name="SystemAdminCanAssignPrimeAdmin",
                description=f"System_Admin은 Prime_Admin 수가 {MAX_PRIME_ADMIN}명 미만일 때 Prime_Admin 역할을 부여할 수 있습니다.",
                actor_role_id=roles_in_db["System_Admin"].id,
                action="assign_role",
                target_role_id=roles_in_db["Prime_Admin"].id,
                context="SYSTEM",
                allow=True, priority=50,
                conditions={"check_max_headcount": True}
            ),
            GovernanceRuleCreate(
                rule_name="SystemAdminCanRevokePrimeAdmin",
                description="System_Admin은 Prime_Admin 수가 1명을 초과할 때 Prime_Admin 역할을 해임할 수 있습니다.",
                actor_role_id=roles_in_db["System_Admin"].id,
                action="revoke_role",
                target_role_id=roles_in_db["Prime_Admin"].id,
                context="SYSTEM",
                allow=True, priority=50,
                conditions={"prime_admin_count": {"$gt": 1}}
            ),
            # 규칙 3: Prime_Admin의 System_Admin 관리
            GovernanceRuleCreate(
                rule_name="PrimeAdminCanAssignSystemAdmin",
                description=f"Prime_Admin은 System_Admin 수가 {MAX_SYSTEM_ADMIN}명 미만일 때 System_Admin 역할을 부여할 수 있습니다.",
                actor_role_id=roles_in_db["Prime_Admin"].id,
                action="assign_role",
                target_role_id=roles_in_db["System_Admin"].id,
                context="SYSTEM",
                allow=True, priority=50,
                conditions={"check_max_headcount": True}
            ),
            GovernanceRuleCreate(
                rule_name="PrimeAdminCannotRevokeSystemAdmin",
                description="Prime_Admin은 System_Admin 역할을 해임할 수 없습니다.",
                actor_role_id=roles_in_db["Prime_Admin"].id,
                action="revoke_role",
                target_role_id=roles_in_db["System_Admin"].id,
                context="SYSTEM",
                allow=False, priority=10
            ),
            # 규칙 4: Prime_Admin의 시스템 내 일반 역할 관리 (`tier > 1`, `scope=SYSTEM`)
            GovernanceRuleCreate(
                rule_name="PrimeAdminCanManageSystemTier2PlusRoles",
                description="Prime_Admin은 시스템 컨텍스트에서 tier가 1보다 큰 시스템 역할을 할당/해제할 수 있습니다.",
                actor_role_id=roles_in_db["Prime_Admin"].id,
                action="assign_role", # 이 규칙은 assign과 revoke 모두에 적용될 수 있도록 validator에서 처리
                context="SYSTEM", 
                allow=True, priority=100,
                conditions={"target_role_tier": {"$gt": 1}, "target_role_scope": "SYSTEM"}
            ),
            GovernanceRuleCreate(
                rule_name="PrimeAdminCanRevokeSystemTier2PlusRoles",
                description="Prime_Admin은 시스템 컨텍스트에서 tier가 1보다 큰 시스템 역할을 해제할 수 있습니다.",
                actor_role_id=roles_in_db["Prime_Admin"].id,
                action="revoke_role",
                context="SYSTEM",
                allow=True, priority=100,
                conditions={"target_role_tier": {"$gt": 1}, "target_role_scope": "SYSTEM"}
            ),


             # 규칙 7: 비상 모드 시 System_Admin에게 Prime_Admin 권한 대리 위임
            GovernanceRuleCreate(
                rule_name="SystemAdminDelegatedAsPrimeInEmergency",
                description="비상 모드에서 System_Admin은 Prime_Admin의 모든 권한을 위임받습니다.",
                actor_role_id=roles_in_db["System_Admin"].id,
                action="delegate_prime_admin_powers", # 이 액션은 evaluate_rule에서 특별 처리
                context="SYSTEM",
                allow=True, priority=5,
                conditions={"is_emergency_mode": True}
            ),
        ]

        for rule_in in governance_rules:
            # OrgAdminCanAssignOrgAdmin 규칙은 조직 생성 시 동적으로 처리해야 하므로 여기서는 건너뜁니다.
            if rule_in.rule_name == "OrgAdminCanAssignOrgAdmin":
                print("Skipping OrgAdminCanAssignOrgAdmin rule seeding. It should be created on organization creation.")
                continue

            rule = governance_rule_crud.get_by_rule_name(db, rule_name=rule_in.rule_name)
            if not rule:
                print(f"Creating governance rule: '{rule_in.rule_name}'...")
                governance_rule_crud.create(db, obj_in=rule_in)
        
        print("Governance rule seeding complete.")


        # 5. 초기 System_Admin 사용자 생성
        admin_email = "ypkim.gs@esgroup.net"
        admin_username = "yoonpyo"
        admin_password = "Yoonpyo04118!"
        user = db.query(User).filter(User.email == admin_email).first()
        if not user:
            print(f"User with email '{admin_email}' not found. Creating it...")
            hashed_password = get_password_hash(admin_password)
            user = User(
                email=admin_email, 
                username=admin_username, 
                password_hash=hashed_password, 
                is_active=True, 
                is_staff=True, 
                is_superuser=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 6. 사용자에게 System_Admin 역할 연결
        system_admin_role = roles_in_db["System_Admin"]
        assignment = db.query(UserOrganizationRole).filter(UserOrganizationRole.user_id == user.id, UserOrganizationRole.role_id == system_admin_role.id).first()
        if not assignment:
            print(f"Assigning 'System_Admin' role to user '{admin_username}'...")
            assignment = UserOrganizationRole(user_id=user.id, role_id=system_admin_role.id, organization_id=None)
            db.add(assignment)
            db.commit()

        # 7. 초기 Prime_Admin 사용자 생성
        prime_admin_email = "evenhorizon1129@gmail.com"
        prime_admin_username = "ypkim"
        prime_admin_password = "Yoonpyo04118!"
        prime_user = db.query(User).filter(User.email == prime_admin_email).first()
        if not prime_user:
            print(f"User with email '{prime_admin_email}' not found. Creating it...")
            hashed_password = get_password_hash(prime_admin_password)
            prime_user = User(
                email=prime_admin_email, 
                username=prime_admin_username, 
                password_hash=hashed_password, 
                is_active=True, 
                is_staff=True, 
                is_superuser=True
            )
            db.add(prime_user)
            db.commit()
            db.refresh(prime_user)

        # 8. 사용자에게 Prime_Admin 역할 연결
        prime_admin_role = roles_in_db["Prime_Admin"]
        prime_assignment = db.query(UserOrganizationRole).filter(UserOrganizationRole.user_id == prime_user.id, UserOrganizationRole.role_id == prime_admin_role.id).first()
        if not prime_assignment:
            print(f"Assigning 'Prime_Admin' role to user '{prime_admin_username}'...")
            prime_assignment = UserOrganizationRole(user_id=prime_user.id, role_id=prime_admin_role.id, organization_id=None)
            db.add(prime_assignment)
            db.commit()

        print("--- Initial Data Setup Complete ---")

    except Exception as e:
        print(f"An error occurred during initial data setup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_initial_data())