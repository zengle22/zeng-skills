#!/usr/bin/env python3
"""
validate-dag.py — I2I Task 依赖关系确定性校验

用法:
    python validate-dag.py <task-list.json>

输入: task-list.json（I2I Phase 3 产出）
输出: dag-validation.json（同目录）

校验内容:
    1. 输入 Schema 校验
    2. 环检测（Tarjan 算法）
    3. 拓扑排序（Kahn 算法）
    4. 孤立节点检测
"""

import heapq
import json
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED_TASK_FIELDS = {"id", "slug", "name", "priority", "estimated_hours", "dependencies"}
VALID_PRIORITY = {"P0", "P1", "P2"}
VALID_DEP_TYPE = {"FS", "FF", "data-dependency"}


def load_task_list(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data: dict) -> list[str]:
    """校验 task-list.json 输入 Schema，返回错误列表"""
    errors: list[str] = []
    if "tasks" not in data:
        errors.append("Missing top-level 'tasks' array")
        return errors
    if not isinstance(data["tasks"], list):
        errors.append("'tasks' must be an array")
        return errors

    seen_ids: set[str] = set()
    for i, task in enumerate(data["tasks"]):
        prefix = f"tasks[{i}]"
        missing = REQUIRED_TASK_FIELDS - set(task.keys())
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
        if task.get("id") in seen_ids:
            errors.append(f"{prefix}: duplicate id '{task['id']}'")
        seen_ids.add(task.get("id", ""))

        if task.get("priority") not in VALID_PRIORITY:
            errors.append(f"{prefix}: invalid priority '{task.get('priority')}'")

        hours = task.get("estimated_hours")
        if not isinstance(hours, (int, float)) or hours <= 0:
            errors.append(f"{prefix}: estimated_hours must be positive number")

        deps = task.get("dependencies", [])
        if not isinstance(deps, list):
            errors.append(f"{prefix}: dependencies must be array")

        dep_type = task.get("dependency_type", {})
        if not isinstance(dep_type, dict):
            errors.append(f"{prefix}: dependency_type must be object")
        else:
            for dep_id, dtype in dep_type.items():
                if dtype not in VALID_DEP_TYPE:
                    errors.append(f"{prefix}.dependency_type.{dep_id}: invalid type '{dtype}'")
                if dep_id not in deps:
                    errors.append(f"{prefix}.dependency_type.{dep_id}: references non-existent dependency")

    return errors


def build_graph(tasks: list) -> tuple[dict[str, list[str]], dict[str, list[str]], set[str]]:
    """构建邻接表和入度表"""
    adj: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = defaultdict(int)
    all_nodes: set[str] = set()

    for task in tasks:
        task_id = task["id"]
        all_nodes.add(task_id)
        deps = task.get("dependencies", [])
        for dep in deps:
            adj[dep].append(task_id)
            in_degree[task_id] += 1
        if task_id not in in_degree:
            in_degree[task_id] = 0

    return adj, in_degree, all_nodes


def detect_cycle_tarjan(adj: dict[str, list[str]], all_nodes: set[str]) -> list[list[str]]:
    """Tarjan 算法检测环，提取最小环路路径"""
    index_counter = [0]
    stack = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    cycles: list[list[str]] = []

    def strongconnect(v: str):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True

        for w in adj.get(v, []):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w, False):
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                # 提取 SCC 中的最小环（沿 SCC 内的边回溯）
                cycle = _extract_min_cycle(scc, adj)
                cycles.append(cycle)

    for v in all_nodes:
        if v not in index:
            strongconnect(v)

    return cycles


def _extract_min_cycle(scc: list[str], adj: dict[str, list[str]]) -> list[str]:
    """从 SCC 中提取一条最小环路路径"""
    scc_set = set(scc)
    # BFS 从 SCC 中第一个节点出发，找最短环
    start = scc[0]
    queue: list[tuple[str, list[str]]] = [(start, [start])]
    visited: set[str] = {start}
    while queue:
        node, path = queue.pop(0)
        for neighbor in adj.get(node, []):
            if neighbor == start and len(path) > 1:
                return path
            if neighbor in scc_set and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return scc  # fallback


def topological_sort_kahn(adj: dict[str, list[str]], in_degree: dict[str, int], all_nodes: set[str]) -> tuple[list[str], bool]:
    """Kahn 算法拓扑排序（使用堆确保确定性顺序，O(n log n)）"""
    heap = [n for n in all_nodes if in_degree.get(n, 0) == 0]
    heapq.heapify(heap)
    result: list[str] = []

    while heap:
        node = heapq.heappop(heap)
        result.append(node)
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    is_valid = len(result) == len(all_nodes)
    return result, is_valid


def find_isolated_nodes(adj: dict[str, list[str]], in_degree: dict[str, int], all_nodes: set[str]) -> list[str]:
    """检测孤立节点（无依赖也无被依赖）"""
    has_outgoing = set(adj.keys())
    has_incoming = {n for n, d in in_degree.items() if d > 0}
    return sorted(all_nodes - has_outgoing - has_incoming)


def validate(task_list_path: str) -> dict:
    data = load_task_list(task_list_path)

    # Schema 校验
    schema_errors = validate_schema(data)
    if schema_errors:
        return {
            "status": "SCHEMA_ERROR",
            "reason": "Input schema validation failed",
            "schema_errors": schema_errors,
            "total_tasks": 0,
            "cycles": [],
            "topological_order": [],
            "isolated_nodes": [],
        }

    tasks = data.get("tasks", [])

    if not tasks:
        return {
            "status": "WARNING",
            "reason": "No tasks found in task-list.json",
            "total_tasks": 0,
            "cycles": [],
            "topological_order": [],
            "isolated_nodes": [],
        }

    adj, in_degree, all_nodes = build_graph(tasks)

    # 环检测
    cycles = detect_cycle_tarjan(adj, all_nodes)

    # 拓扑排序
    topo_order, is_valid = topological_sort_kahn(adj, dict(in_degree), all_nodes)

    # 孤立节点
    isolated = find_isolated_nodes(adj, in_degree, all_nodes)

    # 判定
    if cycles:
        status = "CYCLE_DETECTED"
        reason = f"Found {len(cycles)} cycle(s)"
    elif not is_valid:
        status = "CYCLE_DETECTED"
        reason = "Topological sort failed (cycle detected)"
    elif isolated:
        status = "WARNING"
        reason = f"Found {len(isolated)} isolated node(s)"
    else:
        status = "PASS"
        reason = "All checks passed"

    return {
        "status": status,
        "reason": reason,
        "total_tasks": len(tasks),
        "cycles": [{"nodes": c, "length": len(c)} for c in cycles],
        "topological_order": topo_order,
        "isolated_nodes": isolated,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate-dag.py <task-list.json>", file=sys.stderr)
        sys.exit(2)

    task_list_path = sys.argv[1]
    if not Path(task_list_path).exists():
        print(f"Error: File not found: {task_list_path}", file=sys.stderr)
        sys.exit(2)

    result = validate(task_list_path)

    # 输出到同目录
    output_path = str(Path(task_list_path).parent / "dag-validation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["status"] == "CYCLE_DETECTED":
        sys.exit(1)
    elif result["status"] == "SCHEMA_ERROR":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
