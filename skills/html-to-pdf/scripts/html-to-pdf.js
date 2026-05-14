#!/usr/bin/env node
/**
 * html-to-pdf.js
 * Convert HTML file or URL to PDF using local Chrome headless.
 * No npm dependencies — uses system Chrome directly.
 *
 * Usage:
 *   node html-to-pdf.js <input> <output> [format] [options-json]
 *
 * Examples:
 *   node html-to-pdf.js input.html output.pdf
 *   node html-to-pdf.js input.html output.pdf A4 '{"margin":{"top":"26mm","right":"24mm","bottom":"22mm","left":"24mm"}}'
 *   node html-to-pdf.js "https://example.com" output.pdf
 */

import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ─── Find Chrome binary ───────────────────────────────────────────────────────
function findChrome() {
  const candidates = process.platform === 'darwin'
    ? [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
      ]
    : process.platform === 'linux'
    ? [
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/snap/bin/chromium',
      ]
    : [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files\\Chromium\\Application\\chrome.exe',
      ];

  for (const p of candidates) {
    try { if (fs.existsSync(p)) return p; } catch (_) {}
  }
  return null;
}

// ─── Build Chrome CLI args ─────────────────────────────────────────────────────
function buildChromeArgs({ format = 'A4', landscape = false, margin = {}, scale = 1, printBackground = true } = {}) {
  const m = { top: '10mm', right: '10mm', bottom: '10mm', left: '10mm', ...margin };
  const args = [
    '--headless=new',
    '--disable-gpu',
    '--no-pdf-header-footer',
    '--print-to-pdf-no-header',
    `--print-to-pdf-top=${m.top}`,
    `--print-to-pdf-right=${m.right}`,
    `--print-to-pdf-bottom=${m.bottom}`,
    `--print-to-pdf-left=${m.left}`,
  ];
  if (landscape) args.push('--print-to-pdf-landscape');
  if (scale !== 1) args.push(`--print-to-pdf-scale=${Math.round(scale * 100)}`);
  if (!printBackground) args.push('--print-to-pdf-no-background');
  return args;
}

// ─── Convert ────────────────────────────────────────────────────────────────
/**
 * @param {string} input   - HTML file path or http(s):// URL
 * @param {string} output  - Output PDF path (must end with .pdf)
 * @param {object} options
 */
async function convertHtmlToPdf(input, output, options = {}) {
  const {
    format = 'A4',
    landscape = false,
    margin = {},
    scale = 1,
    printBackground = true
  } = options;

  const chrome = findChrome();
  if (!chrome) {
    throw new Error('Chrome not found. Install Google Chrome: https://www.google.com/chrome/');
  }

  const outputAbs = path.resolve(output);
  const outputDir = path.dirname(outputAbs);
  const tmpPdf = `/tmp/html-to-pdf-${Date.now()}.pdf`;

  // Resolve input to absolute path for file:// URLs
  let target = input;
  if (!input.startsWith('http://') && !input.startsWith('https://') && !input.startsWith('file://')) {
    target = path.resolve(input);
    if (!fs.existsSync(target)) throw new Error(`Input file not found: ${target}`);
  }

  const chromeArgs = buildChromeArgs({ format, landscape, margin, scale, printBackground });

  // Build command: chrome [args] --print-to-pdf=<tmp> <target>
  const cmdParts = [`"${chrome}"`, ...chromeArgs, `--print-to-pdf=${tmpPdf}`, `"${target}"`];
  const cmd = cmdParts.join(' ');

  try {
    execSync(cmd, { stdio: 'pipe', timeout: 30000 });
  } catch (err) {
    // Chrome may exit non-zero but still produce the file — check existence
  }

  if (!fs.existsSync(tmpPdf)) {
    throw new Error('Chrome ran but no PDF was produced. Check the HTML file is valid.');
  }

  // Copy to final destination
  fs.copyFileSync(tmpPdf, outputAbs);
  fs.unlinkSync(tmpPdf);
  return { success: true, path: outputAbs };
}

// ─── CLI ────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: html-to-pdf.js <input.html|url> <output.pdf> [format] [options-json]');
  console.error('');
  console.error('Examples:');
  console.error('  html-to-pdf.js report.html report.pdf');
  console.error('  html-to-pdf.js report.html report.pdf A4');
  console.error('  html-to-pdf.js report.html report.pdf A4 \'{"margin":{"top":"26mm","right":"24mm","bottom":"22mm","left":"24mm"}}\'');
  console.error('  html-to-pdf.js "https://example.com" page.pdf');
  process.exit(1);
}

const [input, output, format, optionsJson] = args;
let options = {};
try {
  if (optionsJson) options = JSON.parse(optionsJson);
  if (format) options.format = format;
} catch (err) {
  console.error(`Invalid JSON options: ${err.message}`);
  process.exit(1);
}

convertHtmlToPdf(input, output, options)
  .then(({ path: outPath }) => {
    console.log(`PDF created: ${outPath}`);
    process.exit(0);
  })
  .catch(err => {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  });
