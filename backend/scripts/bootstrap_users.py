#!/usr/bin/env python3
"""
FinRecon User Account Management & Provisioning CLI.
Safely provisions and manages user accounts with Argon2id password hashing.
Preserves all reconciliation data and SQLite transactions.
"""

import sys
import os
import argparse

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import get_db_connection, init_db
from app.services.auth_service import auth_service
from app.models.schemas import UserRoleEnum

def list_users():
    """List all registered users in the FinRecon database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, role, full_name, is_active, failed_login_attempts, locked_until, created_at, updated_at
        FROM users
        ORDER BY created_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    print("\n" + "=" * 80)
    print("FINRECON REGISTERED USER ACCOUNTS")
    print("=" * 80)
    if not rows:
        print("No users found.")
        return

    print(f"{'ID':<16} {'USERNAME':<20} {'ROLE':<12} {'ACTIVE':<8} {'ATTEMPTS':<10} {'FULL NAME'}")
    print("-" * 80)
    for r in rows:
        active_str = "YES" if r["is_active"] else "NO"
        attempts_str = str(r["failed_login_attempts"])
        if r["locked_until"]:
            attempts_str += " (LOCKED)"
        print(f"{r['id']:<16} {r['username']:<20} {r['role']:<12} {active_str:<8} {attempts_str:<10} {r['full_name'] or ''}")
    print("=" * 80 + "\n")

def create_or_update_user(username: str, password: str, role: str, full_name: str = None):
    """Create a new user or update an existing user's password and role."""
    norm_role = role.upper()
    if norm_role not in [UserRoleEnum.USER.value, UserRoleEnum.SUPERVISOR.value, UserRoleEnum.ANALYST.value]:
        print(f"Error: Invalid role '{role}'. Must be USER or SUPERVISOR.")
        sys.exit(1)

    existing = auth_service.get_user_by_username(username)
    if existing:
        conn = get_db_connection()
        cursor = conn.cursor()
        pw_hash = auth_service.hash_password(password)
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, role = ?, full_name = COALESCE(?, full_name),
                failed_login_attempts = 0, locked_until = NULL, is_active = 1,
                updated_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (pw_hash, norm_role, full_name, existing["id"]))
        conn.commit()
        conn.close()
        print(f"[OK] Successfully updated user '{username}' (Role: {norm_role}).")
    else:
        user = auth_service.create_user(
            username=username,
            password=password,
            role=norm_role,
            full_name=full_name
        )
        print(f"[OK] Successfully created user '{username}' (ID: {user['id']}, Role: {norm_role}).")

def reset_defaults():
    """Ensure standard demo accounts are present."""
    auth_service.ensure_demo_accounts()
    print("[OK] Default demo accounts verified/re-provisioned.")
    list_users()

def main():
    parser = argparse.ArgumentParser(description="FinRecon User Management Utility")
    parser.add_argument("--list", action="store_true", help="List all users")
    parser.add_argument("--create", action="store_true", help="Create or update user")
    parser.add_argument("--username", type=str, help="Username to create/update")
    parser.add_argument("--password", type=str, help="Password for user")
    parser.add_argument("--role", type=str, choices=["USER", "SUPERVISOR", "ANALYST"], default="USER", help="Role")
    parser.add_argument("--name", type=str, default=None, help="Full name of user")
    parser.add_argument("--reset-defaults", action="store_true", help="Reset/re-provision default demo accounts")

    args = parser.parse_args()

    init_db()

    if args.list:
        list_users()
    elif args.reset_defaults:
        reset_defaults()
    elif args.create:
        if not args.username or not args.password:
            print("Error: --username and --password are required when using --create")
            sys.exit(1)
        create_or_update_user(args.username, args.password, args.role, args.name)
    else:
        list_users()

if __name__ == "__main__":
    main()
