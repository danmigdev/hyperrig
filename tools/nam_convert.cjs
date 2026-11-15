// Use the recovered original converter locally, retaining its own license.
// Output is UltraRig A2L1, not a stock Tank Mini AM3/AM4 image.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = path.join(root, 'recovered/ultrarig-original/web/nam2chip.js');
if (!fs.existsSync(source)) {
  console.error('Run python -m hyperrig analyze first.');
  process.exit(1);
}
const input = process.argv[2], output = process.argv[3];
if (!input || !output || input === output) {
  console.error('Usage: node tools/nam_convert.cjs input.nam new-output.a2l');
  process.exit(1);
}
try {
  const converter = require(source);
  const result = converter.convert(fs.readFileSync(input, 'utf8'), {name: path.basename(input, '.nam')});
  fs.writeFileSync(output, result.blob, {flag: 'wx'});
  console.log(JSON.stringify(result.stats, null, 2));
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
