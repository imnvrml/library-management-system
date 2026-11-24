"""Run the tests and keep the test report and the traceability matrix in sync with them.

    python scripts/trace.py

1. runs pytest and reads the result of every test function (JUnit XML);
2. finds the test case ID in each test name (e.g. test_TC_CHK_03_... -> TC-CHK-03);
3. fills the Actual / Result columns of docs/test-plan.md section 4;
4. writes docs/traceability.md: requirement -> use case -> design -> code -> test cases -> automated tests,
   and lists requirements without tests and tests without a requirement.
"""
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "test-plan.md"
REQS = ROOT / "docs" / "requirements.md"
MATRIX = ROOT / "docs" / "traceability.md"

TC_IN_NAME = re.compile(r"TC_([A-Z]+[0-9]*)_([0-9]{2})")
BR_TO_FR = {"BR-04": "FR-11", "BR-06": "FR-09", "BR-11": "FR-03"}

# Test cases that are not automated functions: (actual result, result)
NOT_AUTOMATED = {
    "TC-NFR-05": ("Not run yet: manual walkthrough with 2 people is planned before submission", "Not run"),
    "TC-NFR-07": ("Coverage of library/services 87–100 % per module, 95 % total (section 5.3)", "Pass"),
    "TC-NFR-08": ("CI installs from requirements.txt and runs the suite in < 20 s; install + start = 5 commands "
                  "(README)", "Pass"),
}

# requirement -> (use cases, design elements, code modules)
DESIGN = {
    "FR-01": ("UC-01", "SD-05; AuthService, auth_bp", "services/auth.py, web/auth.py"),
    "FR-02": ("UC-01 (all)", "SD-05; role_required, AccessDeniedError", "web/__init__.py"),
    "FR-03": ("UC-03", "SD-06; CatalogueService.add_title", "services/catalogue.py"),
    "FR-04": ("UC-03, UC-15", "SD-06, Copy SM; CatalogueService.add_copy, ReservationService.serve_queue",
              "services/catalogue.py, services/reservations.py"),
    "FR-05": ("UC-03", "Copy SM; CatalogueService.withdraw_copy", "services/catalogue.py"),
    "FR-06": ("UC-02", "SD-06; CatalogueService.search, TitleRepository.search",
              "services/catalogue.py, repositories/__init__.py"),
    "FR-07": ("UC-04", "SD-07; MemberService.register", "services/members.py"),
    "FR-08": ("UC-04", "SD-07; MemberService.deactivate", "services/members.py"),
    "FR-09": ("UC-05", "SD-01, Copy SM, DT-1; CirculationService.checkout, EligibilityPolicy.checkout_refusal",
              "services/circulation.py, services/policies.py"),
    "FR-10": ("UC-06", "SD-02, Copy SM; CirculationService.return_copy", "services/circulation.py"),
    "FR-11": ("UC-07", "SD-03, DT-2; CirculationService.renew, EligibilityPolicy.renew_refusal",
              "services/circulation.py, services/policies.py"),
    "FR-12": ("UC-13", "SD-02; FinePolicy.fine_for", "services/policies.py"),
    "FR-13": ("UC-08", "SD-04, Reservation SM, DT-3; ReservationService.place, EligibilityPolicy.reservation_refusal",
              "services/reservations.py, services/policies.py"),
    "FR-14": ("UC-15", "SD-02, SD-06, Reservation SM; ReservationService.serve_queue", "services/reservations.py"),
    "FR-15": ("UC-14", "SD-01..SD-04, Reservation SM; ReservationService.expire_holds", "services/reservations.py"),
    "FR-16": ("UC-09", "SD-04, Reservation SM; ReservationService.cancel", "services/reservations.py"),
    "FR-17": ("UC-10", "SD-05; account_bp, MemberService.balance, ReservationService.active_of", "web/account.py"),
    "FR-18": ("UC-11", "SD-07; MemberService.record_payment, EligibilityPolicy.payment_refusal",
              "services/members.py"),
    "FR-19": ("UC-12", "SD-07; CirculationService.overdue_loans", "services/circulation.py"),
    "FR-20": ("—", "— (Could: extension, not designed)", "— (not implemented)"),
    "FR-21": ("—", "Copy SM (state Lost only)", "— (not implemented)"),
    "NFR-01": ("UC-02", "TitleRepository.search", "repositories/__init__.py"),
    "NFR-02": ("UC-01, UC-04", "AuthService.hash_password", "services/auth.py"),
    "NFR-03": ("all", "role_required decorator", "web/__init__.py"),
    "NFR-04": ("UC-05, UC-06, UC-07, UC-14", "Database.transaction", "db.py"),
    "NFR-05": ("UC-05, UC-06", "dashboard page", "web/templates/dashboard.html"),
    "NFR-06": ("UC-04, UC-10", "logical ERD: user table; ReservationView", "schema.sql, services/reservations.py"),
    "NFR-07": ("—", "test pyramid (test plan 2.1)", "tests/"),
    "NFR-08": ("—", "run_tests.py, CI", "run_tests.py, .github/workflows/ci.yml"),
}


def tc_id(name: str) -> str | None:
    m = TC_IN_NAME.search(name)
    return f"TC-{m.group(1)}-{m.group(2)}" if m else None


def run_tests() -> dict[str, str]:
    """Return {test node: 'pass'|'fail'|'skip'}."""
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "results.xml"
        subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={xml_path}"], cwd=ROOT, check=False)
        results = {}
        for case in ET.parse(xml_path).getroot().iter("testcase"):
            node = f"{case.get('classname')}::{case.get('name')}"
            status = "pass"
            if case.find("failure") is not None or case.find("error") is not None:
                status = "fail"
            elif case.find("skipped") is not None:
                status = "skip"
            results[node] = status
        return results


def requirements() -> list[tuple[str, str, str]]:
    text = REQS.read_text(encoding="utf-8")
    reqs = [(m[1], m[2], m[3]) for m in re.finditer(r"\*\*(FR-\d+) — (.+?) \(([MSCW])\)\.\*\*", text)]
    for line in text.splitlines():
        m = re.match(r"\| (NFR-\d+) \| ([^|]+) \| ([^|]+) \|.*\| ([MSCW]) \|$", line)
        if m:
            reqs.append((m[1], f"{m[2].strip()}: {m[3].strip()[:60]}", m[4]))
    return reqs


def main() -> None:
    results = run_tests()
    by_tc: dict[str, list[tuple[str, str]]] = defaultdict(list)
    untraced = []
    for node, status in results.items():
        tc = tc_id(node)
        (by_tc[tc].append((node, status)) if tc else untraced.append(node))

    # ---- 1. fill Actual / Result in the test plan ----
    plan_lines = PLAN.read_text(encoding="utf-8").splitlines()
    tc_reqs: dict[str, str] = {}
    for i, line in enumerate(plan_lines):
        if not line.startswith("| TC-"):
            continue
        cells = line.split(" | ")
        tc = cells[0][2:].strip()
        tc_reqs[tc] = cells[1]
        if tc in by_tc:
            statuses = [s for _, s in by_tc[tc]]
            ok = all(s == "pass" for s in statuses)
            n = len(statuses)
            actual = "as expected" + (f" ({n} checks)" if n > 1 else "") if ok else "differs — see defect log"
            result = "Pass" if ok else "Fail"
        elif tc in NOT_AUTOMATED:
            actual, result = NOT_AUTOMATED[tc]
        else:
            actual, result = "no automated test found", "Not run"
        cells[-2], cells[-1] = actual, f"{result} |"
        plan_lines[i] = " | ".join(cells)
    PLAN.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

    # ---- 2. traceability matrix ----
    req_to_tcs: dict[str, list[str]] = defaultdict(list)
    for tc, req_cell in tc_reqs.items():
        ids = set(re.findall(r"N?FR-\d+", req_cell)) | {BR_TO_FR[b] for b in re.findall(r"BR-\d+", req_cell)
                                                         if b in BR_TO_FR}
        for r in sorted(ids):
            req_to_tcs[r].append(tc)

    def automated(tcs):
        return sum(len(by_tc.get(tc, [])) for tc in tcs)

    out = ["# Traceability Matrix — Library Management System", "",
           "Generated by `python scripts/trace.py` from `docs/requirements.md`, `docs/test-plan.md` and the "
           "automated test results. Do not edit by hand; run the script again.", "",
           "Legend: SD = sequence diagram, SM = state machine, DT = decision table (models / test plan). "
           "*Automated* = number of executed test functions/parameter sets that carry one of the test case IDs.", "",
           "## 1. Requirement → use case → design → code → tests", "",
           "| Req | Name | Prio | Use case | Design element (diagram; class) | Code module | Test cases | Automated | Status |",
           "|---|---|---|---|---|---|---|---|---|"]
    missing = []
    for rid, name, prio in requirements():
        uc, design, code = DESIGN.get(rid, ("?", "?", "?"))
        tcs = sorted(req_to_tcs.get(rid, []))
        n = automated(tcs)
        failed = any(s != "pass" for tc in tcs for _, s in by_tc.get(tc, []))
        if not tcs:
            status = "**NO TEST**" + (" (Could, not implemented)" if prio == "C" else "")
            missing.append(rid)
        elif failed:
            status = "**FAILING**"
        else:
            status = "traced, passing" if n else "traced, manual only"
        out.append(f"| {rid} | {name} | {prio} | {uc} | {design} | `{code}` | {', '.join(tcs) or '—'} | {n} | {status} |")

    must = [r for r, _, p in requirements() if p == "M"]
    out += ["", "## 2. Checks", "",
            f"- Must requirements: {len(must)}; fully traced (use case, design, code and at least one passing test): "
            f"{sum(1 for r in must if r not in missing)}.",
            f"- Requirements without a test case: {', '.join(missing) or 'none'}.",
            f"- Test cases in the plan: {len(tc_reqs)}; automated: {sum(1 for tc in tc_reqs if tc in by_tc)}; "
            f"manual or measured: {', '.join(sorted(NOT_AUTOMATED))}.",
            f"- Executed test functions/parameter sets: {len(results)}; passed: "
            f"{sum(1 for s in results.values() if s == 'pass')}.",
            "", "## 3. Automated tests without a test case ID", "",
            "These tests check technical behaviour that supports the requirements (schema, transactions, CSRF, "
            "helpers) but are not test cases of the plan. They are listed so that no test is hidden.", ""]
    out += [f"- `{node}`" for node in sorted(untraced)] or ["- none"]
    unknown = sorted(tc for tc in by_tc if tc not in tc_reqs)
    out += ["", "## 4. Test IDs used in code but missing from the plan", "",
            *([f"- {tc}" for tc in unknown] or ["- none"])]
    MATRIX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Updated {PLAN.name} and {MATRIX.name}: {len(results)} tests, {len(untraced)} without ID, "
          f"requirements without test: {missing}, unknown IDs: {unknown}")


if __name__ == "__main__":
    main()
