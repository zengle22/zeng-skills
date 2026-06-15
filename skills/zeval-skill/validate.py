#!/usr/bin/env python3
"""
zeval-skill: 产物契约校验脚本

职责：
  1. 校验 EvalReport 是否符合 EvalReport.schema.json
  2. 校验 rubric YAML 是否基本结构合法
  3. 校验 EvalRequest ↔ EvalReport 的引用一致性
  4. （可选）--promote-baseline 把当前 run promote 为 baseline

与 zcode-review-deep/validate.py 范式一致：单文件、无第三方依赖（除 jsonschema / pyyaml）。
"""
import argparse
import json
import sys
import pathlib
import shutil
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("❌ missing dependency: pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from jsonschema import validate, Draft202012Validator
except ImportError:
    print("❌ missing dependency: jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent
SCHEMAS = ROOT / "schemas"
RUBRICS = ROOT / "rubrics"


def load_json(p):
    return json.loads(p.read_text())


def check_report(report_path: pathlib.Path, rubric_path: pathlib.Path = None):
    """校验 EvalReport 主报告。"""
    schema = load_json(SCHEMAS / "EvalReport.schema.json")
    Draft202012Validator.check_schema(schema)
    report = load_json(report_path)
    validate(instance=report, schema=schema)
    print(f"  [OK] schema: {report_path.name} 符合 EvalReport.schema.json")

    if rubric_path:
        rubric = yaml.safe_load(rubric_path.read_text())
        if report["rubric_id"] != rubric["id"]:
            raise AssertionError(
                f"rubric_id 不一致: report={report['rubric_id']} vs rubric={rubric['id']}"
            )
        if report["rubric_version"] != str(rubric["version"]):
            raise AssertionError(
                f"rubric_version 不一致: report={report['rubric_version']} vs rubric={rubric['version']}"
            )
        print(f"  [OK] rubric 一致: {rubric['id']}@{rubric['version']}")

        # scores 的 dimension 必须在 rubric 中定义
        defined_dims = {d["id"] for d in rubric["dimensions"]}
        scored_dims = {s["dimension"] for s in report["scores"]}
        unknown = scored_dims - defined_dims
        if unknown:
            raise AssertionError(f"report 含未定义维度: {unknown}")
        print(f"  [OK] 所有 score 维度均在 rubric 中定义")

    # 缺证据检查
    for s in report["scores"]:
        if s["level"] == "fail" and not s.get("evidence_refs"):
            print(f"  [WARN] judge={s['judge_id']} dim={s['dimension']} 评分=fail 但无 evidence")
    return report


def check_rubric_file(path: pathlib.Path):
    """校验单个 rubric YAML。"""
    data = yaml.safe_load(path.read_text())
    assert "id" in data and "version" in data, f"missing id/version in {path.name}"
    assert data.get("dimensions"), f"no dimensions in {path.name}"
    for d in data["dimensions"]:
        assert d.get("id") and d.get("description"), f"bad dimension in {path.name}"
        assert d.get("weight", 0) > 0, f"non-positive weight in {path.name}"
    print(f"  [OK] rubric: {path.name}")


def check_request_report_consistency(request_path: pathlib.Path, report_path: pathlib.Path):
    """校验 request ↔ report 引用一致性。"""
    req = load_json(request_path)
    rep = load_json(report_path)
    assert req["rubric"]["id"] == rep["rubric_id"], "rubric_id mismatch"
    assert req["rubric"]["version"] == rep["rubric_version"], "rubric_version mismatch"
    judge_ids_req = {j["id"] for j in req["judges"]}
    judge_ids_rep = {s["judge_id"] for s in rep["scores"]}
    missing = judge_ids_req - judge_ids_rep
    assert not missing, f"missing judge scores for: {missing}"
    print("  [OK] request ↔ report 一致")


def promote_baseline(run_dir: pathlib.Path, root: pathlib.Path = pathlib.Path(".zeval")):
    """把当前 run promote 为 baseline。"""
    report = load_json(run_dir / "report.json")
    if report["verdict"]["verdict"] not in ("pass", "pass-with-warn"):
        raise AssertionError(
            f"仅 pass / pass-with-warn 的 run 可 promote，当前 verdict={report['verdict']['verdict']}"
        )
    rubric_id = report["rubric_id"]
    target_hash = report["request_hash"]
    baseline_dir = root / "baselines" / rubric_id / target_hash
    if baseline_dir.exists():
        raise AssertionError(f"baseline 已存在: {baseline_dir}，如需覆盖请先手动删除")
    baseline_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(run_dir / "report.json", baseline_dir / "baseline.json")
    if (run_dir / "replay_bundle").exists():
        shutil.copytree(run_dir / "replay_bundle", baseline_dir / "replay_bundle", dirs_exist_ok=True)
    meta = {
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "source_run_id": report["run_id"],
        "rubric_id": rubric_id,
        "rubric_version": report["rubric_version"],
        "verdict": report["verdict"]["verdict"],
        "score": report["verdict"]["score"],
    }
    (baseline_dir / "meta.yaml").write_text(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False))
    print(f"  [OK] baseline 已 promote: {baseline_dir}")


def main():
    parser = argparse.ArgumentParser(description="zeval-skill 产物校验")
    parser.add_argument("--report", type=pathlib.Path, help="EvalReport.json 路径")
    parser.add_argument("--request", type=pathlib.Path, help="EvalRequest.json 路径")
    parser.add_argument("--rubric", type=pathlib.Path, help="rubric YAML 路径")
    parser.add_argument("--check-rubrics", action="store_true", help="校验 rubrics/ 下所有 YAML")
    parser.add_argument("--promote-baseline", type=pathlib.Path, metavar="RUN_DIR", help="把 run 目录 promote 为 baseline")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(".zeval"), help=".zeval 根目录")
    args = parser.parse_args()

    try:
        if args.check_rubrics:
            print("[1/3] Rubric 结构校验")
            for p in sorted(RUBRICS.glob("*.yaml")):
                if p.name.startswith("_"):
                    continue
                check_rubric_file(p)
        if args.report:
            print("\n[2/3] Report 校验")
            check_report(args.report, args.rubric)
        if args.request and args.report:
            print("\n[3/3] 交叉引用校验")
            check_request_report_consistency(args.request, args.report)
        if args.promote_baseline:
            print("\n[+] Baseline promote")
            promote_baseline(args.promote_baseline, args.root)
        print("\n✅ All checks passed")
    except AssertionError as e:
        print(f"\n❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
