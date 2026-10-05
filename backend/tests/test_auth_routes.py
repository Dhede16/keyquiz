from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.api.routes_auth import RegisterAdminRequest, register_user_admin


class RegisterUserAdminTests(TestCase):
    def setUp(self):
        self.payload = RegisterAdminRequest(
            email="  New.User@example.com ",
            password="secure-password",
            name="  New User  ",
            role="teacher",
        )
        self.admin = Mock()
        self.admin.auth.admin.create_user.return_value = SimpleNamespace(
            user=SimpleNamespace(id="new-user-id")
        )

    def test_register_confirms_account_and_never_saves_password(self):
        with patch("app.api.routes_auth.get_supabase_admin", return_value=self.admin):
            result = register_user_admin(self.payload)

        self.admin.auth.admin.create_user.assert_called_once_with(
            {
                "email": "new.user@example.com",
                "password": "secure-password",
                "email_confirm": True,
                "user_metadata": {"name": "New User", "role": "teacher"},
            }
        )
        self.admin.table.assert_called_once_with("profiles")
        profile = self.admin.table.return_value.upsert.call_args.args[0]
        self.assertEqual(
            profile,
            {
                "id": "new-user-id",
                "email": "new.user@example.com",
                "name": "New User",
                "role": "teacher",
            },
        )
        self.assertEqual(result["status"], "success")

    def test_duplicate_email_is_rejected_without_changing_existing_account(self):
        self.admin.auth.admin.create_user.side_effect = Exception(
            "User already registered"
        )
        with patch("app.api.routes_auth.get_supabase_admin", return_value=self.admin):
            with self.assertRaises(HTTPException) as raised:
                register_user_admin(self.payload)

        self.assertEqual(raised.exception.status_code, 409)
        self.admin.auth.admin.update_user_by_id.assert_not_called()
        self.admin.auth.admin.list_users.assert_not_called()
        self.admin.table.assert_not_called()

    def test_registration_rejects_invalid_email_role_and_short_password(self):
        for changes in (
            {"email": "not-an-email"},
            {"role": "admin"},
            {"password": "123"},
        ):
            with self.subTest(changes=changes):
                values = {
                    "email": "person@example.com",
                    "password": "secure-password",
                    "name": "Person",
                    "role": "student",
                }
                values.update(changes)
                with self.assertRaises(ValidationError):
                    RegisterAdminRequest(**values)
