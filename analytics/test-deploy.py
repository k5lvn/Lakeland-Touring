import ast,re
from pathlib import Path
tree=ast.parse(Path('analytics/deploy.py').read_text());ns={'re':re}
for n in ast.walk(tree):
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TAG' for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name in ('patch_html','is_public','has_head'):
        exec(compile(ast.Module(body=[n],type_ignores=[]),'deploy.py','exec'),ns)
html=b'<html><head><title>Public page</title></head><body>Existing content</body></html>'
patched=ns['patch_html'](html)
assert patched.replace(ns['TAG'],b'')==html
assert ns['patch_html'](patched)==patched
try:ns['patch_html'](html.replace(b'</head>',b'<script src="https://www.googletagmanager.com/gtag/js"></script></head>'))
except ValueError:pass
else:raise AssertionError('Existing tracking must block installation')
for path in ('admin.html','login.html','account/settings.html','rider-hub.html','owner-garage.html','passport.html','verify.html','performance365/index.html'):
    assert not ns['is_public'](path),path
for path in ('index.html','contact.html','about.html','locations/carlisle.html'):
    assert ns['is_public'](path),path
print('HTML preservation, idempotence, duplicate-tag protection and private-page exclusions passed.')

assert not ns['has_head'](b'<header>Menu</header><main>Fragment</main>')
assert ns['has_head'](html)
print('Header-only fragments excluded; full pages recognised.')
