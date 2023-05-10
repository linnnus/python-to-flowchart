import ast
import sys
import graphviz
import inspect

# https://www.lucidchart.com/pages/flowchart-symbols-meaning-explained

# TODO: handle print calls -> Output nodes

def create_getid():
    i = 0

    def getid(prefix: str):
        nonlocal i
        i += 1
        return f"{prefix}-{i}"

    return getid

def visualize(source) -> graphviz.Graph:
    def visit_node(ast_node: ast.AST | list[ast.stmt]) -> str:
        """Adds figures for `node` to `graph`, returning label id."""

        print(f"visiting: {ast_node}")

        match ast_node:
            case ast.Module(body):
                for child in body:
                    visit_node(child)
                return "" # Should be top-level so this doesn't matter
            case ast.FunctionDef(name, args, body):
                decl_id = getid("decl")
                label = name # TODO: include  args?
                graph.node(decl_id, label)
                tail_id = decl_id # use this to connect everything

                # Generate a /take x/ node for each argument
                # TODO: andle *arg and **kwarg
                # TODO: print default values
                for arg in args.args + args.posonlyargs + args.kwonlyargs:
                    arg_id = getid("arg")
                    label = f"Input {arg.arg}"
                    graph.node(arg_id, label, shape="parallelogram")
                    graph.edge(tail_id, arg_id, dir="forward")
                    tail_id = arg_id

                body_id = visit_node(body)
                graph.edge(tail_id, body_id, dir="forward")

                return decl_id
            case ast.If(test, body, orelse):
                test_id = getid("cond")
                code = ast.unparse(test)
                graph.node(test_id, code, shape="diamond")

                body_id = visit_node(body)
                else_id = visit_node(orelse)

                graph.edge(test_id, body_id, label="yes", dir="forward")
                graph.edge(test_id, else_id, label="no", dir="forward")
                return test_id
            # string together label(stmt) and visit_node() such that they are connected in sequence
            case ast.Assign(targets, value):
                assert len(targets) == 1
                assign_id = getid("assignment")
                label = f"set {ast.unparse(targets[0])} to {ast.unparse(value)}"
                graph.node(assign_id, label)
                return assign_id
            case ast.Return(value):
                return_id = getid("return")
                if value:
                    label = f"result is {ast.unparse(value)}"
                else:
                    label = "end of procedure"
                graph.node(return_id, label, shape="rectangle")
                return return_id
            case [head, *tail]:
                if len(tail) > 0:
                    head_id = visit_node(head)
                    tail_id = visit_node(tail)
                    graph.edge(head_id, tail_id, dir="forward")
                    return head_id
                else:
                    return visit_node(head)
            # Some basic nodes are just converted to text
            case ast.Expr() | ast.Name() | ast.Ellipsis():
                decl_id = getid("expr")
                code = ast.unparse(ast_node)
                graph.node(decl_id, code)
                return decl_id
            case _:
                raise NotImplementedError(f"Unhandled node type: {ast_node.__class__.__name__}: {ast_node}")

    getid = create_getid()

    graph = graphviz.Graph()

    source_s = source if isinstance(source, str) else inspect.getsource(source)
    root_ast_node = ast.parse(source_s)

    visit_node(root_ast_node)

    return graph

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        source = f.read()
    graph = visualize(source)
    graph.view()
