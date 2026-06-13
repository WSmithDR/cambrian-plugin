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
    return fs.existsSync(sentinel) && process.cwd().startsWith(PLUGIN_ROOT);
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
  let injected = false;
  return {
    name: 'cambrian',
    transformMessages({ messages }) {
      if (injected) return messages;
      const firstUser = messages.find(m => m.role === 'user');
      if (!firstUser) return messages;
      const already = firstUser.parts?.some(
        p => p.type === 'text' && p.text?.includes('cambrian-plugin')
      );
      if (!already) {
        const bootstrap = getBootstrap();
        if (bootstrap) {
          firstUser.parts.unshift({ type: 'text', text: `<MANDATORY>\n${bootstrap}\n</MANDATORY>` });
        }
      }
      injected = true;
      return messages;
    },
  };
};

export default CambrianPlugin;
