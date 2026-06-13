#!/bin/bash
# Setup de desarrollo de cambrian-plugin. Ejecutar una vez tras clonar: bash bin/dev/setup.sh
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"

install_hook() {
    local name="$1"
    local src="$REPO_ROOT/bin/dev/git-hooks/$name"
    local dst="$REPO_ROOT/.git/hooks/$name"
    chmod +x "$src"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        echo "  $name ya instalado"
    else
        ln -sf "$src" "$dst"
        echo "  $name instalado -> .git/hooks/$name"
    fi
}

echo "cambrian-plugin — setup de desarrollo"
install_hook "pre-commit"
install_hook "post-commit"
echo "Listo. pre-commit corre tests; post-commit auto-bumpea version."
