"""
DLP Engine - Data Loss Prevention with pattern matching and PII detection.

Scans text for sensitive data using regex patterns and Microsoft Presidio.
Supports blocking, redacting, or alerting on sensitive data.
"""

import logging
import re
from typing import List, Optional, Set
from dataclasses import dataclass

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)


@dataclass
class DLPResult:
    """Result of DLP scan"""
    blocked: bool
    pii_detected: bool
    redacted_text: str
    violations: List[str]
    pii_entities: List[str]
    confidence_scores: dict


class DLPEngine:
    """
    Data Loss Prevention engine.

    Features:
    - Pattern-based detection (credit cards, SSN, API keys, etc.)
    - PII detection with Microsoft Presidio
    - Configurable actions: block, redact, alert
    """

    def __init__(self):
        """Initialize DLP engine"""
        logger.info("Initializing DLP Engine...")

        # Initialize Presidio
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Define sensitive patterns
        self.patterns = {
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "api_key": r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})",
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "private_key": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "bearer_token": r"bearer\s+[a-zA-Z0-9\-._~+/]+=*",
            "password": r"(?i)(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?([^\s'\"]+)",
            "ip_internal": r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        }

        # Blocking patterns (always block these)
        self.block_patterns = {
            "api_key",
            "aws_key",
            "private_key",
            "password",
        }

        logger.info("DLP Engine initialized with Presidio")

    async def scan(
        self,
        text: str,
        mode: str = "redact",  # block, redact, alert
        language: str = "en",
    ) -> DLPResult:
        """
        Scan text for sensitive data.

        Args:
            text: Text to scan
            mode: Action mode (block, redact, alert)
            language: Language code (default: en)

        Returns:
            DLPResult with scan results
        """
        violations: List[str] = []
        pii_entities: List[str] = []
        blocked = False
        redacted_text = text

        # Step 1: Pattern-based detection
        pattern_violations = self._scan_patterns(text)
        violations.extend(pattern_violations)

        # Check if any blocking patterns matched
        if any(pattern in self.block_patterns for pattern in pattern_violations):
            blocked = True

        # Step 2: Presidio PII detection
        pii_results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "CREDIT_CARD",
                "US_SSN",
                "US_PASSPORT",
                "LOCATION",
                "DATE_TIME",
                "IBAN_CODE",
                "IP_ADDRESS",
                "CRYPTO",
                "MEDICAL_LICENSE",
                "URL",
            ],
        )

        # Extract PII entity types
        if pii_results:
            pii_entities = list(set([result.entity_type for result in pii_results]))

        # Redact PII if mode is redact
        if mode == "redact" and (pattern_violations or pii_results):
            redacted_text = self._redact_text(text, pii_results, pattern_violations)

        # Build confidence scores
        confidence_scores = {
            result.entity_type: result.score for result in pii_results
        }

        return DLPResult(
            blocked=blocked and mode == "block",
            pii_detected=bool(pii_results),
            redacted_text=redacted_text,
            violations=violations,
            pii_entities=pii_entities,
            confidence_scores=confidence_scores,
        )

    def _scan_patterns(self, text: str) -> List[str]:
        """
        Scan text using regex patterns.

        Args:
            text: Text to scan

        Returns:
            List of matched pattern names
        """
        matched_patterns = []

        for pattern_name, pattern_regex in self.patterns.items():
            if re.search(pattern_regex, text, re.IGNORECASE):
                logger.warning(f"Pattern matched: {pattern_name}")
                matched_patterns.append(pattern_name)

        return matched_patterns

    def _redact_text(
        self,
        text: str,
        pii_results: List[RecognizerResult],
        pattern_violations: List[str],
    ) -> str:
        """
        Redact sensitive information from text.

        Args:
            text: Original text
            pii_results: Presidio detection results
            pattern_violations: Matched patterns

        Returns:
            Redacted text
        """
        redacted = text

        # Redact PII using Presidio
        if pii_results:
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=pii_results,
                operators={
                    "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
                    "PERSON": OperatorConfig("replace", {"new_value": "<NAME_REDACTED>"}),
                    "EMAIL_ADDRESS": OperatorConfig(
                        "replace", {"new_value": "<EMAIL_REDACTED>"}
                    ),
                    "PHONE_NUMBER": OperatorConfig(
                        "replace", {"new_value": "<PHONE_REDACTED>"}
                    ),
                    "CREDIT_CARD": OperatorConfig(
                        "replace", {"new_value": "<CARD_REDACTED>"}
                    ),
                    "US_SSN": OperatorConfig("replace", {"new_value": "<SSN_REDACTED>"}),
                },
            )
            redacted = anonymized.text

        # Redact pattern-based matches
        for pattern_name in pattern_violations:
            if pattern_name in self.patterns:
                pattern = self.patterns[pattern_name]
                redacted = re.sub(
                    pattern,
                    f"<{pattern_name.upper()}_REDACTED>",
                    redacted,
                    flags=re.IGNORECASE,
                )

        return redacted

    def add_custom_pattern(self, name: str, pattern: str, block: bool = False) -> None:
        """
        Add custom DLP pattern.

        Args:
            name: Pattern name
            pattern: Regex pattern
            block: Whether to block on match
        """
        self.patterns[name] = pattern
        if block:
            self.block_patterns.add(name)

        logger.info(f"Added custom DLP pattern: {name}")
