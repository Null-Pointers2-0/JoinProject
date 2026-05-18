from django.test import TestCase
from users.services import (
    get_content_analytics, format_analytics_for_csv, _strip_pii, PII_COLUMNS,
    GDPR_ANONYMIZE_FIELDS, anonymize_user_id, validate_gdpr_compliance,
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

    def test_b2b_mode_anonymizes_gdpr_fields(self):
        rows = [
            {'title': 'Test', 'username': 'john_doe', 'email': 'john@example.com',
             'first_name': 'John', 'last_name': 'Doe'}
        ]
        result = format_analytics_for_csv(rows, is_b2b_report=True)
        row = result[0]
        self.assertTrue(row['username'].startswith('UID_'))
        self.assertEqual(len(row['username']), 16)
        self.assertTrue(row['email'].startswith('UID_'))
        self.assertTrue(row['first_name'].startswith('UID_'))
        self.assertTrue(row['last_name'].startswith('UID_'))

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


class GDPRComplianceTest(TestCase):

    def test_anonymize_user_id_is_deterministic(self):
        uid1 = anonymize_user_id('john_doe')
        uid2 = anonymize_user_id('john_doe')
        self.assertEqual(uid1, uid2)

    def test_anonymize_user_id_produces_different_ids_for_different_inputs(self):
        uid1 = anonymize_user_id('john_doe')
        uid2 = anonymize_user_id('jane_doe')
        self.assertNotEqual(uid1, uid2)

    def test_anonymize_user_id_prefix(self):
        uid = anonymize_user_id('test_user')
        self.assertTrue(uid.startswith('UID_'))

    def test_validate_gdpr_compliance_passes_for_clean_data(self):
        data = [{'title': 'Movie', 'views': 10}]
        validate_gdpr_compliance(data)

    def test_validate_gdpr_compliance_raises_on_pii_columns(self):
        data = [{'title': 'Movie', 'username': 'john_doe'}]
        with self.assertRaises(ValueError) as ctx:
            validate_gdpr_compliance(data)
        self.assertIn('GDPR violation', str(ctx.exception))

    def test_validate_gdpr_compliance_raises_on_email_in_values(self):
        data = [{'title': 'Movie', 'note': 'contact john@example.com for info'}]
        with self.assertRaises(ValueError) as ctx:
            validate_gdpr_compliance(data)
        self.assertIn('GDPR violation', str(ctx.exception))

    def test_validate_gdpr_compliance_b2b_raises_on_non_anonymized(self):
        data = [{'username': 'john_doe'}]
        with self.assertRaises(ValueError) as ctx:
            validate_gdpr_compliance(data, is_b2b_report=True)
        self.assertIn('GDPR violation', str(ctx.exception))

    def test_validate_gdpr_compliance_b2b_passes_with_uid_prefix(self):
        data = [{'username': 'UID_abc123def456'}]
        validate_gdpr_compliance(data, is_b2b_report=True)

    def test_gdpr_anonymize_fields_contains_expected(self):
        self.assertIn('username', GDPR_ANONYMIZE_FIELDS)
        self.assertIn('email', GDPR_ANONYMIZE_FIELDS)
        self.assertIn('first_name', GDPR_ANONYMIZE_FIELDS)
        self.assertIn('last_name', GDPR_ANONYMIZE_FIELDS)
