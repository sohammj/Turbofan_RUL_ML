import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const skill = '/Users/soham/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const runtime = '/Users/soham/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(runtime, 'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const { finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const work = path.join(project, '.presentation-build');
const deliverable = path.join(project, 'deliverables', 'FINAL_PROJECT_PRESENTATION.pptx');
const buildId = Date.now();
const final = path.join(work, 'final', `FINAL_PROJECT_PRESENTATION-${buildId}.pptx`);
await fs.mkdir(work, { recursive: true });
await fs.mkdir(path.dirname(final), { recursive: true });
await fs.mkdir(path.dirname(deliverable), { recursive: true });

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const navy = '#172B42';
const gray = '#3D4854';

function text(slide, value, x, y, w, h, size = 24, bold = false, color = gray) {
  const shape = slide.shapes.add({
    geometry: 'textbox',
    position: { left: x, top: y, width: w, height: h },
    fill: 'none',
    line: { style: 'solid', fill: 'none', width: 0 },
  });
  shape.text = value;
  shape.text.style = { fontFamily: 'Aptos', fontSize: size, bold, color };
  return shape;
}

function slide(title, notes) {
  const s = deck.slides.add();
  s.background.fill = '#FFFFFF';
  text(s, title, 70, 52, 1140, 86, 34, true, navy);
  s.speakerNotes.text = notes;
  return s;
}

async function image(slide, relativePath, x, y, w, h, alt) {
  const bytes = await fs.readFile(path.join(project, relativePath));
  slide.images.add({
    blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    contentType: 'image/png',
    alt,
    fit: 'contain',
    position: { left: x, top: y, width: w, height: h },
  });
}

{
  const s = deck.slides.add();
  s.background.fill = '#FFFFFF';
  text(s, 'Predictive Remaining Useful Life Estimation', 70, 150, 1130, 120, 46, true, navy);
  text(s, 'NASA C-MAPSS turbofan engines', 70, 300, 1120, 60, 29, false, gray);
  text(s, 'Final academic machine learning project', 70, 394, 1120, 48, 22, false, gray);
  s.speakerNotes.text = 'Source: NASA C-MAPSS data and Saxena et al. (2008), DOI 10.1109/PHM.2008.4711414. The data are simulated, not live aircraft measurements.';
}

{
  const s = slide('Dataset and prediction target', 'Source: docs/SOURCE_PROVENANCE.md and reports/dataset_summary.csv. FD001–FD004 are the modeled subsets; the original PHM08 challenge train.txt package is distinct.');
  text(s, '26 raw fields per cycle', 80, 168, 460, 45, 28, true, navy);
  text(s, 'Engine ID, cycle, 3 operating settings, 21 sensors', 80, 220, 1080, 45, 23);
  text(s, 'Training trajectories run to failure', 80, 316, 1050, 40, 27, true, navy);
  text(s, 'Test trajectories stop early. Predict remaining cycles at the last observed cycle.', 80, 370, 1060, 78, 23);
  text(s, 'Four subsets: FD001, FD002, FD003, FD004', 80, 520, 1070, 45, 23);
}

{
  const s = slide('Preprocessing and leakage controls', 'Source: src/cmapss_pipeline.py, reports/PREPROCESSING_SUMMARY.md, docs/MODELING_PROTOCOL.md. Modeling reloads raw data and fits feature selection inside the engine-wise split.');
  text(s, 'Raw data checks', 80, 174, 400, 42, 27, true, navy);
  text(s, 'Missing values, duplicates, engine-cycle keys, numeric types and cycle order', 80, 226, 1080, 70, 22);
  text(s, 'RUL label', 80, 335, 400, 42, 27, true, navy);
  text(s, 'Final training cycle minus current cycle. Official test RUL is an evaluation label.', 80, 387, 1080, 70, 22);
  text(s, 'Leakage boundary', 80, 500, 400, 42, 27, true, navy);
  text(s, 'Split by engine. Use only current and earlier sensor readings. Never use RUL as an input.', 80, 552, 1080, 70, 22);
}

{
  const s = slide('Model selection protocol', 'Source: docs/MODELING_PROTOCOL.md. The candidates are the median baseline, Ridge regression, Random Forest and Histogram Gradient Boosting. The official test answers are excluded from model selection.');
  text(s, '1  Hold out 20% of training engines', 80, 178, 1110, 45, 26);
  text(s, '2  Choose one partial-history endpoint per held-out engine', 80, 259, 1110, 55, 26);
  text(s, '3  Compare models using validation RMSE', 80, 354, 1110, 45, 26);
  text(s, '4  Refit the winner on all training engines', 80, 438, 1110, 45, 26);
  text(s, '5  Evaluate once on official test endpoints', 80, 522, 1110, 45, 26);
}

{
  const s = slide('Official test results', 'Source: reports/modeling/official_test_summary.csv. RMSE and MAE are measured in cycles. The selected model was chosen on validation data before official-test evaluation.');
  const headers = ['Subset', 'Selected model', 'MAE', 'RMSE', 'R²'];
  const rows = [
    ['FD001', 'Random Forest', '21.21', '28.68', '0.52'],
    ['FD002', 'Histogram Gradient Boosting', '20.27', '27.66', '0.74'],
    ['FD003', 'Histogram Gradient Boosting', '23.89', '34.81', '0.29'],
    ['FD004', 'Histogram Gradient Boosting', '27.72', '38.50', '0.50'],
  ];
  const xs = [80, 260, 760, 920, 1080];
  const widths = [145, 480, 115, 115, 95];
  headers.forEach((h, i) => text(s, h, xs[i], 190, widths[i], 45, 23, true, navy));
  rows.forEach((row, r) => row.forEach((cell, i) => text(s, cell, xs[i], 276 + r * 79, widths[i], 70, i === 1 ? 19 : 23, false, gray)));
  text(s, 'Lower MAE and RMSE are better. These are benchmark results, not deployment guarantees.', 80, 627, 1120, 45, 19);
}

{
  const s = slide('Predicted versus actual RUL', 'Source: reports/modeling/FD001/official_test_actual_vs_predicted.png and reports/modeling/FD002/official_test_actual_vs_predicted.png. Each point is one official test engine.');
  await image(s, 'reports/modeling/FD001/official_test_actual_vs_predicted.png', 50, 155, 580, 455, 'FD001 actual versus predicted RUL');
  await image(s, 'reports/modeling/FD002/official_test_actual_vs_predicted.png', 650, 155, 580, 455, 'FD002 actual versus predicted RUL');
  text(s, 'FD001', 298, 623, 160, 35, 20, true, navy);
  text(s, 'FD002', 898, 623, 160, 35, 20, true, navy);
}

{
  const s = slide('Error analysis', 'Source: reports/modeling/error_direction_counts.csv and reports/modeling/error_by_rul_band.png. Overestimation means predicted remaining life exceeds actual remaining life.');
  await image(s, 'reports/modeling/error_by_rul_band.png', 75, 147, 755, 505, 'Official test error by RUL band');
  text(s, 'Overestimated life', 865, 206, 345, 45, 27, true, navy);
  text(s, 'FD001  65 / 100', 865, 281, 300, 38, 22);
  text(s, 'FD002  150 / 259', 865, 340, 300, 38, 22);
  text(s, 'FD003  76 / 100', 865, 399, 300, 38, 22);
  text(s, 'FD004  175 / 248', 865, 458, 300, 38, 22);
  text(s, 'Large individual errors remain.', 865, 548, 310, 70, 20);
}

{
  const s = slide('Robustness and limits', 'Source: docs/ROBUSTNESS_ANALYSIS.md and reports/robustness/repeated_validation_rmse.png. This post-hoc audit uses three training-only engine splits and fixed 50%, 70%, 85% endpoints. It does not alter the official-test model choices.');
  await image(s, 'reports/robustness/repeated_validation_rmse.png', 55, 158, 760, 472, 'Mean repeated validation RMSE by model and subset');
  text(s, 'FD002 and FD004 change mean-RMSE leader under this audit.', 845, 211, 365, 125, 22, true, navy);
  text(s, 'Three repeats show sensitivity, not a confidence interval.', 845, 365, 365, 100, 21);
  text(s, 'Simulated data and late-life overestimates prevent safety claims.', 845, 508, 365, 100, 21);
}

{
  const s = slide('Team presentation responsibilities', 'Source: dated group study report and deliverables/FINAL_PROJECT_REPORT.docx. These are assigned presentation roles, not independently verified authorship of files or experiments.');
  const roles = [
    ['Soham', 'Project flow, model-selection decision and scores'],
    ['Hardik', 'Dataset, 26 fields and RUL target'],
    ['Farhaan', 'Data cleaning and causal sensor features'],
    ['Sanjeet', 'Candidate models and FD001 validation'],
    ['Sparsh', 'FD001/FD002 prediction plots and limitations'],
  ];
  roles.forEach(([name, role], index) => {
    const y = 166 + index * 92;
    text(s, name, 84, y, 240, 50, 27, true, navy);
    text(s, role, 338, y, 840, 65, 23, false, gray);
  });
  text(s, 'Presentation split from the earlier group study report', 84, 634, 1090, 32, 18);
}

const candidate = path.join(work, 'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const result = await finalizePresentation({
  workspaceDir: project,
  candidatePath: candidate,
  finalPath: final,
  pythonExecutable: path.join(runtime, 'python/bin/python3'),
  integrityValidatorPath: path.join(skill, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(skill, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '12192000,6858000', '--validate-heading-fit'],
  explicitTotalSlideCount: 9,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: { basis: 'design', families: ['Aptos'] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(work, `validation-${buildId}.json`),
});
await fs.copyFile(final, deliverable);
for (const [index, s] of deck.slides.items.entries()) {
  const png = await deck.export({ slide: s, format: 'png', scale: 1 });
  await fs.writeFile(path.join(work, `slide-${String(index + 1).padStart(2, '0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log(JSON.stringify({ deliverable, result }, null, 2));
