import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

from backend.apps.solve.models import UserAttempt, VerificationRecord

logger = logging.getLogger(__name__)

VERIFICATION_STATUS_VERIFIED = "VERIFIED"
VERIFICATION_STATUS_FAILED = "FAILED"
VERIFICATION_STATUS_UNABLE = "UNABLE_TO_VERIFY"


@dataclass
class VerificationResult:
    status: str
    method: str
    confidence: float
    details: str
    checks: list = field(default_factory=list)
    expected: Optional[str] = None
    actual: Optional[str] = None


class BaseVerificationStrategy(ABC):
    @abstractmethod
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        raise NotImplementedError


def _safe_eval_expression(expression: str):
    if not isinstance(expression, str):
        return None
    expression = expression.strip()
    if not expression:
        return None
    safe_pattern = re.compile(r"^[0-9+\-*/().%\s]+$")
    if not safe_pattern.match(expression):
        return None
    try:
        expr = parse_expr(
            expression,
            transformations=standard_transformations + (implicit_multiplication_application,),
        )
        return float(expr)
    except Exception:
        return None


def _extract_numbers(text: str):
    pattern = r"[-+]?\d*\.\d+|\d+"
    return [float(m) for m in re.findall(pattern, text)]


def normalize_answer(text: str):
    if not text:
        return None
    text = text.strip().lower()
    text = text.replace("₹", "").replace(",", "").replace(" ", "")

    if "/" in text:
        parts = text.split("/")
        if len(parts) == 2:
            try:
                return float(parts[0]) / float(parts[1])
            except ValueError:
                pass

    if text.endswith("%"):
        text = text[:-1]

    match = re.match(r"^([-+]?\d*\.?\d+)", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return None


def compare_normalized(actual: str, expected: str, tolerance: float = 1e-3):
    a = normalize_answer(actual)
    b = normalize_answer(expected)
    if a is None or b is None:
        return None
    return abs(a - b) <= tolerance


def _verify_steps(steps: list):
    if not steps:
        return True, "No steps to verify", []

    failed_step = None
    for step in steps:
        calc = step.get("calculation", "")
        if "=" not in calc:
            continue
        left, right = calc.split("=", 1)
        left = left.strip()
        right = right.strip()
        left_val = _safe_eval_expression(left)
        right_val = _safe_eval_expression(right)
        if left_val is None or right_val is None:
            return False, f"Cannot evaluate step: {calc}", [step]
        if abs(left_val - right_val) > 1e-6:
            failed_step = step
            return False, f"Step {step.get('step')} failed: {calc}", [failed_step]
    return True, "All steps arithmetically correct.", []


class PercentageOfStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "percentage" and bool(re.search(r"\d+\s*%\s*of\s+\d+", question_text, re.IGNORECASE))

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s+(\d+(?:\.\d+)?)", question_text, re.IGNORECASE)
        if not match:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERCENTAGE_OF", 0.0, "Could not extract numbers.", expected=None, actual=final_answer)
        pct = float(match.group(1))
        base = float(match.group(2))
        expected = base * pct / 100
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERCENTAGE_OF", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "PERCENTAGE_OF", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "PERCENTAGE_OF", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class PercentageChangeStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "percentage" and bool(re.search(r"from\s+\d+\s+to\s+\d+", question_text, re.IGNORECASE))

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        match = re.search(r"from\s+(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)", question_text, re.IGNORECASE)
        if not match:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERCENTAGE_CHANGE", 0.0, "Could not extract numbers.", expected=None, actual=final_answer)
        old = float(match.group(1))
        new = float(match.group(2))
        if old == 0:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERCENTAGE_CHANGE", 0.0, "Division by zero.", expected=None, actual=final_answer)
        expected = (new - old) / old * 100
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERCENTAGE_CHANGE", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "PERCENTAGE_CHANGE", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "PERCENTAGE_CHANGE", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class ProfitLossStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "profit-loss"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PROFIT_LOSS", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        cp, sp = numbers[0], numbers[1]
        expected = abs((sp - cp) / cp * 100)
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PROFIT_LOSS", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "PROFIT_LOSS", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "PROFIT_LOSS", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class AverageStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "average"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "AVERAGE", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        expected = sum(numbers) / len(numbers)
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "AVERAGE", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "AVERAGE", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "AVERAGE", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class SimpleInterestStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "simple-interest"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 3:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "SIMPLE_INTEREST", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        p, r, t = numbers[0], numbers[1], numbers[2]
        expected = p * r * t / 100
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "SIMPLE_INTEREST", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "SIMPLE_INTEREST", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "SIMPLE_INTEREST", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class CompoundInterestStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "compound-interest"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", question_text)
        year_match = re.search(r"(\d+)\s+year", question_text)
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "COMPOUND_INTEREST", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        p = numbers[0]
        r = float(pct_match.group(1)) if pct_match else (numbers[1] if len(numbers) > 1 else 0)
        t = float(year_match.group(1)) if year_match else (numbers[2] if len(numbers) > 2 else numbers[1])
        try:
            expected = p * ((1 + r / 100) ** t - 1)
        except Exception:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "COMPOUND_INTEREST", 0.0, "Calculation error.", expected=None, actual=final_answer)
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "COMPOUND_INTEREST", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "COMPOUND_INTEREST", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "COMPOUND_INTEREST", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class TimeWorkStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "time-work"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TIME_WORK", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        rates = [1 / n for n in numbers[:2] if n != 0]
        if not rates:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TIME_WORK", 0.0, "Invalid rates.", expected=None, actual=final_answer)
        combined = sum(rates)
        expected = 1 / combined
        result = compare_normalized(str(expected), final_answer, tolerance=1e-2)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TIME_WORK", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "TIME_WORK", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "TIME_WORK", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class PipesCisternsStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "pipes-cisterns"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PIPES_CISTERNS", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        inlet = numbers[0]
        outlet = numbers[1]
        if inlet >= outlet:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PIPES_CISTERNS", 0.0, "Inlet must be less than outlet for net filling.", expected=None, actual=final_answer)
        expected = 1 / (1 / inlet - 1 / outlet)
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PIPES_CISTERNS", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "PIPES_CISTERNS", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "PIPES_CISTERNS", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class TimeSpeedDistanceStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "time-speed-distance"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TIME_SPEED_DISTANCE", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        speed = numbers[0]
        time = numbers[1]
        expected = speed * time
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TIME_SPEED_DISTANCE", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "TIME_SPEED_DISTANCE", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "TIME_SPEED_DISTANCE", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class TrainStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "problems-trains"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TRAIN", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        length = numbers[0]
        speed = numbers[1]
        expected = length / speed
        if "km/h" in question_text.lower() and ("m" in question_text.lower() or "pole" in question_text.lower()):
            expected = expected * 3.6
        result = compare_normalized(str(expected), final_answer, tolerance=1e-1)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "TRAIN", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "TRAIN", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "TRAIN", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class HcfLcmStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "hcf-lcm"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) < 2:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "HCF_LCM", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
        a, b = numbers[0], numbers[1]
        import math
        hcf = math.gcd(int(a), int(b))
        lcm = abs(int(a * b)) // hcf if hcf != 0 else 0
        answer_norm = normalize_answer(final_answer)
        if answer_norm is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "HCF_LCM", 0.0, "Could not normalize answer.", expected=f"HCF={hcf}, LCM={lcm}", actual=final_answer)
        if abs(answer_norm - hcf) < 1e-6 or abs(answer_norm - lcm) < 1e-6:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "HCF_LCM", 1.0, "Answer matches HCF or LCM.", expected=f"HCF={hcf}, LCM={lcm}", actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "HCF_LCM", 1.0, "Answer does not match HCF or LCM.", expected=f"HCF={hcf}, LCM={lcm}", actual=final_answer)


class ProbabilityStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "probability"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        numbers = _extract_numbers(question_text)
        if len(numbers) >= 2:
            favorable = numbers[0]
            total = numbers[1]
            if total == 0:
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "PROBABILITY", 0.0, "Division by zero.", expected=None, actual=final_answer)
            expected = favorable / total
            result = compare_normalized(str(expected), final_answer)
            if result is None:
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "PROBABILITY", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
            if result:
                return VerificationResult(VERIFICATION_STATUS_VERIFIED, "PROBABILITY", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
            return VerificationResult(VERIFICATION_STATUS_FAILED, "PROBABILITY", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_UNABLE, "PROBABILITY", 0.0, "Insufficient structure for verification.", expected=None, actual=final_answer)


class PermutationCombinationStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "permutation-combination"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        n_match = re.search(r"(\d+)\s+(?:people|letters|items|objects|things|books|students|digits)", question_text, re.IGNORECASE)
        r_match = re.search(r"(\d+)\s+(?:from|at\s+a\s+time|committee|group|team|subset|arrangements?|ways?)", question_text, re.IGNORECASE)
        if not n_match:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERMUTATION_COMBINATION", 0.0, "Could not extract n.", expected=None, actual=final_answer)
        n = int(n_match.group(1))
        r = int(r_match.group(1)) if r_match else n
        if r > n:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERMUTATION_COMBINATION", 0.0, "r > n.", expected=None, actual=final_answer)
        import math
        if "arrange" in question_text.lower():
            expected = math.factorial(n) / math.factorial(n - r) if r <= n else 0
        else:
            expected = math.factorial(n) / (math.factorial(r) * math.factorial(n - r))
        result = compare_normalized(str(expected), final_answer)
        if result is None:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "PERMUTATION_COMBINATION", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
        if result:
            return VerificationResult(VERIFICATION_STATUS_VERIFIED, "PERMUTATION_COMBINATION", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_FAILED, "PERMUTATION_COMBINATION", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)


class RatioStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "ratio-proportion"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        if "share" in question_text.lower() or "divide" in question_text.lower():
            numbers = _extract_numbers(question_text)
            if len(numbers) < 2:
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "RATIO", 0.0, "Not enough numbers.", expected=None, actual=final_answer)
            total = numbers[0]
            parts = numbers[1:]
            sum_parts = sum(parts)
            if sum_parts == 0:
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "RATIO", 0.0, "Sum of parts is zero.", expected=None, actual=final_answer)
            for idx, part in enumerate(parts):
                expected = total / sum_parts * part
                result = compare_normalized(str(expected), final_answer)
                if result:
                    return VerificationResult(VERIFICATION_STATUS_VERIFIED, "RATIO", 1.0, f"Independent calculation matches for part {idx+1}.", expected=str(expected), actual=final_answer)
            return VerificationResult(VERIFICATION_STATUS_FAILED, "RATIO", 1.0, "Independent calculation does not match any part.", expected=str([total / sum_parts * p for p in parts]), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_UNABLE, "RATIO", 0.0, "Unsupported ratio structure.", expected=None, actual=final_answer)


class NumberSystemStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "number-system"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        if "remainder" in question_text.lower():
            numbers = _extract_numbers(question_text)
            if len(numbers) >= 2:
                dividend, divisor = numbers[0], numbers[1]
                if divisor == 0:
                    return VerificationResult(VERIFICATION_STATUS_UNABLE, "NUMBER_SYSTEM", 0.0, "Division by zero.", expected=None, actual=final_answer)
                expected = dividend % divisor
                result = compare_normalized(str(expected), final_answer)
                if result is None:
                    return VerificationResult(VERIFICATION_STATUS_UNABLE, "NUMBER_SYSTEM", 0.0, "Could not normalize answer.", expected=str(expected), actual=final_answer)
                if result:
                    return VerificationResult(VERIFICATION_STATUS_VERIFIED, "NUMBER_SYSTEM", 1.0, "Independent calculation matches.", expected=str(expected), actual=final_answer)
                return VerificationResult(VERIFICATION_STATUS_FAILED, "NUMBER_SYSTEM", 1.0, "Independent calculation does not match.", expected=str(expected), actual=final_answer)
        return VerificationResult(VERIFICATION_STATUS_UNABLE, "NUMBER_SYSTEM", 0.0, "Unsupported number-system structure.", expected=None, actual=final_answer)


class AgesStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return topic_slug == "ages"

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        step_ok, step_details, _ = _verify_steps(steps)
        if not step_ok:
            return VerificationResult(VERIFICATION_STATUS_FAILED, "AGES", 1.0, f"Step verification failed: {step_details}", checks=["STEP_VERIFICATION"])
        if steps:
            last_calc = steps[-1].get("calculation", "")
            if "=" in last_calc:
                _, right = last_calc.split("=", 1)
                result = compare_normalized(right.strip(), final_answer)
                if result:
                    return VerificationResult(VERIFICATION_STATUS_VERIFIED, "AGES", 1.0, "Final answer consistent with last step.", checks=["STEP_VERIFICATION", "CONSISTENCY"])
                return VerificationResult(VERIFICATION_STATUS_FAILED, "AGES", 1.0, "Final answer inconsistent with last step.", checks=["STEP_VERIFICATION", "CONSISTENCY"])
        return VerificationResult(VERIFICATION_STATUS_UNABLE, "AGES", 0.0, "Insufficient structure for independent verification.", expected=None, actual=final_answer)


class AlgebraicStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return bool(re.search(r"[a-zA-Z]\s*[\+\-\*/]\s*\d+.*=\s*\d+", question_text) or re.search(r"\d+\s*[a-zA-Z].*=\s*\d+", question_text))

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        equation_str = self._extract_equation(question_text)
        if not equation_str:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.0, "Could not extract equation from question text.", expected=None, actual=final_answer)
        equation_str = equation_str.replace(" ", "")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9+\-*/().=]+", equation_str):
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.0, "Unsafe equation format.", expected=None, actual=final_answer)
        try:
            lhs_str, rhs_str = equation_str.split("=", 1)
            variable_match = re.search(r"[a-zA-Z]", equation_str)
            if not variable_match:
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.0, "No variable found in equation.", expected=None, actual=final_answer)
            variable = variable_match.group(0)
            from sympy import symbols, Eq, solve
            sympy_var = symbols(variable)
            lhs = parse_expr(lhs_str, local_dict={variable: sympy_var}, transformations=standard_transformations + (implicit_multiplication_application,))
            rhs = parse_expr(rhs_str, local_dict={variable: sympy_var}, transformations=standard_transformations + (implicit_multiplication_application,))
            equation = Eq(lhs, rhs)
            solutions = solve(equation, sympy_var)
            if not solutions:
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.0, "No solution found.", expected=None, actual=final_answer)
            expected_solution = solutions[0]
            expected_str = str(expected_solution)
            answer_normalized = final_answer.strip().lower().replace(" ", "")
            if answer_normalized.startswith(variable.lower() + "="):
                answer_value = answer_normalized.split("=", 1)[1]
                comparison = compare_normalized(answer_value, expected_str)
                if comparison is True:
                    return VerificationResult(VERIFICATION_STATUS_VERIFIED, "ALGEBRAIC", 1.0, "Submitted answer matches SymPy-derived solution.", expected=expected_str, actual=final_answer)
                if comparison is False:
                    return VerificationResult(VERIFICATION_STATUS_FAILED, "ALGEBRAIC", 1.0, "Submitted answer does not match derived solution.", expected=expected_str, actual=final_answer)
                return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.5, "Could not normalize submitted answer for comparison.", expected=expected_str, actual=final_answer)
            comparison = compare_normalized(answer_normalized, expected_str)
            if comparison is True:
                return VerificationResult(VERIFICATION_STATUS_VERIFIED, "ALGEBRAIC", 1.0, "Submitted answer matches SymPy-derived solution.", expected=expected_str, actual=final_answer)
            if comparison is False:
                return VerificationResult(VERIFICATION_STATUS_FAILED, "ALGEBRAIC", 1.0, "Submitted answer does not match derived solution.", expected=expected_str, actual=final_answer)
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.5, "Could not normalize submitted answer for comparison.", expected=expected_str, actual=final_answer)
        except Exception as exc:
            logger.debug("Algebraic verification failed: %s", exc)
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "ALGEBRAIC", 0.0, "Could not safely parse or solve equation.", expected=None, actual=final_answer)

    def _extract_equation(self, question_text: str) -> Optional[str]:
        equals_positions = [m.start() for m in re.finditer(r'=', question_text)]
        for pos in equals_positions:
            start = max(0, pos - 30)
            end = min(len(question_text), pos + 30)
            context = question_text[start:end]
            eq_match = re.search(r'([a-zA-Z0-9+\-*/().\s]+=\s*[-+]?\d+(?:\.\d+)?)', context)
            if not eq_match:
                continue
            candidate = eq_match.group(1).strip()
            for prefix in ("solve", "find", "if", "then", "what is", "calculate", "evaluate"):
                if candidate.lower().startswith(prefix):
                    candidate = candidate[len(prefix):].strip()
            if not candidate or '=' not in candidate:
                continue
            return candidate
        return None


class DefaultStrategy(BaseVerificationStrategy):
    def can_handle(self, topic_slug: str, problem_type_name: str, question_text: str) -> bool:
        return True

    def verify(self, question_text: str, final_answer: str, steps: list) -> VerificationResult:
        step_ok, step_details, _ = _verify_steps(steps)
        if not step_ok:
            return VerificationResult(VERIFICATION_STATUS_FAILED, "DEFAULT", 1.0, f"Step verification failed: {step_details}", checks=["STEP_VERIFICATION"])
        if not steps:
            return VerificationResult(VERIFICATION_STATUS_UNABLE, "DEFAULT", 0.0, "No steps or strategy matched.", expected=None, actual=final_answer)
        last_step = steps[-1]
        last_calc = last_step.get("calculation", "")
        if "=" in last_calc:
            _, right = last_calc.split("=", 1)
            result = compare_normalized(right.strip(), final_answer)
            if result:
                return VerificationResult(VERIFICATION_STATUS_VERIFIED, "DEFAULT", 0.8, "Final answer consistent with steps.", checks=["STEP_VERIFICATION", "CONSISTENCY"])
            return VerificationResult(VERIFICATION_STATUS_FAILED, "DEFAULT", 0.8, "Final answer inconsistent with last step.", checks=["STEP_VERIFICATION", "CONSISTENCY"])
        return VerificationResult(VERIFICATION_STATUS_UNABLE, "DEFAULT", 0.5, "Could not verify final answer against steps.", expected=None, actual=final_answer)


class VerificationService:
    def __init__(self):
        self.strategies = [
            PercentageOfStrategy(),
            PercentageChangeStrategy(),
            ProfitLossStrategy(),
            AverageStrategy(),
            SimpleInterestStrategy(),
            CompoundInterestStrategy(),
            TimeWorkStrategy(),
            PipesCisternsStrategy(),
            TimeSpeedDistanceStrategy(),
            TrainStrategy(),
            HcfLcmStrategy(),
            ProbabilityStrategy(),
            PermutationCombinationStrategy(),
            RatioStrategy(),
            NumberSystemStrategy(),
            AgesStrategy(),
            AlgebraicStrategy(),
            DefaultStrategy(),
        ]

    def verify(self, attempt: UserAttempt, solve_output: dict = None) -> VerificationResult:
        if solve_output is None:
            solve_output = {}
        question_text = solve_output.get("question_text", "")
        final_answer = solve_output.get("final_answer", "")
        steps = solve_output.get("steps", [])
        topic_slug = ""
        problem_type_name = ""
        topic = solve_output.get("topic")
        if isinstance(topic, dict):
            topic_slug = topic.get("slug", "") or topic.get("name", "").lower().replace(" ", "-")
        problem_type = solve_output.get("problem_type")
        if isinstance(problem_type, dict):
            problem_type_name = problem_type.get("name", "")

        for strategy in self.strategies:
            if strategy.can_handle(topic_slug, problem_type_name, question_text):
                result = strategy.verify(question_text, final_answer, steps)
                record = VerificationRecord(
                    attempt=attempt,
                    method=result.method,
                    input_data=solve_output,
                    expected_result=result.expected or "",
                    actual_result=result.actual or final_answer,
                    is_verified=(result.status == VERIFICATION_STATUS_VERIFIED),
                    verification_details={
                        "status": result.status,
                        "confidence": result.confidence,
                        "details": result.details,
                        "checks": result.checks,
                    },
                )
                record.save()
                return result

        fallback = VerificationResult(VERIFICATION_STATUS_UNABLE, "UNKNOWN", 0.0, "No verification strategy matched.", expected=None, actual=final_answer)
        record = VerificationRecord(
            attempt=attempt,
            method="UNKNOWN",
            input_data=solve_output,
            expected_result="",
            actual_result=final_answer,
            is_verified=False,
            verification_details={"status": fallback.status, "confidence": fallback.confidence, "details": fallback.details},
        )
        record.save()
        return fallback
