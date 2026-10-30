import unittest

from app import render_response, render_pm_kisan_screen


class UiTests(unittest.TestCase):
    def test_no_evidence_state_is_visible(self):
        markup = render_response(
            {
                "status": "no_evidence",
                "message": "No matching source.",
                "summary": [],
                "action_plan": [],
                "evidence": [],
            }
        )
        self.assertIn("No matching source.", markup)
        self.assertIn("Evidence-based guidance", render_response({"status": "ok"}))

    def test_model_and_source_text_are_escaped_and_http_links_are_rendered(self):
        markup = render_response(
            {
                "status": "ok",
                "summary": [{"text": "<script>alert(1)</script>", "source_ids": ["S1"]}],
                "action_plan": [],
                "evidence": [
                    {
                        "id": "S1",
                        "source_title": "PM-KISAN",
                        "source_file": "data/samman_nidhi_pm.pdf",
                        "page": 2,
                        "text": "source <script> text",
                        "source_urls": ["https://pmkisan.gov.in/", "javascript:alert(1)"],
                    }
                ],
            }
        )
        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)
        self.assertIn('href="https://pmkisan.gov.in/"', markup)
        self.assertNotIn("javascript:", markup)

    def test_screen_output_links_official_source_and_keeps_warning(self):
        markup = render_pm_kisan_screen(*(["Not sure / पता नहीं"] * 10))
        self.assertIn("https://pmkisan.gov.in/", markup)
        self.assertIn("More information needed", markup)
        self.assertIn("not an official eligibility or payment decision", markup)


if __name__ == "__main__":
    unittest.main()
