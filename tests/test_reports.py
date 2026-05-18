from django.test import TestCase
from users.services import (
    get_content_analytics, format_analytics_for_csv, _strip_pii, PII_COLUMNS
)


class PIIAnonymizationTest(TestCase):

    def test_get_content_analytics_returns_no_pii_fields(self):
        data = get_content_analytics()
        for row in data:
            for col in row:
                self.assertNotIn(col, PII_COLUMNS,
                                 f"PII column '{col}' found in analytics data")

    def test_format_analytics_never_contains_pii(self):
        rows = [
            {
                'title': 'Test',
                'username': 'john_doe',
                'email': 'john@example.com',
                'ip_address': '192.168.1.1',
            }
        ]
        result = format_analytics_for_csv(rows, is_b2b_report=False)
        for row in result:
            self.assertNotIn('username', row)
            self.assertNotIn('email', row)
            self.assertNotIn('ip_address', row)
            self.assertIn('title', row)

    def test_b2b_mode_hashes_username(self):
        rows = [
            {'title': 'Test', 'username': 'john_doe', 'email': 'john@example.com'}
        ]
        result = format_analytics_for_csv(rows, is_b2b_report=True)
        row = result[0]
        self.assertTrue(row['username'].startswith('USER_'))
        self.assertEqual(len(row['username']), 15)
        self.assertNotIn('email', row)

    def test_strip_pii_removes_all_sensitive_fields(self):
        row = {'title': 'Movie', 'username': 'user', 'email': 'a@b.com', 'location': 'NYC'}
        clean = _strip_pii(row)
        self.assertIn('title', clean)
        self.assertNotIn('username', clean)
        self.assertNotIn('email', clean)
        self.assertNotIn('location', clean)

    def test_pii_columns_contains_expected_fields(self):
        self.assertIn('username', PII_COLUMNS)
        self.assertIn('email', PII_COLUMNS)
        has_ip = 'ip_address' in PII_COLUMNS or 'id_address' in PII_COLUMNS
        self.assertTrue(has_ip)
