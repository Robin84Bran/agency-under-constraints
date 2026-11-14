"""Enumerate explicit termination, classification and exception-routing sites."""
import ast
from pathlib import Path

MODULES=('uc_core.py','uc_store.py','uc_transport.py','uc_collect.py','uc_freeze.py','uc_analysis.py','uc_manifest.py')


def scan(root,original=False):
    root=Path(root);rows=[]
    for name in MODULES:
        path=root/('deviations/a1/original/'+name if original else name)
        if not path.exists():continue
        class Visitor(ast.NodeVisitor):
            def __init__(self):self.scope=[];self.guards=[]
            def visit_FunctionDef(self,node):
                self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
            visit_AsyncFunctionDef=visit_FunctionDef
            def visit_ClassDef(self,node):
                self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
            def visit_If(self,node):
                self.guards.append(ast.unparse(node.test))
                for child in node.body:self.visit(child)
                self.guards.pop()
                for child in node.orelse:self.visit(child)
            def add(self,node,kind,expression=None):
                rows.append(dict(site=f'{name}:{node.lineno}:{kind}',file=name,line=node.lineno,kind=kind,
                    function='.'.join(self.scope),expression=expression or ast.unparse(node).replace('\n',' '),
                    guard=self.guards[-1] if self.guards else None))
            def visit_Raise(self,node):self.add(node,'raise')
            def visit_ExceptHandler(self,node):
                self.add(node,'handler','except '+(ast.unparse(node.type) if node.type else 'BaseException'))
                self.generic_visit(node)
            def visit_Return(self,node):
                if any(isinstance(n,ast.Constant) and n.value in ('fatal','episode','content','transport') for n in ast.walk(node)):
                    self.add(node,'classification')
                self.generic_visit(node)
            def visit_Assign(self,node):
                targets=[ast.unparse(t) for t in node.targets]
                if node.value==None:return
                if isinstance(node.value,ast.Constant) and node.value.value is True and any(t in ('fatal','self.blocked') for t in targets):
                    self.add(node,'fatal-flag')
                if 'consecutive' in targets and 'terminal' in ast.unparse(node.value):self.add(node,'streak')
                self.generic_visit(node)
            def visit_Call(self,node):
                if isinstance(node.func,ast.Name) and node.func.id=='durable_stop':self.add(node,'durable-stop')
                self.generic_visit(node)
        Visitor().visit(ast.parse(path.read_text()))
    return sorted(rows,key=lambda r:(r['file'],r['line'],r['kind']))
