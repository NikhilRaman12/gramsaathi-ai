import unittest

from scripts.eligibility import ALL_FIELDS, RULE_SOURCE_URL, check_pm_kisan


def complete_answers(value="No"):
    answers = {name: value for name in ALL_FIELDS}
    answers["landholding_farmer"] = "Yes"
    return answers


class EligibilityTests(unittest.TestCase):
    def test_unknown_fields_remain_unknown_and_are_asked(self):
        result = check_pm_kisan({})
        self.assertEqual(result["status"], "needs_more_information")
        self.assertTrue(result["missing_information"])
        self.assertEqual(result["source_url"], RULE_SOURCE_URL)

    def test_exclusion_is_a_preliminary_flag_not_final_decision(self):
        answers = complete_answers()
        answers["income_tax_payer"] = "Yes"
        result = check_pm_kisan(answers)
        self.assertEqual(result["status"], "possible_exclusion")
        self.assertIn("income_tax_payer", result["matched_exclusions"])
        self.assertIn("not an official decision", result["message"])

    def test_complete_answers_without_listed_exclusion_do_not_claim_eligibility(self):
        result = check_pm_kisan(complete_answers())
        self.assertEqual(result["status"], "no_listed_exclusion_found")
        self.assertIn("does not confirm", result["message"])

    def test_recent_land_or_multiple_recipients_are_cautions_not_exclusions(self):
        answers = complete_answers()
        answers["ownership_after_2019_02_01"] = "Yes"
        answers["multiple_family_recipients"] = "Yes"
        result = check_pm_kisan(answers)
        self.assertEqual(result["status"], "no_listed_exclusion_found")
        self.assertEqual(len(result["cautions"]), 2)
        self.assertEqual(result["matched_exclusions"], [])

    def test_missing_landholding_requirement_is_not_presented_as_approval(self):
        answers = complete_answers()
        answers["landholding_farmer"] = "No"
        result = check_pm_kisan(answers)
        self.assertEqual(result["status"], "landholding_requirement_not_confirmed")


if __name__ == "__main__":
    unittest.main()
