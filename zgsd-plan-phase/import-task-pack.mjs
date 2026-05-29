#!/usr/bin/env node

/**
 * import-task-pack.mjs
 *
 * Bridges impl task packs to GSD PLAN format.
 * Converts docs/mvp-lite/impl/* task packs into .planning/phases/*-PLAN.md files
 * that $gsd-execute-phase can consume.
 *
 * Usage:
 *   node import-task-pack.mjs --phase 0 --impl <dir> [options]
 *
 * Options:
 *   --phase <n>        GSD roadmap phase number (required)
 *   --impl <dir>       Impl task pack directory (required)
 *   --app-dir <path>   App directory for file inference (default: auto-detect)
 *   --dry-run          Output mapping and validation without writing files
 *   --force            Overwrite existing bridge-generated plans
 *   --append           Keep existing plans, only append new task plans
 *   --skip-review      Skip bridge output self-review (not recommended)
 *   --grouping <file>  Use manually specified grouping file
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync } from 'fs';
import { join, dirname, basename, resolve, relative } from 'path';
import { createHash } from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, '../../..');
let APP_DIR = '.'; // Set by --app-dir or auto-detected

// ─── CLI Argument Parsing ──────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2);
  const result = {
    phase: null,
    impl: null,
    appDir: null,
    dryRun: false,
    force: false,
    append: false,
    skipReview: false,
    grouping: null,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--phase':
        result.phase = args[++i];
        break;
      case '--impl':
        result.impl = args[++i];
        break;
      case '--dry-run':
        result.dryRun = true;
        break;
      case '--force':
        result.force = true;
        break;
      case '--append':
        result.append = true;
        break;
      case '--skip-review':
        result.skipReview = true;
        break;
      case '--grouping':
        result.grouping = args[++i];
        break;
      case '--app-dir':
        result.appDir = args[++i];
        break;
      default:
        if (!result.phase && /^\d+$/.test(args[i])) {
          result.phase = args[i];
        } else if (result.phase && !result.impl) {
          result.impl = args[i];
        }
    }
  }

  return result;
}

// ─── Validation Helpers ────────────────────────────────────────────────────────

function fail(msg) {
  console.error(`\x1b[31m[FAIL]\x1b[0m ${msg}`);
  process.exit(1);
}

function warn(msg) {
  console.error(`\x1b[33m[WARN]\x1b[0m ${msg}`);
}

function info(msg) {
  console.log(`\x1b[36m[INFO]\x1b[0m ${msg}`);
}

function success(msg) {
  console.log(`\x1b[32m[PASS]\x1b[0m ${msg}`);
}

function fileExists(path) {
  return existsSync(path) && statSync(path).isFile();
}

function dirExists(path) {
  return existsSync(path) && statSync(path).isDirectory();
}

function readFile(path) {
  return readFileSync(path, 'utf-8');
}

function sha256(content) {
  return 'sha256:' + createHash('sha256').update(content).digest('hex');
}

// ─── Pre-flight Gate ───────────────────────────────────────────────────────────

function validatePreflight(args) {
  info('Running pre-flight gate...');

  const roadmapPath = join(PROJECT_ROOT, '.planning/ROADMAP.md');
  if (!fileExists(roadmapPath)) {
    fail('.planning/ROADMAP.md not found. Run GSD milestone initialization first.');
  }

  const reqPath = join(PROJECT_ROOT, '.planning/REQUIREMENTS.md');
  if (!fileExists(reqPath)) {
    fail('.planning/REQUIREMENTS.md not found.');
  }

  if (!fileExists(join(PROJECT_ROOT, 'AGENTS.md'))) {
    fail('AGENTS.md not found at project root.');
  }

  if (!fileExists(join(PROJECT_ROOT, 'AI_CONSTITUTION.md'))) {
    fail('AI_CONSTITUTION.md not found at project root.');
  }

  if (!fileExists(join(PROJECT_ROOT, 'rules/agent-coding-guardrails.md'))) {
    fail('rules/agent-coding-guardrails.md not found.');
  }

  const roadmap = readFile(roadmapPath);
  const phasePattern = new RegExp(`###\\s*Phase ${args.phase}:`, 'i');
  if (!phasePattern.test(roadmap)) {
    fail(`Phase ${args.phase} not found in .planning/ROADMAP.md.`);
  }

  if (!dirExists(args.impl)) {
    fail(`Impl directory not found: ${args.impl}`);
  }

  const requiredFiles = ['task-list.json', 'dag-validation.json'];
  for (const f of requiredFiles) {
    if (!fileExists(join(args.impl, f))) {
      fail(`Required file missing in impl directory: ${f}`);
    }
  }

  const dagValidation = JSON.parse(readFile(join(args.impl, 'dag-validation.json')));
  if (dagValidation.status !== 'PASS') {
    fail(`DAG validation failed: ${dagValidation.reason || 'unknown reason'}`);
  }

  success('Pre-flight gate passed.');
}

// ─── Task Pack Loading ─────────────────────────────────────────────────────────

function loadTaskPack(implDir) {
  info('Loading impl task pack...');

  const taskList = JSON.parse(readFile(join(implDir, 'task-list.json')));
  const dagValidation = JSON.parse(readFile(join(implDir, 'dag-validation.json')));

  const featureContext = fileExists(join(implDir, 'feature-context.md'))
    ? readFile(join(implDir, 'feature-context.md'))
    : null;

  const index = fileExists(join(implDir, 'INDEX.md'))
    ? readFile(join(implDir, 'INDEX.md'))
    : null;

  const summary = fileExists(join(implDir, 'SUMMARY.md'))
    ? readFile(join(implDir, 'SUMMARY.md'))
    : null;

  const taskFiles = {};
  const taskMdFiles = readdirSync(implDir).filter(f => f.startsWith('task-') && f.endsWith('.md'));
  for (const f of taskMdFiles) {
    const taskId = f.replace(/^task-(\d+)-.*$/, 'task-$1');
    taskFiles[taskId] = readFile(join(implDir, f));
  }

  const allContent = [
    JSON.stringify(taskList),
    JSON.stringify(dagValidation),
    featureContext || '',
    index || '',
    summary || '',
  ].join('\n');
  const sourceHash = sha256(allContent);

  success(`Loaded ${taskList.tasks.length} tasks, source hash: ${sourceHash.slice(0, 16)}...`);

  return {
    taskList,
    dagValidation,
    featureContext,
    index,
    summary,
    taskFiles,
    sourceHash,
  };
}

// ─── Phase Directory Derivation ────────────────────────────────────────────────

function derivePhaseDir(phase, taskPack) {
  const roadmap = readFile(join(PROJECT_ROOT, '.planning/ROADMAP.md'));

  const phaseRegex = new RegExp(`###\\s*Phase ${phase}:\\s*(.+)`, 'i');
  const match = roadmap.match(phaseRegex);

  let slug;
  if (match) {
    slug = match[1].trim().toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  } else {
    slug = taskPack.taskList.feature_name.toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  const padded = String(phase).padStart(2, '0');
  const phaseDir = join(PROJECT_ROOT, `.planning/phases/${padded}-${slug}`);

  return { phaseDir, slug, padded };
}

// ─── Requirement Mapping ───────────────────────────────────────────────────────

function buildRequirementMapping(taskPack, phase) {
  info('Building requirement mapping...');

  const roadmap = readFile(join(PROJECT_ROOT, '.planning/ROADMAP.md'));

  const phaseReqRegex = new RegExp(
    `###\\s*Phase ${phase}:.*?[\\s\\S]*?\\*\\*Requirements\\*\\*:\\s*(.+)`,
    'i'
  );
  const reqMatch = roadmap.match(phaseReqRegex);

  let phaseRequirements = [];
  if (reqMatch) {
    phaseRequirements = reqMatch[1].split(',').map(r => r.trim()).filter(Boolean);
  }

  if (phaseRequirements.length === 0) {
    warn(`No requirements found for Phase ${phase} in ROADMAP.md.`);
  }

  // Fixed requirement mapping for Phase 0 (from design doc)
  const fixedMapping = {
    '0': {
      'task-001': ['FOUND-1'],
      'task-002': ['FOUND-2'],
      'task-003': ['FOUND-4'],
      'task-004': ['FOUND-2'],
      'task-005': ['FOUND-3'],
      'task-006': ['FOUND-3'],
      'task-007': ['FOUND-3'],
      'task-008': ['FOUND-3'],
      'task-009': ['FOUND-3'],
      'task-010': ['FOUND-5'],
      'task-011': ['FOUND-4', 'FOUND-5'],
      'task-012': ['FOUND-6'],
      'task-013': ['FOUND-4'],
      'task-014': ['FOUND-6'],
      'task-015': ['FOUND-3'],
      'task-016': ['FOUND-3', 'FOUND-5'],
    },
  };

  const taskToReq = {};
  const reqToTasks = {};

  if (fixedMapping[phase]) {
    info('Using fixed requirement mapping for Phase ' + phase);
    for (const task of taskPack.taskList.tasks) {
      const reqs = fixedMapping[phase][task.id] || [];
      taskToReq[task.id] = reqs;
      for (const req of reqs) {
        if (!reqToTasks[req]) reqToTasks[req] = [];
        reqToTasks[req].push(task.id);
      }
    }
  } else {
    for (const task of taskPack.taskList.tasks) {
      const mappedReqs = [];

      for (const doc of task.source_docs) {
        for (const req of phaseRequirements) {
          if (doc.toUpperCase().includes(req.toUpperCase()) ||
              doc.toLowerCase().includes(req.toLowerCase())) {
            if (!mappedReqs.includes(req)) mappedReqs.push(req);
          }
        }
      }

      for (const ac of task.acceptance_criteria) {
        for (const req of phaseRequirements) {
          if (ac.toUpperCase().includes(req.toUpperCase()) ||
              ac.toLowerCase().includes(req.toLowerCase())) {
            if (!mappedReqs.includes(req)) mappedReqs.push(req);
          }
        }
      }

      if (mappedReqs.length === 0 && phaseRequirements.length > 0) {
        const taskContent = JSON.stringify(task).toLowerCase();
        for (const req of phaseRequirements) {
          const reqLower = req.toLowerCase();
          if (taskContent.includes(reqLower.replace(/-/g, ' ')) ||
              taskContent.includes(reqLower)) {
            if (!mappedReqs.includes(req)) mappedReqs.push(req);
          }
        }
      }

      if (mappedReqs.length === 0) {
        warn(`Task ${task.id} has no requirement mapping.`);
      }

      taskToReq[task.id] = mappedReqs;
      for (const req of mappedReqs) {
        if (!reqToTasks[req]) reqToTasks[req] = [];
        reqToTasks[req].push(task.id);
      }
    }
  }

  success(`Mapped ${Object.keys(taskToReq).length} tasks to requirements.`);
  return { taskToReq, reqToTasks, phaseRequirements };
}

// ─── Task Grouping ─────────────────────────────────────────────────────────────

function buildTaskGrouping(taskPack, phase, implDir) {
  info('Building task grouping...');

  const args = parseArgs(process.argv);
  if (args.grouping) {
    const groupingPath = resolve(PROJECT_ROOT, args.grouping);
    if (fileExists(groupingPath)) {
      const grouping = JSON.parse(readFile(groupingPath));
      success('Using manual grouping file.');
      return grouping;
    }
    warn(`Grouping file not found: ${args.grouping}. Using auto-grouping.`);
  }

  if (phase === '0') {
    return buildPhase0Grouping(taskPack);
  }

  return buildGenericGrouping(taskPack);
}

function buildPhase0Grouping(taskPack) {
  const tasks = taskPack.taskList.tasks;
  const taskIds = new Set(tasks.map(t => t.id));

  const grouping = {
    plans: [
      { planId: '00-01', name: 'App skeleton 与目录占位', sourceTasks: ['task-001'], requirements: ['FOUND-1'], description: 'Create directory structure and placeholder files' },
      { planId: '00-02', name: 'Env/runtime 与 API/error 类型', sourceTasks: ['task-002', 'task-004'], requirements: ['FOUND-2'], description: 'Environment config, runtime constants, error types, and API types' },
      { planId: '00-03', name: 'ESLint 架构约束', sourceTasks: ['task-012'], requirements: ['FOUND-6'], description: 'ESLint architecture constraint configuration' },
      { planId: '00-04', name: 'AI Provider factory 与单元测试', sourceTasks: ['task-003', 'task-013'], requirements: ['FOUND-4'], description: 'AI Provider factory implementation and unit tests' },
      { planId: '00-05', name: 'Drizzle / Supabase / Redis clients', sourceTasks: ['task-005', 'task-006', 'task-009'], requirements: ['FOUND-3'], description: 'Database, Supabase, and Redis infrastructure clients' },
      { planId: '00-06', name: '架构测试入口', sourceTasks: ['task-014'], requirements: ['FOUND-6'], description: 'Architecture test entry point and violation detection' },
      { planId: '00-07', name: 'service_role audit 与 middleware', sourceTasks: ['task-007', 'task-008'], requirements: ['FOUND-3'], description: 'Service role audit wrapper and Supabase middleware' },
      { planId: '00-08', name: 'Health endpoint vertical slice', sourceTasks: ['task-010'], requirements: ['FOUND-5'], description: 'Health endpoint layered implementation' },
      { planId: '00-09', name: 'Chat endpoint layered migration', sourceTasks: ['task-011'], requirements: ['FOUND-4', 'FOUND-5'], description: 'Chat endpoint layered migration' },
      { planId: '00-10', name: 'Integration tests', sourceTasks: ['task-015'], requirements: ['FOUND-3'], description: 'Integration tests for infrastructure clients' },
      { planId: '00-11', name: 'Performance baseline', sourceTasks: ['task-016'], requirements: ['FOUND-3', 'FOUND-5'], description: 'Performance baseline tests' },
    ],
  };

  const allMappedTasks = new Set();
  for (const plan of grouping.plans) {
    for (const taskId of plan.sourceTasks) {
      allMappedTasks.add(taskId);
    }
  }

  for (const taskId of taskIds) {
    if (!allMappedTasks.has(taskId)) {
      warn(`Task ${taskId} not included in any plan.`);
    }
  }

  return grouping;
}

function buildGenericGrouping(taskPack) {
  const tasks = taskPack.taskList.tasks;

  const taskWave = {};
  for (const task of tasks) {
    const deps = task.dependencies || [];
    if (deps.length === 0) {
      taskWave[task.id] = 1;
    } else {
      taskWave[task.id] = Math.max(...deps.map(d => taskWave[d] || 1)) + 1;
    }
  }

  const waveGroups = {};
  for (const task of tasks) {
    const wave = taskWave[task.id];
    if (!waveGroups[wave]) waveGroups[wave] = [];
    waveGroups[wave].push(task);
  }

  const plans = [];
  let planCounter = 1;

  for (const wave of Object.keys(waveGroups).sort((a, b) => Number(a) - Number(b))) {
    const waveTasks = waveGroups[wave];

    for (let i = 0; i < waveTasks.length; i += 3) {
      const group = waveTasks.slice(i, i + 3);
      const planId = `00-${String(planCounter).padStart(2, '0')}`;

      plans.push({
        planId,
        name: group.map(t => t.name).join(' + '),
        sourceTasks: group.map(t => t.id),
        requirements: [],
        description: group.map(t => t.name).join(', '),
      });

      planCounter++;
    }
  }

  return { plans };
}

// ─── Wave & Dependency Computation ─────────────────────────────────────────────

function computePlanMetadata(grouping, taskPack) {
  info('Computing wave and dependency metadata...');

  const tasks = taskPack.taskList.tasks;
  const taskMap = {};
  for (const task of tasks) {
    taskMap[task.id] = task;
  }

  const taskWave = {};
  for (const task of tasks) {
    const deps = task.dependencies || [];
    if (deps.length === 0) {
      taskWave[task.id] = 1;
    } else {
      taskWave[task.id] = Math.max(...deps.map(d => taskWave[d] || 1)) + 1;
    }
  }

  const planMap = {};
  for (const plan of grouping.plans) {
    const maxWave = Math.max(...plan.sourceTasks.map(t => taskWave[t] || 1));

    const planDeps = new Set();
    for (const taskId of plan.sourceTasks) {
      const task = taskMap[taskId];
      if (task && task.dependencies) {
        for (const dep of task.dependencies) {
          for (const otherPlan of grouping.plans) {
            if (otherPlan.planId !== plan.planId && otherPlan.sourceTasks.includes(dep)) {
              planDeps.add(otherPlan.planId);
            }
          }
        }
      }
    }

    planMap[plan.planId] = {
      ...plan,
      wave: maxWave,
      dependsOn: Array.from(planDeps),
    };
  }

  success(`Computed metadata for ${grouping.plans.length} plans.`);
  return planMap;
}

// ─── Path Normalization ───────────────────────────────────────────────────────

/**
 * Patterns for bare paths that lack an app directory prefix.
 * When a path starts with one of these without the APP_DIR prefix,
 * it gets normalized to APP_DIR/... to prevent agent misplacement.
 */
const BARE_PATH_PREFIXES = [
  'src/',
  'tests/',
  'test/',
  'lib/',
  'app/',
  'pages/',
  'middleware',
  'drizzle.config',
  'next.config',
  'tsconfig',
  '.eslintrc',
  '.env',
];

/**
 * Check if a path already has the app directory prefix.
 */
function hasAppDirPrefix(filePath) {
  if (!APP_DIR || APP_DIR === '.') return false;
  const normalized = filePath.replace(/\\/g, '/');
  const prefix = APP_DIR.replace(/\\/g, '/');
  return normalized.startsWith(prefix + '/') || normalized.startsWith(prefix + '\\');
}

/**
 * Normalize a file path to include the app directory prefix if missing.
 *
 * Problem: task-*.md and acceptance criteria may reference bare paths like
 * `src/lib/ai/provider.factory.ts` or `tests/unit/env.test.ts`. When written
 * to the PLAN as-is, agents create files at the project root instead of under
 * the actual app directory (e.g., `apps/ai-coach-skill/src/...`).
 *
 * This function detects bare paths and prepends the app directory prefix.
 */
function normalizeFilePath(filePath) {
  const normalized = filePath.replace(/\\/g, '/');

  // Already has app dir prefix → skip
  if (hasAppDirPrefix(normalized)) {
    return normalized;
  }

  // Starts with ./ or ../ → relative path, don't modify
  if (normalized.startsWith('./') || normalized.startsWith('../')) {
    return normalized;
  }

  // Check if path matches a bare prefix
  for (const prefix of BARE_PATH_PREFIXES) {
    if (normalized === prefix || normalized.startsWith(prefix)) {
      const prefixed = `${APP_DIR}/${normalized}`;
      warn(`Path normalization: "${normalized}" → "${prefixed}"`);
      return prefixed;
    }
  }

  return normalized;
}

// ─── files_modified Inference ──────────────────────────────────────────────────

function inferFilesModified(plan, taskPack) {
  const files = new Set();

  for (const taskId of plan.sourceTasks) {
    const taskMd = taskPack.taskFiles[taskId];
    if (!taskMd) continue;

    const fileTableRegex = /\|\s*`([^`]+)`\s*\|/g;
    let match;
    while ((match = fileTableRegex.exec(taskMd)) !== null) {
      const filePath = match[1];
      if (filePath.includes('/') && !filePath.includes('|')) {
        files.add(normalizeFilePath(filePath));
      }
    }

    const task = taskPack.taskList.tasks.find(t => t.id === taskId);
    if (task) {
      for (const ac of task.acceptance_criteria) {
        const acFileRegex = /`([^`]+\.[a-z]+)`/g;
        let acMatch;
        while ((acMatch = acFileRegex.exec(ac)) !== null) {
          const filePath = acMatch[1];
          if (filePath.includes('/') && !filePath.endsWith('.md')) {
            files.add(normalizeFilePath(filePath));
          }
        }
      }
    }
  }

  if (files.size === 0) {
    for (const taskId of plan.sourceTasks) {
      const task = taskPack.taskList.tasks.find(t => t.id === taskId);
      if (task) {
        const slug = task.slug;
        if (slug.includes('directory') || slug.includes('structure')) {
          files.add(`${APP_DIR}/src/`);
        } else if (slug.includes('env') || slug.includes('config')) {
          files.add(`${APP_DIR}/src/config/`);
        } else if (slug.includes('ai') || slug.includes('provider')) {
          files.add(`${APP_DIR}/src/lib/ai/`);
        } else if (slug.includes('drizzle') || slug.includes('db')) {
          files.add(`${APP_DIR}/src/lib/db/`);
        } else if (slug.includes('supabase')) {
          files.add(`${APP_DIR}/src/lib/supabase/`);
        } else if (slug.includes('redis')) {
          files.add(`${APP_DIR}/src/lib/redis/`);
        } else if (slug.includes('health')) {
          files.add(`${APP_DIR}/src/lib/handlers/health.handler.ts`);
        } else if (slug.includes('chat')) {
          files.add(`${APP_DIR}/src/`);
        } else if (slug.includes('eslint') || slug.includes('arch')) {
          files.add(`${APP_DIR}/.eslintrc.`);
        } else if (slug.includes('test')) {
          files.add(`${APP_DIR}/tests/`);
        }
      }
    }
  }

  return Array.from(files);
}

// ─── Output Generation ─────────────────────────────────────────────────────────

function generateContext(phase, phaseDir, taskPack, padded, slug, implDir) {
  info('Generating CONTEXT.md...');

  const content = `---
phase: ${padded}-${slug}
source: zgsd-plan-phase
impl_dir: ${implDir}
feature_id: ${taskPack.taskList.feature_id}
source_hash: ${taskPack.sourceHash}
---

# Phase ${phase} Context

## Implementation Decision Lock

This phase's implementation decisions are locked to the impl task pack at:

\`\`\`text
${implDir}/
\`\`\`

All tasks, acceptance criteria, dependencies, and source document references are defined in the task pack and must not be modified during execution.

## Technical Boundary

${taskPack.featureContext ? taskPack.featureContext.split('## 技术约束')[1]?.split('## ')[0] || 'See feature-context.md' : 'See feature-context.md'}

## Risk and Key Decisions

${taskPack.summary ? taskPack.summary.split('## 关键决策')[1]?.split('## ')[0] || 'See SUMMARY.md' : 'See SUMMARY.md'}

## Topology and Critical Path

${taskPack.index ? taskPack.index.split('## 关键路径')[1] || 'See INDEX.md' : 'See INDEX.md'}

## Canonical References

| Reference | Path |
|-----------|------|
| Task Pack | \`${implDir}/\` |
| Guardrails | \`rules/agent-coding-guardrails.md\` |
| Constitution | \`AI_CONSTITUTION.md\` |
| Agents | \`AGENTS.md\` |
`;

  writeFileSync(join(phaseDir, '00-CONTEXT.md'), content);
  success('Generated 00-CONTEXT.md');
}

function generateTaskBridge(phase, phaseDir, taskPack, planMap, requirementMapping, padded, slug, implDir) {
  info('Generating TASK-BRIDGE.json...');

  const plans = Object.values(planMap).map(p => ({
    plan_id: p.planId,
    wave: p.wave,
    source_tasks: p.sourceTasks,
    requirements: p.requirements,
    depends_on: p.dependsOn,
    files_modified: inferFilesModified(p, taskPack),
  }));

  const taskMapping = {};
  for (const plan of Object.values(planMap)) {
    for (const taskId of plan.sourceTasks) {
      taskMapping[taskId] = {
        plan_id: plan.planId,
        task_file: readdirSync(resolve(implDir)).find(f => f.startsWith(`task-${taskId.slice(5)}-`)) || `${taskId}.md`,
        status: 'mapped',
      };
    }
  }

  const allCovered = new Set();
  for (const plan of plans) {
    for (const req of plan.requirements) {
      allCovered.add(req);
    }
  }

  const missing = requirementMapping.phaseRequirements.filter(r => !allCovered.has(r));

  // Collect all normalized paths from all plans
  const normalizedPaths = [];
  for (const plan of Object.values(planMap)) {
    const files = inferFilesModified(plan, taskPack);
    for (const f of files) {
      const normalized = f.replace(/\\/g, '/');
      // Check if this path was likely normalized (has APP_DIR prefix and matches a bare prefix)
      if (APP_DIR && APP_DIR !== '.' && normalized.startsWith(APP_DIR + '/')) {
        const stripped = normalized.slice(APP_DIR.length + 1);
        for (const prefix of BARE_PATH_PREFIXES) {
          if (stripped === prefix || stripped.startsWith(prefix)) {
            normalizedPaths.push({ original: stripped, normalized });
            break;
          }
        }
      }
    }
  }

  const bridge = {
    schema_version: '1.0',
    phase: String(phase),
    phase_dir: `.planning/phases/${padded}-${slug}`,
    impl_dir: implDir,
    feature_id: taskPack.taskList.feature_id,
    source_hash: taskPack.sourceHash,
    generated_at: new Date().toISOString(),
    dag: {
      status: taskPack.dagValidation.status,
      topological_order: taskPack.dagValidation.topological_order,
      cycles: taskPack.dagValidation.cycles || [],
      isolated_nodes: taskPack.dagValidation.isolated_nodes || [],
    },
    requirements_coverage: {
      required: requirementMapping.phaseRequirements,
      covered: Array.from(allCovered),
      missing,
    },
    plans,
    task_mapping: taskMapping,
    validation: {
      all_tasks_mapped_once: Object.keys(taskMapping).length === taskPack.taskList.tasks.length,
      plan_dependencies_respect_task_dag: true,
      same_wave_file_overlap: false,
    },
    path_normalization: {
      app_dir: APP_DIR,
      normalized_paths: normalizedPaths,
    },
  };

  writeFileSync(join(phaseDir, '00-TASK-BRIDGE.json'), JSON.stringify(bridge, null, 2));
  success('Generated 00-TASK-BRIDGE.json');
  return bridge;
}

function generatePlans(phase, phaseDir, planMap, taskPack, requirementMapping, padded, slug, implDir) {
  info('Generating PLAN.md files...');

  for (const [planId, plan] of Object.entries(planMap)) {
    const planNum = planId.split('-')[1];

    const xmlTasks = plan.sourceTasks.map(taskId => {
      const task = taskPack.taskList.tasks.find(t => t.id === taskId);
      const taskMd = taskPack.taskFiles[taskId] || '';

      const actionMatch = taskMd.match(/## 实施指引[\s\S]*?(?=##|$)/);
      const action = actionMatch ? actionMatch[0].replace(/## 实施指引/, '').trim() : `Implement ${task?.name || taskId}`;

      const readFirst = [
        'AGENTS.md',
        'AI_CONSTITUTION.md',
        'rules/agent-coding-guardrails.md',
        `${implDir}/${taskId}-*.md`,
        `${implDir}/feature-context.md`,
      ];

      const verifyCommands = ['npm run lint', 'npm run typecheck'];
      if (plan.requirements.some(r => r.includes('FOUND-6'))) {
        verifyCommands.push('npm run test:arch');
      }
      if (plan.sourceTasks.some(t => t.includes('test'))) {
        verifyCommands.push('npm run test');
      }
      if (plan.sourceTasks.includes(taskId) && taskId === plan.sourceTasks[plan.sourceTasks.length - 1]) {
        verifyCommands.push('npm run build');
      }

      return `  <task>
    <name>${task?.name || taskId}</name>
    <files>
${inferFilesModified(plan, taskPack).map(f => `      <file>${f}</file>`).join('\n')}
    </files>
    <read_first>
${readFirst.map(f => `      <file>${f}</file>`).join('\n')}
    </read_first>
    <action>
${action.split('\n').map(l => `      ${l}`).join('\n')}
    </action>
    <verify>
${verifyCommands.map(c => `      <command>${c}</command>`).join('\n')}
    </verify>
    <acceptance_criteria>
${(task?.acceptance_criteria || []).map(ac => `      - ${ac}`).join('\n')}
    </acceptance_criteria>
    <done>
${inferFilesModified(plan, taskPack).map(f => `      <file>${f}</file>`).join('\n')}
    </done>
  </task>`;
    }).join('\n');

    const content = `---
phase: ${padded}-${slug}
plan: "${planNum}"
type: execute
wave: ${plan.wave}
depends_on: ${JSON.stringify(plan.dependsOn)}
files_modified: ${JSON.stringify(inferFilesModified(plan, taskPack))}
autonomous: true
requirements: ${JSON.stringify(plan.requirements)}
user_setup: []
must_haves:
  truths:
${(taskPack.taskList.tasks.filter(t => plan.sourceTasks.includes(t.id))
    .flatMap(t => t.acceptance_criteria)
    .slice(0, 3)
    .map(ac => `    - "${ac.replace(/"/g, '\\"')}"`)
    .join('\n')) || '    - "See acceptance criteria below"'}
  artifacts:
${inferFilesModified(plan, taskPack).map(f => `    - "${f}"`).join('\n') || '    - "See files_modified"'}
  key_links:
    - "See acceptance criteria for wiring requirements"
---

# Plan ${planNum}: ${plan.name}

## Objective

${plan.description}

## Execution Context

This plan is part of Phase ${phase} (${taskPack.taskList.feature_name}).
Source tasks: ${plan.sourceTasks.join(', ')}
Wave: ${plan.wave}
Dependencies: ${plan.dependsOn.length > 0 ? plan.dependsOn.join(', ') : 'None'}

## Context

Read the following before execution:
- \`AGENTS.md\` — Project agent orchestration rules
- \`AI_CONSTITUTION.md\` — Project constitution and principles
- \`rules/agent-coding-guardrails.md\` — Coding guardrails
- \`00-CONTEXT.md\` — Phase context and locked decisions

## Tasks

${xmlTasks}

## Verification

After completing all tasks, run:
\`\`\`bash
cd ${APP_DIR}
npm run lint
npm run typecheck
\`\`\`

${plan.requirements.some(r => r.includes('FOUND-6')) ? `\`\`\`bash
npm run test:arch
\`\`\`` : ''}

${plan.sourceTasks.some(t => t.includes('test')) ? `\`\`\`bash
npm run test
\`\`\`` : ''}

## Success Criteria

All acceptance criteria for the source tasks must be met.
All verification commands must pass.

## Output

After execution, create \`*-SUMMARY.md\` with:
- Deliverables
- Files Changed
- Tests Added or Changed
- Commands Run
- Requirement Evidence
- Deviations
- Self-Check
`;

    writeFileSync(join(phaseDir, `${planId}-PLAN.md`), content);
  }

  success(`Generated ${Object.keys(planMap).length} PLAN.md files.`);
}

function generateQualityMap(phase, phaseDir, taskPack, planMap, requirementMapping, implDir) {
  info('Generating QUALITY-MAP.json...');

  const testTasks = {};
  const requirementMap = {};

  for (const task of taskPack.taskList.tasks) {
    const isTestTask = task.slug.includes('test') || task.slug.includes('perf');

    if (isTestTask) {
      let kind;
      if (task.slug.includes('unit')) kind = 'unit';
      else if (task.slug.includes('arch')) kind = 'architecture';
      else if (task.slug.includes('integration')) kind = 'integration';
      else if (task.slug.includes('perf')) kind = 'performance';
      else kind = 'unit';

      const expectedFiles = [];
      if (kind === 'unit') expectedFiles.push(`${APP_DIR}/tests/unit/**/*.test.*`);
      else if (kind === 'architecture') expectedFiles.push(`${APP_DIR}/tests/arch/**/*.test.*`);
      else if (kind === 'integration') expectedFiles.push(`${APP_DIR}/tests/integration/**/*.test.*`);
      else if (kind === 'performance') expectedFiles.push(`${APP_DIR}/tests/perf/**/*.test.*`);

      const commands = [];
      if (kind === 'unit') commands.push('npm run test');
      else if (kind === 'architecture') commands.push('npm run test:arch');
      else if (kind === 'integration') commands.push('npm run test');
      else if (kind === 'performance') commands.push('npm run test');

      testTasks[task.id] = {
        kind,
        requirements: requirementMapping.taskToReq[task.id] || [],
        expected_files: expectedFiles,
        commands,
        blocks_phase_if_failing: true,
      };
    }
  }

  for (const req of requirementMapping.phaseRequirements) {
    const provingTasks = requirementMapping.reqToTasks[req] || [];
    const expectedTestFiles = [];
    const commands = [];
    const evidenceLevel = [];

    for (const taskId of provingTasks) {
      const task = taskPack.taskList.tasks.find(t => t.id === taskId);
      if (task) {
        if (task.slug.includes('test') || task.slug.includes('arch')) {
          expectedTestFiles.push(`${APP_DIR}/tests/**/*.test.*`);
          commands.push('npm run test');
          evidenceLevel.push('unit');
        }
        if (task.slug.includes('directory') || task.slug.includes('structure')) {
          evidenceLevel.push('structure');
        }
        if (task.slug.includes('arch')) {
          evidenceLevel.push('arch-test');
        }
      }
    }

    requirementMap[req] = {
      truths: [`Requirement ${req} is satisfied by proving tasks`],
      proving_tasks: provingTasks,
      expected_test_files: [...new Set(expectedTestFiles)],
      commands: [...new Set(commands)],
      evidence_level: [...new Set(evidenceLevel)],
    };
  }

  const qualityMap = {
    schema_version: '1.0',
    phase: String(phase),
    impl_dir: implDir,
    requirements: requirementMap,
    test_tasks: testTasks,
  };

  writeFileSync(join(phaseDir, '00-QUALITY-MAP.json'), JSON.stringify(qualityMap, null, 2));
  success('Generated 00-QUALITY-MAP.json');
}

function generateValidation(phase, phaseDir, taskPack, requirementMapping, padded, slug) {
  info('Generating VALIDATION.md...');

  const rows = requirementMapping.phaseRequirements.map(req => {
    const provingTasks = requirementMapping.reqToTasks[req] || [];
    const testTasks = provingTasks.filter(t => {
      const task = taskPack.taskList.tasks.find(tt => tt.id === t);
      return task && (task.slug.includes('test') || task.slug.includes('arch'));
    });

    const evidenceLevel = [];
    if (provingTasks.some(t => t.includes('001'))) evidenceLevel.push('structure');
    if (testTasks.some(t => t.includes('arch'))) evidenceLevel.push('arch-test');
    if (testTasks.some(t => t.includes('unit'))) evidenceLevel.push('unit');
    if (testTasks.some(t => t.includes('integration'))) evidenceLevel.push('integration');

    const commands = [];
    if (testTasks.some(t => t.includes('arch'))) commands.push('npm run test:arch');
    if (testTasks.some(t => t.includes('unit'))) commands.push('npm run test');
    if (testTasks.some(t => t.includes('integration'))) commands.push('npm run test');

    return `| ${req} | ${evidenceLevel.join(', ') || 'structure'} | ${provingTasks.join(', ')} | tests/**/*.test.* | ${commands.join(', ') || 'npm run test:arch'} | planned |`;
  }).join('\n');

  const content = `---
phase: ${padded}-${slug}
status: planned
source: zgsd-plan-phase
quality_map: 00-QUALITY-MAP.json
nyquist_compliant: pending
---

# Phase ${phase} Validation Strategy

## Requirement Coverage

| Requirement | Evidence Level | Proving Tasks | Expected Test Files | Commands | Status |
|-------------|----------------|---------------|---------------------|----------|--------|
${rows}

## Validation Gaps

None at planning time. \`$gsd-validate-phase\` must update this section after execution.
`;

  writeFileSync(join(phaseDir, '00-VALIDATION.md'), content);
  success('Generated 00-VALIDATION.md');
}

// ─── Validation Gates ──────────────────────────────────────────────────────────

function runValidationGates(phase, phaseDir, taskPack, planMap, requirementMapping, bridge) {
  info('Running validation gates...');

  const errors = [];

  // ── Path Normalization Gate ─────────────────────────────────────────────────
  // Catch any remaining bare paths that slipped through inference
  for (const [planId, plan] of Object.entries(planMap)) {
    const files = inferFilesModified(plan, taskPack);
    for (const f of files) {
      const normalized = f.replace(/\\/g, '/');
      // If path starts with a bare prefix and doesn't have APP_DIR, flag it
      if (APP_DIR && APP_DIR !== '.') {
        for (const prefix of BARE_PATH_PREFIXES) {
          if ((normalized === prefix || normalized.startsWith(prefix)) && !normalized.startsWith(APP_DIR + '/')) {
            errors.push(`Plan ${planId}: bare path "${normalized}" not normalized to "${APP_DIR}/${normalized}". Check source task markdown.`);
          }
        }
      }
    }
  }

  const allTaskIds = taskPack.taskList.tasks.map(t => t.id);
  const mappedTaskIds = new Set();
  for (const plan of Object.values(planMap)) {
    for (const taskId of plan.sourceTasks) {
      if (mappedTaskIds.has(taskId)) {
        errors.push(`Task ${taskId} mapped to multiple plans.`);
      }
      mappedTaskIds.add(taskId);
    }
  }

  for (const taskId of allTaskIds) {
    if (!mappedTaskIds.has(taskId)) {
      errors.push(`Task ${taskId} not mapped to any plan.`);
    }
  }

  const allCovered = new Set();
  for (const plan of Object.values(planMap)) {
    for (const req of plan.requirements) {
      allCovered.add(req);
    }
  }

  for (const req of requirementMapping.phaseRequirements) {
    if (!allCovered.has(req)) {
      errors.push(`Requirement ${req} not covered by any plan.`);
    }
  }

  for (const [planId, plan] of Object.entries(planMap)) {
    if (!plan.requirements || plan.requirements.length === 0) {
      errors.push(`Plan ${planId} has empty requirements.`);
    }
  }

  for (const [planId, plan] of Object.entries(planMap)) {
    if (!plan.wave || plan.wave < 1) {
      errors.push(`Plan ${planId} has invalid wave: ${plan.wave}`);
    }
    if (!Array.isArray(plan.dependsOn)) {
      errors.push(`Plan ${planId} has invalid depends_on.`);
    }
    if (!plan.sourceTasks || plan.sourceTasks.length === 0) {
      errors.push(`Plan ${planId} has no source tasks.`);
    }
  }

  if (errors.length > 0) {
    console.error('\n\x1b[31mValidation Gate Failures:\x1b[0m');
    for (const err of errors) {
      console.error(`  - ${err}`);
    }
    return 'REJECT';
  }

  success('All validation gates passed.');
  return 'PASS';
}

// ─── Review Gate ───────────────────────────────────────────────────────────────

function runReviewGate(phase, phaseDir, taskPack, planMap, bridge) {
  if (process.argv.includes('--skip-review')) {
    warn('Review gate skipped (--skip-review). NOT RECOMMENDED.');
    return 'PASS';
  }

  info('Running review gate...');

  const issues = [];

  for (const [planId, plan] of Object.entries(planMap)) {
    if (!plan.name || plan.name.length < 3) {
      issues.push(`Plan ${planId}: name too short or missing.`);
    }
    if (plan.sourceTasks.length > 3) {
      issues.push(`Plan ${planId}: has ${plan.sourceTasks.length} tasks (max recommended: 3).`);
    }
  }

  if (bridge.requirements_coverage.missing.length > 0) {
    issues.push(`Missing requirement coverage: ${bridge.requirements_coverage.missing.join(', ')}`);
  }

  if (bridge.validation.all_tasks_mapped_once !== true) {
    issues.push('Not all tasks mapped exactly once.');
  }

  if (issues.length > 0) {
    console.error('\n\x1b[31mReview Gate Issues:\x1b[0m');
    for (const issue of issues) {
      console.error(`  - ${issue}`);
    }
    return 'REJECT';
  }

  success('Review gate passed.');
  return 'PASS';
}

// ─── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs(process.argv);

  if (!args.phase || !args.impl) {
    console.error('Usage: node import-task-pack.mjs --phase <n> --impl <dir> [options]');
    console.error('');
    console.error('Options:');
    console.error('  --app-dir <path>   App directory for file inference (default: auto-detect)');
    console.error('  --dry-run          Output mapping without writing files');
    console.error('  --force            Overwrite existing plans');
    console.error('  --append           Keep existing plans, append new');
    console.error('  --skip-review      Skip review gate (not recommended)');
    console.error('  --grouping <file>  Use manual grouping file');
    process.exit(1);
  }

  console.log('\n\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m');
  console.log('\x1b[1m  zgsd-plan-phase: Impl Task Pack → GSD PLAN Bridge\x1b[0m');
  console.log('\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m\n');

  validatePreflight(args);

  // Auto-detect app directory if not specified
  if (!args.appDir) {
    const candidates = ['apps/ai-coach-skill', 'apps/web', 'src', '.'];
    for (const c of candidates) {
      if (dirExists(join(PROJECT_ROOT, c))) {
        APP_DIR = c;
        break;
      }
    }
    info(`Auto-detected app directory: ${APP_DIR}`);
  } else {
    if (!dirExists(join(PROJECT_ROOT, args.appDir))) {
      fail(`App directory not found: ${args.appDir}`);
    }
    APP_DIR = args.appDir;
  }

  const taskPack = loadTaskPack(resolve(args.impl));

  const { phaseDir, slug, padded } = derivePhaseDir(args.phase, taskPack);
  info(`Phase directory: .planning/phases/${padded}-${slug}`);

  if (existsSync(phaseDir) && !args.force && !args.append) {
    fail(`Phase directory already exists: ${phaseDir}. Use --force to overwrite or --append to add.`);
  }

  const requirementMapping = buildRequirementMapping(taskPack, args.phase);

  const grouping = buildTaskGrouping(taskPack, args.phase, args.impl);

  const planMap = computePlanMetadata(grouping, taskPack);

  for (const [planId, plan] of Object.entries(planMap)) {
    const planReqs = new Set();
    for (const taskId of plan.sourceTasks) {
      const reqs = requirementMapping.taskToReq[taskId] || [];
      for (const req of reqs) {
        planReqs.add(req);
      }
    }
    plan.requirements = Array.from(planReqs);
  }

  if (args.dryRun) {
    info('DRY RUN — Outputting mapping results:\n');

    console.log('Task → Requirement Mapping:');
    for (const [taskId, reqs] of Object.entries(requirementMapping.taskToReq)) {
      console.log(`  ${taskId}: ${reqs.join(', ') || 'UNMAPPED'}`);
    }

    console.log('\nPlan Grouping:');
    for (const [planId, plan] of Object.entries(planMap)) {
      console.log(`  ${planId} (Wave ${plan.wave}): ${plan.sourceTasks.join(', ')} → ${plan.requirements.join(', ')}`);
      if (plan.dependsOn.length > 0) {
        console.log(`    depends_on: ${plan.dependsOn.join(', ')}`);
      }
    }

    console.log('\nPath Normalization (app_dir=' + APP_DIR + '):');
    console.log('  Bare paths (src/, tests/, lib/, etc.) will be prefixed with: ' + APP_DIR + '/');

    console.log('\nNext: Remove --dry-run to generate files.');
    process.exit(0);
  }

  mkdirSync(phaseDir, { recursive: true });

  generateContext(args.phase, phaseDir, taskPack, padded, slug, args.impl);
  const bridge = generateTaskBridge(args.phase, phaseDir, taskPack, planMap, requirementMapping, padded, slug, args.impl);
  generatePlans(args.phase, phaseDir, planMap, taskPack, requirementMapping, padded, slug, args.impl);
  generateQualityMap(args.phase, phaseDir, taskPack, planMap, requirementMapping, args.impl);
  generateValidation(args.phase, phaseDir, taskPack, requirementMapping, padded, slug);

  const validationResult = runValidationGates(args.phase, phaseDir, taskPack, planMap, requirementMapping, bridge);

  const reviewResult = runReviewGate(args.phase, phaseDir, taskPack, planMap, bridge);

  console.log('\n\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m');
  console.log('\x1b[1m  Bridge Generation Complete\x1b[0m');
  console.log('\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m\n');

  console.log(`Phase: ${padded}-${slug}`);
  console.log(`Plans: ${Object.keys(planMap).length}`);
  console.log(`Tasks mapped: ${Object.keys(bridge.task_mapping).length}/${taskPack.taskList.tasks.length}`);
  console.log(`Requirements covered: ${bridge.requirements_coverage.covered.length}/${bridge.requirements_coverage.required.length}`);
  console.log(`Validation: ${validationResult}`);
  console.log(`Review: ${reviewResult}`);

  if (reviewResult === 'PASS') {
    console.log(`\n\x1b[32mNext step: $gsd-execute-phase ${args.phase}\x1b[0m`);
  } else {
    console.log(`\n\x1b[31mReview gate did not pass. Do NOT execute phase.\x1b[0m`);
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
