"""Offline AST inventory of collector, validators and their fatal dependencies."""
import ast
from pathlib import Path
from od_core import ROOT

MODULES=('od_collect.py','od_validation.py','od_core.py','od_io.py','od_identity.py','od_transport.py',
         'od_freeze.py','od_provenance.py','od_recovery.py','od_analysis.py','od_archive.py')


def audit_sites(root=ROOT):
    rows=[]
    for name in MODULES:
        tree=ast.parse((Path(root)/name).read_text())
        def walk(node,scope='module'):
            if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                scope=(scope+'.' if scope!='module' else '')+node.name
            kind=None
            if isinstance(node,ast.Raise): kind='raise'
            elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fatal' for t in node.targets) and not (isinstance(node.value,ast.Constant) and node.value.value is None): kind='fatal assignment'
            elif isinstance(node,ast.ExceptHandler) and name in ('od_collect.py','od_transport.py'): kind='exception route'
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='durable_stop':kind='durable stop'
            if kind:
                expression=ast.unparse(node.exc) if kind=='raise' and node.exc else ('re-raise' if kind=='raise' else ast.unparse(node.type) if kind=='exception route' else ast.unparse(node))
                rows.append({'site':f'{name}:{node.lineno}:{kind}','scope':scope,'kind':kind,'expression':expression})
            for child in ast.iter_child_nodes(node): walk(child,scope)
        walk(tree)
    return rows

if __name__=='__main__':
    from od_core import canonical
    print(canonical(audit_sites()))
