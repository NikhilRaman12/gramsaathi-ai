import unittest
from unittest.mock import Mock

import requests

from scripts.generator import (
    NebiusProvider,
    ProviderConfigurationError,
    ProviderProtocolError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


def response(status, content=None, headers=None):
    item = Mock()
    item.status_code = status
    item.headers = headers or {}
    item.json.return_value = content
    return item


class ProviderTests(unittest.TestCase):
    def test_success_uses_openai_compatible_endpoint_and_bearer_key(self):
        session = Mock()
        session.post.return_value = response(
            200,
            {"choices": [{"message": {"content": "Grounded answer"}}]},
        )
        provider = NebiusProvider(api_key="test-key", model="nvidia/test", session=session)
        result = provider.generate([{"role": "user", "content": "hello"}])
        self.assertEqual(result, "Grounded answer")
        args, kwargs = session.post.call_args
        self.assertEqual(args[0], "https://api.tokenfactory.nebius.com/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["model"], "nvidia/test")
        self.assertGreater(kwargs["timeout"], 0)

    def test_missing_credentials_fail_without_network_call(self):
        session = Mock()
        provider = NebiusProvider(api_key="", session=session)
        with self.assertRaises(ProviderConfigurationError):
            provider.generate([{"role": "user", "content": "hello"}])
        session.post.assert_not_called()

    def test_timeout_is_reported_without_replaying_generation(self):
        session = Mock()
        session.post.side_effect = requests.Timeout()
        provider = NebiusProvider(api_key="test-key", session=session)
        with self.assertRaises(ProviderTimeoutError):
            provider.generate([{"role": "user", "content": "hello"}])
        self.assertEqual(session.post.call_count, 1)

    def test_rate_limit_retries_once_when_retry_after_is_short(self):
        session = Mock()
        session.post.side_effect = [
            response(429, headers={"Retry-After": "0"}),
            response(200, {"choices": [{"message": {"content": "ok"}}]}),
        ]
        provider = NebiusProvider(api_key="test-key", session=session, sleeper=lambda _: None)
        self.assertEqual(provider.generate([{"role": "user", "content": "hello"}]), "ok")
        self.assertEqual(session.post.call_count, 2)

    def test_long_rate_limit_window_is_not_retried_early(self):
        session = Mock()
        session.post.return_value = response(429, headers={"Retry-After": "60"})
        provider = NebiusProvider(api_key="test-key", session=session, sleeper=lambda _: None)
        with self.assertRaises(ProviderRateLimitError):
            provider.generate([{"role": "user", "content": "hello"}])
        self.assertEqual(session.post.call_count, 1)

    def test_auth_failure_and_malformed_response_are_safe_errors(self):
        session = Mock()
        session.post.return_value = response(401)
        provider = NebiusProvider(api_key="test-key", session=session)
        with self.assertRaises(ProviderConfigurationError):
            provider.generate([{"role": "user", "content": "hello"}])
        session.post.return_value = response(200, {"choices": []})
        with self.assertRaises(ProviderProtocolError):
            provider.generate([{"role": "user", "content": "hello"}])

    def test_live_catalog_verification_checks_exact_model_id(self):
        session = Mock()
        catalog = response(200, {"object": "list", "data": [{"id": "nvidia/Nemotron-3_5-Lightning"}]})
        session.get.return_value = catalog
        provider = NebiusProvider(
            api_key="mocked-test-only",
            model="nvidia/Nemotron-3_5-Lightning",
            session=session,
        )
        self.assertEqual(provider.verify_model_access(), "nvidia/Nemotron-3_5-Lightning")
        args, kwargs = session.get.call_args
        self.assertEqual(args[0], "https://api.tokenfactory.nebius.com/v1/models")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer mocked-test-only")

    def test_catalog_rejects_model_not_available_to_key(self):
        session = Mock()
        session.get.return_value = response(200, {"data": [{"id": "nvidia/another-model"}]})
        provider = NebiusProvider(
            api_key="mocked-test-only",
            model="nvidia/Nemotron-3_5-Lightning",
            session=session,
        )
        with self.assertRaises(ProviderConfigurationError):
            provider.verify_model_access()


if __name__ == "__main__":
    unittest.main()
