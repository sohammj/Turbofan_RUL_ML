import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const skill = '/Users/soham/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const runtime = '/Users/soham/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(runtime, 'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const { finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const work = path.join(project, '.presentation-build', 'group-activity');
const output = path.join(project, 'deliverables', 'FINAL_ML_PRESENTATION.pptx');
const staged = path.join(work, 'final', `FINAL_ML_PRESENTATION-${Date.now()}.pptx`);
await fs.mkdir(path.dirname(staged), { recursive: true });
await fs.mkdir(path.dirname(output), { recursive: true });

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const ink = '#172B42';
const copy = '#344454';
const muted = '#5A6875';
const accent = '#2A668D';

function text(slide, value, x, y, w, h, size = 24, bold = false, color = copy, align = 'left') {
  const shape = slide.shapes.add({
    geometry: 'textbox',
    position: { left: x, top: y, width: w, height: h },
    fill: 'none',
    line: { style: 'solid', fill: 'none', width: 0 },
  });
  shape.text = value;
  shape.text.style = { fontFamily: 'Aptos', fontSize: size, bold, color, alignment: align };
  return shape;
}

function slide(title, notes) {
  const s = deck.slides.add();
  s.background.fill = '#FFFFFF';
  text(s, title, 70, 46, 1140, 82, 35, true, ink);
  s.speakerNotes.text = notes;
  return s;
}

async function image(s, relative, x, y, w, h, alt) {
  const bytes = await fs.readFile(path.join(project, relative));
  s.images.add({
    blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    contentType: 'image/png', alt, fit: 'contain',
    position: { left: x, top: y, width: w, height: h },
  });
}

function row(s, cells, y, widths, sizes, bold = false, color = copy) {
  let x = 78;
  cells.forEach((cell, i) => {
    text(s, cell, x, y, widths[i] - 12, 58, sizes[i] ?? 22, bold, color);
    x += widths[i];
  });
}

{
  const s = deck.slides.add();
  s.background.fill = '#FFFFFF';
  text(s, 'Predictive Remaining Useful Life\nEstimation of Aircraft Turbofan Engines', 70, 132, 1140, 150, 45, true, ink);
  text(s, 'Machine Learning Group Activity Presentation', 72, 323, 1110, 45, 27, false, accent);
  text(s, 'B Tech Computer Science and Engineering Data Science  |  Semester V', 72, 425, 1120, 65, 22, false, copy);
  text(s, 'Mentor: Abhay Kolhe', 72, 520, 1050, 38, 22, false, muted);
  s.speakerNotes.text = 'Based on deliverables/FINAL_ML_REPORT.docx, supplied by the group. Team name, course code, academic year and submission date remain unfilled in the report. Farhaan and Sanjeet roll numbers are also blank.';
}

{
  const s = slide('Problem and objective', 'Source: GROUP_ACTIVITY_REPORT_SOURCE.md, sections 2 and 5. The NASA C-MAPSS data are simulated.');
  text(s, 'Question', 82, 166, 270, 42, 27, true, ink);
  text(s, 'Given an engine’s sensor history up to today, how many operating cycles remain before simulated failure?', 82, 221, 1070, 130, 30);
  text(s, 'Learning task', 82, 395, 350, 42, 27, true, ink);
  text(s, 'Supervised regression. One numerical RUL prediction is evaluated at the final observed cycle of each official test engine.', 82, 450, 1070, 140, 25);
}

{
  const s = slide('Dataset and source files', 'Source: NASA C-MAPSS, docs/SOURCE_PROVENANCE.md, reports/dataset_summary.csv. The FD001–FD004 package differs from the PHM08 challenge train.txt package.');
  text(s, 'Four subsets', 82, 155, 350, 40, 27, true, ink);
  text(s, 'FD001 and FD003: one operating condition\nFD002 and FD004: six operating conditions', 82, 205, 1080, 110, 25);
  text(s, 'Each raw row has 26 numeric fields', 82, 345, 1080, 42, 27, true, ink);
  text(s, 'Engine ID, cycle, 3 operating settings and 21 sensor measurements', 82, 398, 1080, 55, 25);
  text(s, 'Training trajectories reach failure. Test trajectories stop early. A separate RUL file supplies one answer per test engine.', 82, 514, 1080, 125, 23);
}

{
  const s = slide('Dataset size', 'Source: reports/dataset_summary.csv. Counts refer to rows and distinct engines, not independent row samples.');
  row(s, ['Subset', 'Train rows', 'Train engines', 'Test rows', 'Test engines'], 170, [190, 220, 250, 220, 240], [23, 23, 23, 23, 23], true, ink);
  const data = [
    ['FD001', '20,631', '100', '13,096', '100'],
    ['FD002', '53,759', '260', '33,991', '259'],
    ['FD003', '24,720', '100', '16,596', '100'],
    ['FD004', '61,249', '249', '41,214', '248'],
  ];
  data.forEach((values, i) => row(s, values, 250 + i * 78, [190, 220, 250, 220, 240], [25, 25, 25, 25, 25]));
  text(s, 'The official test evaluates one endpoint per engine.', 80, 620, 1100, 40, 20, false, muted);
}

{
  const s = slide('Exploratory data analysis', 'Source: reports/eda/engine_lifetimes.png and GROUP_ACTIVITY_REPORT_SOURCE.md, section 7.1.');
  await image(s, 'reports/eda/engine_lifetimes.png', 65, 150, 750, 480, 'Distribution of full training engine lifetimes by subset');
  text(s, 'Median training lifetime', 850, 198, 350, 45, 26, true, ink);
  text(s, 'FD001  199 cycles\nFD002  199 cycles\nFD003  220.5 cycles\nFD004  234 cycles', 850, 280, 340, 230, 24);
  text(s, 'Lifetime varies by engine, so rows from the same engine stay together during validation.', 850, 545, 345, 102, 20);
}

{
  const s = slide('Preprocessing and feature engineering', 'Source: src/cmapss_pipeline.py, train_models.py, GROUP_ACTIVITY_REPORT_SOURCE.md, section 6.3.');
  text(s, 'Quality checks', 82, 158, 330, 42, 27, true, ink);
  text(s, 'Numeric types, missing values, duplicates and engine-cycle order', 82, 208, 1100, 75, 24);
  text(s, 'Training RUL', 82, 314, 330, 42, 27, true, ink);
  text(s, 'Final training cycle minus current cycle', 82, 364, 1050, 60, 24);
  text(s, 'Predictors', 82, 460, 330, 42, 27, true, ink);
  text(s, 'Cycle, operating settings, retained sensors, one-cycle changes and five-cycle rolling means. Temporal features use current and earlier cycles only.', 82, 513, 1100, 120, 23);
}

{
  const s = slide('Model selection protocol', 'Source: train_models.py and GROUP_ACTIVITY_REPORT_SOURCE.md, sections 6.4–6.7. Engine ID is a grouping key, not a model input.');
  const steps = [
    '1  Hold out 20% of training engines',
    '2  Predict one partial-history endpoint per held-out engine',
    '3  Select the lowest validation RMSE within each subset',
    '4  Refit the selected model on all training engines',
    '5  Evaluate once at official test endpoints',
  ];
  steps.forEach((value, i) => text(s, value, 84, 166 + i * 89, 1100, 60, 25));
}

{
  const s = slide('Models compared', 'Source: train_models.py and GROUP_ACTIVITY_REPORT_SOURCE.md, section 6.4. Settings were fixed before official-test evaluation.');
  const items = [
    ['Median baseline', 'Constant median RUL reference'],
    ['Ridge regression', 'Regularized linear model with training-only scaling'],
    ['Random Forest', '80 regression trees with averaging'],
    ['Histogram Gradient Boosting', 'Sequential regression trees, 150 iterations'],
  ];
  items.forEach(([name, desc], i) => {
    const y = 163 + i * 118;
    text(s, name, 82, y, 480, 46, 28, true, ink);
    text(s, desc, 82, y + 49, 1080, 60, 23);
  });
}

{
  const s = slide('Validation RMSE and selected models', 'Source: reports/modeling/FD00X/validation_metrics.csv. Units are cycles. A lower RMSE is better.');
  row(s, ['Subset', 'Median', 'Ridge', 'Forest', 'Boosting', 'Selected'], 162, [145, 160, 160, 160, 190, 300], [21, 21, 21, 21, 21, 21], true, ink);
  const rows = [
    ['FD001', '47.51', '32.93', '27.17', '27.31', 'Forest'],
    ['FD002', '47.55', '41.37', '33.14', '32.16', 'Boosting'],
    ['FD003', '67.43', '53.09', '28.13', '24.87', 'Boosting'],
    ['FD004', '58.79', '56.47', '45.38', '45.19', 'Boosting'],
  ];
  rows.forEach((values, i) => row(s, values, 247 + i * 76, [145, 160, 160, 160, 190, 300], [22, 22, 22, 22, 22, 22]));
  text(s, 'The FD001 forest lead is only 0.14 cycles; FD004’s boosting lead is about 0.19 cycles.', 80, 616, 1110, 55, 20, false, muted);
}

{
  const s = slide('Official test results', 'Source: reports/modeling/official_test_summary.csv. The selected models were chosen on validation data. MAE and RMSE are in cycles.');
  row(s, ['Subset', 'Selected model', 'MAE', 'RMSE', 'R²'], 162, [160, 520, 155, 155, 130], [22, 22, 22, 22, 22], true, ink);
  const rows = [
    ['FD001', 'Random Forest', '21.21', '28.68', '0.52'],
    ['FD002', 'Histogram Gradient Boosting', '20.27', '27.66', '0.74'],
    ['FD003', 'Histogram Gradient Boosting', '23.89', '34.81', '0.29'],
    ['FD004', 'Histogram Gradient Boosting', '27.72', '38.50', '0.50'],
  ];
  rows.forEach((values, i) => row(s, values, 247 + i * 76, [160, 520, 155, 155, 130], [23, 21, 23, 23, 23]));
  text(s, 'These scores describe simulated benchmark engines, not a maintenance-ready system.', 80, 619, 1110, 45, 20, false, muted);
}

{
  const s = slide('FD001 and FD002 prediction plots', 'Source: reports/modeling/FD001/official_test_actual_vs_predicted.png and FD002 equivalent. Each dot is one official test engine.');
  await image(s, 'reports/modeling/FD001/official_test_actual_vs_predicted.png', 48, 145, 580, 485, 'FD001 actual versus predicted RUL');
  await image(s, 'reports/modeling/FD002/official_test_actual_vs_predicted.png', 652, 145, 580, 485, 'FD002 actual versus predicted RUL');
  text(s, 'FD001', 288, 635, 160, 35, 21, true, ink);
  text(s, 'FD002', 890, 635, 160, 35, 21, true, ink);
}

{
  const s = slide('FD003 and FD004 prediction plots', 'Source: reports/modeling/FD003/official_test_actual_vs_predicted.png and FD004 equivalent. The dashed diagonal is exact prediction.');
  await image(s, 'reports/modeling/FD003/official_test_actual_vs_predicted.png', 48, 145, 580, 485, 'FD003 actual versus predicted RUL');
  await image(s, 'reports/modeling/FD004/official_test_actual_vs_predicted.png', 652, 145, 580, 485, 'FD004 actual versus predicted RUL');
  text(s, 'FD003', 288, 635, 160, 35, 21, true, ink);
  text(s, 'FD004', 890, 635, 160, 35, 21, true, ink);
}

{
  const s = slide('Error direction', 'Source: reports/modeling/error_direction_counts.csv and error_by_rul_band.png. Overestimation means predicted RUL exceeds true RUL.');
  await image(s, 'reports/modeling/error_by_rul_band.png', 60, 150, 760, 485, 'Mean absolute error by true RUL band');
  text(s, 'Engines with overestimated life', 850, 195, 350, 80, 25, true, ink);
  text(s, 'FD001  65 / 100\nFD002  150 / 259\nFD003  76 / 100\nFD004  175 / 248', 850, 307, 350, 260, 23);
  text(s, 'Late predictions would matter most in a maintenance setting.', 850, 570, 350, 70, 20);
}

{
  const s = slide('Robustness audit', 'Source: reports/robustness/repeated_validation_rmse.png. Three training-only splits with endpoints at 50%, 70% and 85% of lifetime. This audit did not change official-test selections.');
  await image(s, 'reports/robustness/repeated_validation_rmse.png', 55, 150, 760, 490, 'Repeated validation RMSE by model and subset');
  text(s, 'FD002 and FD004 change mean-RMSE leader in this later audit.', 845, 215, 355, 125, 24, true, ink);
  text(s, 'Three repetitions show sensitivity. They do not provide a confidence interval.', 845, 405, 355, 120, 22);
}

{
  const s = slide('Research context and limitations', 'Source: GROUP_ACTIVITY_REPORT_SOURCE.md, sections 3, 4 and 7.6–7.8. Key literature: Saxena et al. 2008 DOI 10.1109/PHM.2008.4711414; Ramasso and Saxena 2014 DOI 10.36001/ijphm.2014.v5i2.2236; Liu et al. 2023 DOI 10.3390/aerospace10080715.');
  text(s, 'Literature survey', 80, 156, 480, 44, 27, true, ink);
  text(s, '13 studies cover benchmark design, deep sequence models, feature engineering, uncertainty and explainability.', 80, 207, 1100, 92, 24);
  text(s, 'What our results cannot establish', 80, 340, 800, 44, 27, true, ink);
  text(s, 'Published scores use different targets and protocols. C-MAPSS is simulated. One original validation split and frequent overestimation limit conclusions.', 80, 396, 1100, 151, 24);
  text(s, 'No real-aircraft safety or deployment claim follows from these scores.', 80, 600, 1100, 46, 21, false, muted);
}

{
  const s = slide('Conclusion and next steps', 'Source: GROUP_ACTIVITY_REPORT_SOURCE.md, sections 8 and 9. Future work is proposed, not completed.');
  text(s, 'Completed', 80, 160, 300, 44, 27, true, ink);
  text(s, 'Preserved raw data, checked quality, engineered causal features, compared four regressors and evaluated all four subsets on official test engines.', 80, 216, 1100, 132, 25);
  text(s, 'Next research steps', 80, 386, 500, 44, 27, true, ink);
  text(s, 'Repeated nested engine-wise validation, engine-balanced training, calibrated uncertainty and external data evaluation.', 80, 441, 1100, 130, 25);
  text(s, 'Repository: github.com/sohammj/Turbofan_RUL_ML', 80, 623, 1100, 42, 20, false, muted);
}

{
  const s = slide('Group contribution assignment', 'Source: deliverables/FINAL_ML_REPORT.docx, Declaration and individual contribution table. This slide reproduces the updated report assignment. The report still describes the allocation as proposed and requires member confirmation before submission.');
  const roles = [
    ['Farhaan', 'Data quality, preprocessing, RUL label checks, and causal feature engineering.'],
    ['Sanjeet', 'Candidate model explanation, validation comparison, experiment protocol and reproducibility checks.'],
    ['Sparsh', 'Official-test evaluation, prediction plots, error analysis, limitations, and presentation figures.'],
    ['Soham', 'Project integration, model training, final result interpretation, and report coordination.'],
    ['Hardik', 'Dataset provenance, data dictionary, raw data inspection, and EDA interpretation.'],
  ];
  roles.forEach(([name, role], i) => {
    const y = 154 + i * 92;
    text(s, name, 80, y, 230, 48, 27, true, ink);
    text(s, role, 310, y, 880, 65, 22);
  });
  text(s, 'Confirm actual work and fill missing roll numbers before submission.', 80, 632, 1100, 38, 19, false, muted);
}

const candidate = path.join(work, 'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const result = await finalizePresentation({
  workspaceDir: project,
  candidatePath: candidate,
  finalPath: staged,
  pythonExecutable: path.join(runtime, 'python/bin/python3'),
  integrityValidatorPath: path.join(skill, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(skill, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '12192000,6858000', '--validate-heading-fit'],
  explicitTotalSlideCount: 17,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: { basis: 'design', families: ['Aptos'] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(work, `validation-${Date.now()}.json`),
});
await fs.copyFile(staged, output);
for (const [index, s] of deck.slides.items.entries()) {
  const png = await deck.export({ slide: s, format: 'png', scale: 1 });
  await fs.writeFile(path.join(work, `slide-${String(index + 1).padStart(2, '0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log(JSON.stringify({ output, result }, null, 2));
