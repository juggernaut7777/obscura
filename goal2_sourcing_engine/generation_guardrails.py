"""
generation_guardrails.py — Generation Guardrail Engine for OBSCURA Pipeline.

Validates ALL generation requests (image + video) BEFORE they reach the API.
Catches errors before they happen instead of auditing failures after the fact.

RULES ENFORCED:
  1. Video model MUST be omni_flash — Veo is NOT allowed as automatic fallback
  2. Speech text in video prompts MUST be ≤ 30 words (10 seconds max)
  3. "OBSCURA" brand name MUST NOT appear in generation prompts (it's the store
     name, not a garment brand — products are sourced blanks with no branding)
  4. Products MUST exist in MANUAL_CURATION with real metadata.json + images
  5. Reference image file paths MUST exist on disk
  6. Video duration MUST be exactly 10 seconds
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional

log = logging.getLogger("guardrails")

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MAX_SPEECH_WORDS = 30  # 10 seconds of speech ≈ 25-30 words
ALLOWED_VIDEO_MODELS = {"omni_flash"}
BANNED_BRAND_PATTERNS = [
    re.compile(r'\bOBSCURA\b'),           # exact uppercase
    re.compile(r'\bObscura\b'),           # title case
    re.compile(r'\bobscura\b'),           # lowercase
]

# Contexts where brand name is acceptable (e.g., CTA "shop at OBSCURA",
# "link in bio", store references — NOT on the garment itself)
BRAND_OK_CONTEXTS = [
    "link in bio",
    "shop at",
    "shop the",
    "got from",
    "just dropped",
    "just arrived",
    "CTA",
]

BASE_DIR = Path(__file__).parent
MANUAL_CURATION_DIR = BASE_DIR / "MANUAL_CURATION"


class GenerationGuardrails:
    """Validates ALL generation requests before they reach the API.
    
    Usage:
        from generation_guardrails import guardrails
        
        ok, violations = guardrails.validate_video_request(prompt, video_model)
        if not ok:
            for v in violations:
                print(f"[!] GUARDRAIL BLOCKED: {v}")
            return []
    """

    # ── VIDEO REQUEST VALIDATION ──────────────────────────────────────────

    def validate_video_request(
        self,
        prompt: str,
        video_model: str,
        ref_image_paths: Optional[List[str]] = None,
        duration_seconds: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate a video generation request. Returns (is_valid, violations)."""
        violations = []

        # Rule 1: Video model must be omni_flash
        if video_model not in ALLOWED_VIDEO_MODELS:
            violations.append(
                f"WRONG MODEL: video_model='{video_model}' is NOT allowed. "
                f"Only {ALLOWED_VIDEO_MODELS} permitted. Veo fallback is blocked."
            )

        # Rule 2: Speech word count ≤ 30
        speech_text = self._extract_speech_from_prompt(prompt)
        if speech_text:
            word_count = len(speech_text.split())
            if word_count > MAX_SPEECH_WORDS:
                violations.append(
                    f"SPEECH TOO LONG: {word_count} words detected in speech "
                    f"(max {MAX_SPEECH_WORDS} for 10-second video). "
                    f"Speech: '{speech_text[:80]}...'"
                )

        # Rule 3: No "OBSCURA" branding on garments in prompts
        brand_violation = self._check_brand_in_prompt(prompt)
        if brand_violation:
            violations.append(brand_violation)

        # Rule 4: Reference images must exist
        if ref_image_paths:
            for path in ref_image_paths:
                if path and not os.path.exists(path):
                    violations.append(
                        f"MISSING REF IMAGE: '{path}' does not exist on disk."
                    )

        # Rule 5: Duration must be 10 seconds (if explicitly specified)
        if duration_seconds is not None and duration_seconds != 10:
            violations.append(
                f"WRONG DURATION: duration={duration_seconds}s specified, "
                f"but only 10s is allowed for Omni Flash UGC videos."
            )

        is_valid = len(violations) == 0
        if not is_valid:
            log.warning(
                f"[GUARDRAIL] VIDEO BLOCKED — {len(violations)} violation(s): "
                + "; ".join(violations)
            )
        return is_valid, violations

    # ── IMAGE REQUEST VALIDATION ──────────────────────────────────────────

    def validate_image_request(
        self,
        prompt: str,
        ref_image_paths: Optional[List[str]] = None,
        product_folder: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate an image generation request. Returns (is_valid, violations)."""
        violations = []

        # Rule 3: No "OBSCURA" branding on garments
        brand_violation = self._check_brand_in_prompt(prompt)
        if brand_violation:
            violations.append(brand_violation)

        # Rule 4: Reference images must exist
        if ref_image_paths:
            for path in ref_image_paths:
                if path and not os.path.exists(path):
                    violations.append(
                        f"MISSING REF IMAGE: '{path}' does not exist on disk."
                    )

        # Rule 5: Product folder must have metadata if specified
        if product_folder:
            exists_ok, exists_msg = self.validate_product_exists(
                product_name=None, product_folder=product_folder
            )
            if not exists_ok:
                violations.extend(exists_msg)

        is_valid = len(violations) == 0
        if not is_valid:
            log.warning(
                f"[GUARDRAIL] IMAGE BLOCKED — {len(violations)} violation(s): "
                + "; ".join(violations)
            )
        return is_valid, violations

    # ── PRODUCT EXISTENCE VALIDATION ──────────────────────────────────────

    def validate_product_exists(
        self,
        product_name: Optional[str],
        product_folder: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Check that a product exists in MANUAL_CURATION with metadata.json
        and at least one real image file."""
        violations = []

        if product_folder:
            folder_path = Path(product_folder)
            if not folder_path.is_absolute():
                folder_path = MANUAL_CURATION_DIR / product_folder

            if not folder_path.exists():
                violations.append(
                    f"PHANTOM PRODUCT: Folder '{folder_path.name}' does not "
                    f"exist in MANUAL_CURATION. Cannot generate for a product "
                    f"that hasn't been sourced and approved."
                )
                return False, violations

            metadata_path = folder_path / "metadata.json"
            if not metadata_path.exists():
                violations.append(
                    f"NO METADATA: '{folder_path.name}' has no metadata.json. "
                    f"Product must be properly curated before generation."
                )
                return False, violations

            # Check for at least one real image
            image_exts = {".jpg", ".jpeg", ".png", ".webp"}
            images = [
                f for f in folder_path.iterdir()
                if f.suffix.lower() in image_exts and f.name != "size.jpg"
            ]
            if not images:
                violations.append(
                    f"NO IMAGES: '{folder_path.name}' has metadata.json but "
                    f"no product images. Need real flat-lay photos to generate from."
                )

        is_valid = len(violations) == 0
        return is_valid, violations

    # ── INTERNAL HELPERS ──────────────────────────────────────────────────

    def _extract_speech_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract quoted speech/voiceover text from a generation prompt.
        
        Looks for patterns like:
          Speaking: "..."
          Speaking directly: '...'
          Voiceover: "..."
          Model's voice says: '...'
        """
        # Match text inside quotes after speech indicators
        patterns = [
            # Double quotes after speech keywords
            r"(?:Speaking|Voiceover|voice\s+says?|says?)\s*(?:directly\s*)?(?:to\s+(?:the\s+)?camera\s*)?:\s*['\"](.+?)['\"]",
            # Standalone quoted speech (single or double)
            r"['\"]([^'\"]{15,})['\"]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE | re.DOTALL)
            if matches:
                # Return the longest match (most likely the actual speech)
                return max(matches, key=len)

        return None

    def _check_brand_in_prompt(self, prompt: str) -> Optional[str]:
        """Check if "OBSCURA" appears in a prompt as garment branding.
        
        Allows brand name in acceptable contexts like CTAs ("shop at OBSCURA",
        "got from OBSCURA") but blocks it when used to describe what the model
        is wearing (e.g., "wearing an OBSCURA hoodie").
        """
        for pattern in BANNED_BRAND_PATTERNS:
            match = pattern.search(prompt)
            if match:
                # Check if it's in an acceptable context
                # Get surrounding text (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(prompt), match.end() + 50)
                context = prompt[start:end].lower()

                # If it's in a CTA or store reference context, allow it
                if any(ok_ctx in context for ok_ctx in BRAND_OK_CONTEXTS):
                    continue

                # It's being used to describe clothing/product → BLOCK
                return (
                    f"BRAND ON GARMENT: Prompt contains '{match.group()}' used "
                    f"as garment branding. OBSCURA is the store name, not a "
                    f"clothing brand. Products are sourced blanks with no "
                    f"visible branding. Remove brand name from garment description."
                )

        return None


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON INSTANCE — import this directly
# ─────────────────────────────────────────────────────────────────────────────
guardrails = GenerationGuardrails()
