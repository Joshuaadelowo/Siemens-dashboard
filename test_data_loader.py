import unittest
from datetime import datetime

from data_loader import InvalidCampusDataError, load_monthly_records


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.records = load_monthly_records()

    def test_returns_twelve_months(self):
        self.assertEqual(len(self.records), 12)

    def test_first_month_values(self):
        first = self.records[0]
        self.assertEqual(first.date, datetime(2025, 8, 1))
        self.assertEqual(first.month_label, "Aug 2025")
        self.assertEqual(first.electricity_kwh, 138192.0)
        self.assertEqual(first.gas_kwh, 1932.22)
        self.assertEqual(first.water_m3, 103394.0)
        self.assertAlmostEqual(first.carbon_tonnes, 64.53, places=1)
        self.assertAlmostEqual(first.homes_equivalent, 921.28, places=1)

    def test_last_month_values(self):
        last = self.records[-1]
        self.assertEqual(last.month_label, "Jul 2026")
        self.assertEqual(last.electricity_kwh, 125525.0)
        self.assertEqual(last.gas_kwh, 2373.71)
        self.assertAlmostEqual(last.carbon_tonnes, 55.55, places=1)

    def test_rejects_dummy_shaped_data(self, tmp_path=None):
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "siemens_data.json"
            bad_path.write_text(json.dumps({"timestamp": "x", "status": "ok", "sample_reading": 1}))
            with self.assertRaises(InvalidCampusDataError):
                load_monthly_records(bad_path)


if __name__ == "__main__":
    unittest.main()
