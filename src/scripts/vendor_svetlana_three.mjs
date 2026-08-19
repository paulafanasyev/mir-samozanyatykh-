import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const frontend = path.join(root, 'frontend');
const targets = [
  path.join(frontend, 'public', 'svetlana', 'vendor', 'three', '0.179.1'),
  path.join(root, 'mobile', 'assets', 'svetlana', 'vendor', 'three', '0.179.1'),
];

const required = [
  'build/three.module.js',
  'build/three.core.js',
  path.join('examples', 'jsm', 'loaders', 'GLTFLoader.js'),
  path.join('examples', 'jsm', 'utils', 'BufferGeometryUtils.js'),
];
const packageRoot = path.join(frontend, 'node_modules', 'three');

async function exists(p) { try { await fs.access(p); return true; } catch { return false; } }

if (!(await exists(packageRoot))) {
  console.error('Three.js 0.179.1 is not installed locally. Run `npm ci` first in src/frontend.');
  console.error('This script intentionally does not download from the network or substitute another version.');
  process.exit(2);
}

const pkg = JSON.parse(await fs.readFile(path.join(packageRoot, 'package.json'), 'utf8'));
if (pkg.version !== '0.179.1') {
  console.error(`Refusing to vendor Three.js ${pkg.version}; expected exactly 0.179.1.`);
  process.exit(3);
}

for (const rel of required) {
  const src = path.join(packageRoot, rel);
  if (!(await exists(src))) {
    console.error(`Missing required upstream file: ${src}`);
    process.exit(4);
  }
}

const copies = [
  ['build/three.module.js', 'three.module.js'],
  ['build/three.core.js', 'three.core.js'],
  [path.join('examples', 'jsm', 'loaders', 'GLTFLoader.js'), path.join('examples', 'jsm', 'loaders', 'GLTFLoader.js')],
  [path.join('examples', 'jsm', 'utils', 'BufferGeometryUtils.js'), path.join('examples', 'jsm', 'utils', 'BufferGeometryUtils.js')],
];

for (const target of targets) {
  await fs.rm(target, { recursive: true, force: true });
  await fs.mkdir(target, { recursive: true });
  for (const [from, to] of copies) {
    const dest = path.join(target, to);
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.copyFile(path.join(packageRoot, from), dest);
  }
  console.log(`Vendored minimal Three.js ${pkg.version} runtime -> ${target}`);
}

