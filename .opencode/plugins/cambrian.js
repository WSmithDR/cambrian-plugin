// .opencode/plugins/cambrian.js
// Inyecta el bootstrap de AGENTS.md en la primera sesión de OpenCode, solo dentro de este repo.
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(__dirname, '../..'); // .opencode/plugins -> repo root
const AGENTS_MD = path.join(PLUGIN_ROOT, 'AGENTS.md');

function isInOwnRepo() {
  try {
    const sentinel = path.join(PLUGIN_ROOT, '.claude-plugin', 'plugin.json');
    const cwd = process.cwd();
    const inRepo = cwd === PLUGIN_ROOT || cwd.startsWith(PLUGIN_ROOT + path.sep);
    return fs.existsSync(sentinel) && inRepo;
  } catch {
    return false;
  }
}

let _cache;
function getBootstrap() {
  if (_cache !== undefined) return _cache;
  try {
    _cache = fs.existsSync(AGENTS_MD) ? fs.readFileSync(AGENTS_MD, 'utf8').trim() : null;
  } catch {
    _cache = null;
  }
  return _cache;
}

const CambrianPlugin = () => {
  if (!isInOwnRepo()) return {};
  return {
    'experimental.chat.messages.transform': async (_input, output) => {
      if (!output.messages?.length) return;
      const firstUser = output.messages.find((m) => m.info?.role === 'user');
      if (!firstUser?.parts?.length) return;
      const already = firstUser.parts.some(
        (p) => p.type === 'text' && p.text?.includes('cambrian-plugin')
      );
      if (!already) {
        const bootstrap = getBootstrap();
        if (bootstrap) {
          firstUser.parts.unshift({ type: 'text', text: `<MANDATORY>\n${bootstrap}\n</MANDATORY>` });
        }
      }
    },
  };
};

export default CambrianPlugin;
