#!/usr/bin/env node

/**
 * validate-bridge.mjs
 *
 * Validates bridge output: TASK-BRIDGE.json schema and PLAN.md contract.
 *
 * Usage:
 *   node validate-bridge.mjs --phase <n>
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, dirname, resolve, basename } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, '../../..');

// ─── CLI Argument Parsing ──────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2);
  const result = { phase: null };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--phase' && args[i + 1]) {
      result.phase = args[++i];
    } else if (/^\d+$/.test(args[i]) && !result.phase) {
      result.phase = args[i];
    }
  }

  return result;
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function fail(msg) {
  console.error(`\x1b[31m[FAIL]\x1b[0m ${msg}`);
}

function warn(msg) {
  console.error(`\x1b[33m[WARN]\x1b[0m ${msg}`);
}

function success(msg) {
  console.log(`\x1b[32m[PASS]\x1b[0m ${msg}`);
}

function info(msg) {
  console.log(`\x1b[36m[INFO]\x1b[0m ${msg}`);
}

function fileExists(path) {
  return existsSync(path) && statSync(path).isFile();
}

function readFile(path) {
  return readFileSync(path, 'utf-8');
}

// ─── Bridge Manifest Validation ────────────────────────────────────────────────

function validateBridgeManifest(bridgePath) {
  info('Validating TASK-BRIDGE.json schema...');

  const errors = [];

  let bridge;
  try {
    bridge = JSON.parse(readFile(bridgePath));
  } catch (e) {
    errors.push(`Invalid JSON: ${e.message}`);
    return { valid: false, errors, bridge: null };
  }

  // schema_version
  if (bridge.schema_version !== '1.0') {
    errors.push(`schema_version must be "1.0", got "${bridge.schema_version}"`);
  }

  // required top-level fields
  const required = ['phase', 'phase_dir', 'impl_dir', 'feature_id', 'source_hash', 'generated_at'];
  for (const field of required) {
    if (!bridge[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // source_hash format
  if (bridge.source_hash && !bridge.source_hash.startsWith('sha256:')) {
    errors.push(`source_hash must start with "sha256:", got "${bridge.source_hash.slice(0, 20)}..."`);
  }

  // dag
  if (!bridge.dag) {
    errors.push('Missing dag object');
  } else {
    if (bridge.dag.status !== 'PASS' && bridge.dag.status !== 'FAIL') {
      errors.push(`dag.status must be "PASS" or "FAIL", got "${bridge.dag.status}"`);
    }
    if (!Array.isArray(bridge.dag.topological_order)) {
      errors.push('dag.topological_order must be an array');
    }
  }

  // requirements_coverage
  if (!bridge.requirements_coverage) {
    errors.push('Missing requirements_coverage object');
  } else {
    const rc = bridge.requirements_coverage;
    if (!Array.isArray(rc.required)) errors.push('requirements_coverage.required must be an array');
    if (!Array.isArray(rc.covered)) errors.push('requirements_coverage.covered must be an array');
    if (!Array.isArray(rc.missing)) errors.push('requirements_coverage.missing must be an array');

    if (Array.isArray(rc.required) && Array.isArray(rc.covered)) {
      const missing = rc.required.filter(r => !rc.covered.includes(r));
      if (missing.length > 0) {
        errors.push(`requirements_coverage.missing is inconsistent: ${missing.join(', ')}`);
      }
    }
  }

  // plans
  if (!Array.isArray(bridge.plans)) {
    errors.push('plans must be an array');
  } else {
    for (let i = 0; i < bridge.plans.length; i++) {
      const plan = bridge.plans[i];
      if (!plan.plan_id) errors.push(`plans[${i}]: missing plan_id`);
      if (!plan.wave || plan.wave < 1) errors.push(`plans[${i}]: invalid wave ${plan.wave}`);
      if (!Array.isArray(plan.source_tasks) || plan.source_tasks.length === 0) {
        errors.push(`plans[${i}]: source_tasks must be non-empty array`);
      }
      if (!Array.isArray(plan.requirements) || plan.requirements.length === 0) {
        errors.push(`plans[${i}]: requirements must be non-empty array`);
      }
      if (!Array.isArray(plan.depends_on)) {
        errors.push(`plans[${i}]: depends_on must be an array`);
      }
    }
  }

  // task_mapping
  if (!bridge.task_mapping || typeof bridge.task_mapping !== 'object') {
    errors.push('task_mapping must be an object');
  } else {
    for (const [taskId, mapping] of Object.entries(bridge.task_mapping)) {
      if (!mapping.plan_id) errors.push(`task_mapping.${taskId}: missing plan_id`);
      if (!mapping.task_file) errors.push(`task_mapping.${taskId}: missing task_file`);
      if (!['mapped', 'unmapped', 'error'].includes(mapping.status)) {
        errors.push(`task_mapping.${taskId}: invalid status "${mapping.status}"`);
      }
    }
  }

  // validation flags
  if (!bridge.validation) {
    errors.push('Missing validation object');
  } else {
    const v = bridge.validation;
    if (typeof v.all_tasks_mapped_once !== 'boolean') {
      errors.push('validation.all_tasks_mapped_once must be boolean');
    }
    if (typeof v.plan_dependencies_respect_task_dag !== 'boolean') {
      errors.push('validation.plan_dependencies_respect_task_dag must be boolean');
    }
    if (typeof v.same_wave_file_overlap !== 'boolean') {
      errors.push('validation.same_wave_file_overlap must be boolean');
    }
  }

  if (errors.length === 0) {
    success('TASK-BRIDGE.json schema valid.');
  } else {
    for (const err of errors) {
      fail(`Bridge: ${err}`);
    }
  }

  return { valid: errors.length === 0, errors, bridge };
}

// ─── PLAN Contract Validation ──────────────────────────────────────────────────

function validatePlanContract(planPath) {
  const errors = [];
  let content;

  try {
    content = readFile(planPath);
  } catch (e) {
    errors.push(`Cannot read file: ${e.message}`);
    return errors;
  }

  // Frontmatter validation
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) {
    errors.push('Missing YAML frontmatter (--- delimiters)');
    return errors;
  }

  const fm = fmMatch[1];

  const requiredFrontmatter = ['phase', 'plan', 'type', 'wave', 'depends_on', 'files_modified', 'autonomous', 'requirements'];
  for (const field of requiredFrontmatter) {
    const re = new RegExp(`^${field}:`, 'm');
    if (!re.test(fm)) {
      errors.push(`Frontmatter missing required field: ${field}`);
    }
  }

  // Must be type: execute
  const typeMatch = fm.match(/^type:\s*(.+)/m);
  if (!typeMatch || typeMatch[1].trim() !== 'execute') {
    errors.push(`Frontmatter type must be "execute"`);
  }

  // Wave must be positive integer
  const waveMatch = fm.match(/^wave:\s*(\d+)/m);
  if (!waveMatch) {
    errors.push('Frontmatter wave must be a positive integer');
  } else if (Number(waveMatch[1]) < 1) {
    errors.push(`Frontmatter wave must be >= 1, got ${waveMatch[1]}`);
  }

  // XML task validation
  const body = content.slice(fmMatch[0].length).trim();

  const requiredSections = ['objective', 'tasks', 'verification', 'success.?criteria'];
  for (const section of requiredSections) {
    const re = new RegExp(`##\\s+${section}`, 'i');
    if (!re.test(body)) {
      errors.push(`Body missing required section: ## ${section}`);
    }
  }

  // XML tasks
  const taskRegex = /<task>[\s\S]*?<\/task>/g;
  const tasks = body.match(taskRegex) || [];

  if (tasks.length === 0) {
    errors.push('No <task> XML elements found in body');
  }

  const requiredXmlElements = ['name', 'files', 'read_first', 'action', 'verify', 'acceptance_criteria', 'done'];

  for (let i = 0; i < tasks.length; i++) {
    const task = tasks[i];
    for (const elem of requiredXmlElements) {
      const re = new RegExp(`<${elem}>[\\s\\S]*?</${elem}>`);
      if (!re.test(task)) {
        errors.push(`Task ${i + 1}: missing <${elem}> element`);
      }
    }

    // name must not be empty
    const nameMatch = task.match(/<name>([\s\S]*?)<\/name>/);
    if (nameMatch && !nameMatch[1].trim()) {
      errors.push(`Task ${i + 1}: <name> is empty`);
    }

    // must have at least one <file> in <files>
    const filesBlock = task.match(/<files>([\s\S]*?)<\/files>/);
    if (filesBlock && !/<file>/.test(filesBlock[1])) {
      errors.push(`Task ${i + 1}: <files> has no <file> elements`);
    }

    // must have at least one <command> in <verify>
    const verifyBlock = task.match(/<verify>([\s\S]*?)<\/verify>/);
    if (verifyBlock && !/<command>/.test(verifyBlock[1])) {
      errors.push(`Task ${i + 1}: <verify> has no <command> elements`);
    }

    // acceptance_criteria must have at least one item
    const acBlock = task.match(/<acceptance_criteria>([\s\S]*?)<\/acceptance_criteria>/);
    if (acBlock && !acBlock[1].trim()) {
      errors.push(`Task ${i + 1}: <acceptance_criteria> is empty`);
    }
  }

  if (errors.length === 0) {
    success(`${basename(planPath)}: PLAN contract valid (${tasks.length} tasks).`);
  } else {
    for (const err of errors) {
      fail(`${basename(planPath)}: ${err}`);
    }
  }

  return errors;
}

// ─── Main ──────────────────────────────────────────────────────────────────────

function main() {
  const args = parseArgs(process.argv);

  if (!args.phase) {
    console.error('Usage: node validate-bridge.mjs --phase <n>');
    process.exit(1);
  }

  console.log('\n\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m');
  console.log('\x1b[1m  zgsd-plan-phase: Bridge Validation\x1b[0m');
  console.log('\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m\n');

  const padded = String(args.phase).padStart(2, '0');

  // Find phase directory
  const phasesDir = join(PROJECT_ROOT, '.planning/phases');
  if (!existsSync(phasesDir)) {
    fail('.planning/phases/ directory not found');
    process.exit(1);
  }

  const phaseDirs = readdirSync(phasesDir).filter(d => d.startsWith(`${padded}-`));
  if (phaseDirs.length === 0) {
    fail(`No phase directory found matching ${padded}-*`);
    process.exit(1);
  }

  const phaseDir = join(phasesDir, phaseDirs[0]);
  info(`Phase directory: ${phaseDirs[0]}`);

  let allValid = true;

  // Validate TASK-BRIDGE.json
  const bridgePath = join(phaseDir, `${padded}-TASK-BRIDGE.json`);
  if (!fileExists(bridgePath)) {
    fail(`${padded}-TASK-BRIDGE.json not found`);
    allValid = false;
  } else {
    const { valid } = validateBridgeManifest(bridgePath);
    if (!valid) allValid = false;
  }

  // Validate PLAN.md files
  const planFiles = readdirSync(phaseDir).filter(f => f.endsWith('-PLAN.md')).sort();
  if (planFiles.length === 0) {
    warn('No PLAN.md files found in phase directory');
  } else {
    info(`\nValidating ${planFiles.length} PLAN.md files...`);
    let planErrors = 0;
    for (const pf of planFiles) {
      const errs = validatePlanContract(join(phaseDir, pf));
      planErrors += errs.length;
    }
    if (planErrors > 0) allValid = false;
  }

  // Summary
  console.log('\n\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m');
  if (allValid) {
    success('\x1b[1mAll bridge validations passed.\x1b[0m');
  } else {
    fail('\x1b[1mBridge validation FAILED. Fix errors above.\x1b[0m');
    process.exit(1);
  }
  console.log('\x1b[1m═══════════════════════════════════════════════════════════════\x1b[0m\n');
}

main();
