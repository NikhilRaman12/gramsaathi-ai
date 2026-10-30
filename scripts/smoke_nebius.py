"""One real Token Factory inference request; requires NEBIUS_API_KEY."""

from __future__ import annotations

import sys

from scripts.generator import NebiusProvider, ProviderError


def main() -> int:
    provider = NebiusProvider()
    try:
        provider.verify_model_access()
        answer = provider.generate(
            [
                {
                    "role": "user",
                    "content": "Reply with exactly: Gramsaathi One live inference verified.",
                }
            ]
        )
    except ProviderError as exc:
        print(f"Live Nebius inference failed: {exc}", file=sys.stderr)
        return 1
    print(f"Live Nebius inference succeeded with {provider.model}.")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
