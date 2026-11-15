// Compare against the original converter recovered from the release archive.
// Input/output are JSON over stdin/stdout; this helper never contacts a pedal.
const fs = require('node:fs');
const path = require('node:path');
const original = require(path.join(__dirname, '../recovered/ultrarig-original/web/nam2chip.js'));
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
original.validateBlob(Buffer.from(request.capture, 'base64'));
const ranges = request.signals.map(samples => original.measure(request.engine, Float64Array.from(samples)));
process.stdout.write(JSON.stringify(ranges));
