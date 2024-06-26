from mal_types import true, false, Array, Symbol, atom, Function 
from printer import pr_str
import reader
from time import time

import copy

def _prn(*args):
    print(' '.join([pr_str(x) for x in args]))
    return None

def _println(*args):
    print(' '.join([pr_str(x, print_readably=False) for x in args]))
    return None

def _reset_atom(a, val):
    a.reference = val
    return a.reference

def _swap_atom(a, f, *args):
       
    if callable(f):
        a.reference = f(a.reference, *args)
    else:
        a.reference = f.fn(a.reference, *args)
    return a.reference

def _qq_expand(x):
    res = Array([],"(")
    for elt in reversed(x):
        if isinstance(elt, Array) and len(elt) > 0 and isinstance(elt[0], Symbol) and elt[0].name == "splice-unquote":
            res = Array([Symbol("concat"), elt[1], res],"(")
        else:
            res= Array([Symbol("cons"), quasiquote(elt), res], "(")
    return Array(res, "(")
    
def quasiquote(x):
    if isinstance(x, Array) and x.type == "vector":
        return Array([Symbol("vec"), _qq_expand(Array(x,"("))],"(")
    elif isinstance(x, Array) and len(x) > 0 and isinstance(x[0], Symbol) and x[0].name == "unquote":
        return x[1]
    elif isinstance(x, Array) and x.type == "list":
        return _qq_expand(x)
    elif isinstance(x, Array) and x.type == "hash-map" or isinstance(x, Symbol):
        return Array([Symbol("quote"), x], "(")
    else:
        return x
    
def is_macro_call(x, env):
    
    if not isinstance(x, Array):
        call = False
    elif x.type != "list" or len(x) < 1:
        call = False
    elif not isinstance(x[0], Symbol):
        call = False
    elif env.find(x[0].name) is None:
        call = False
    elif not isinstance(env.get(x[0].name), Function):
        call = False
    elif not env.get(x[0].name).is_macro:
        call = False
    else:
        call = True
    
    return call

def macroexpand(x, env):
    
    while is_macro_call(x, env):
        macro = env.get(x[0].name)
        x = macro.fn(*x[1:])
        
    return x

def _rest(l):
    if l == [] or (l is None):
        return Array([], "(")
    else:
        return Array(l[1:], "[" if l.type == "vector" else "(")
    
def _raise_exception(a):
    raise Exception(a)
    
def _apply(f, *args):
    
    arg_list = []
    for arg in args:
        if isinstance(arg, list):
            for ar in arg:
                arg_list.append(ar)
        else:
            arg_list.append(arg)
            
    if callable(f):
        return f(*arg_list)
    else:
        return f.fn(*arg_list)

def _map(*args):
    
    f = args[0]
    arg_vals = args[1]
    
    if callable(f):
        res = [f(arg) for arg in arg_vals]
    else:
        res = [f.fn(arg) for arg in arg_vals]
    
    return Array(res, "(")

def _assoc(hash, *args):
    
    new_hash = []
    for i in range(len(hash)):
        new_hash.append(hash[i])
        
    for j in range(0,len(args),2):
        if args[j] in new_hash:
            new_hash[new_hash.index(args[j])+1] = args[j+1]
        else:
            new_hash.append(args[j])
            new_hash.append(args[j+1])
    return Array(new_hash,"{")

def _dissoc(hash, *keys):
    
    res = []
    for i in range(0,len(hash),2):
        if hash[i] not in keys:
            res.append(hash[i])
            res.append(hash[i+1])
        else:
            continue
    return Array(res, "{")
    
def _readline(s):
    try:
        return input(s)
    except EOFError:
        return None
    
def _clone(a):
    if isinstance(a, Function):
        c = Function(
            copy.deepcopy(a.x), 
            copy.deepcopy(a.params), 
            copy.deepcopy(a.env), 
            copy.deepcopy(a.fn), 
            copy.deepcopy(a.is_macro)
        )
    elif callable(a):
        c = lambda: a
    else:
        c = copy.deepcopy(a)
    
    return c
    
def _with_meta(a, b):
    c = _clone(a)
    c.metadata = b
    return c

def _seq(a):
    
    if (isinstance(a, Array) and a.type != "hash-map" and len(a) == 0) or a == "" or a is None:
        return None
    elif isinstance(a, Array) and a.type == "list":
        return a
    elif isinstance(a, Array) and a.type == "vector":
        return Array(a, "(")
    elif isinstance(a, str):
        return Array([x for x in a], "(")
    else:
        raise Exception("Not implemented")
    
def _conj(a, *args):
    
    if isinstance(a, Array) and a.type == "list":
        return Array([b for b in reversed(args)] + a,"(")
    elif isinstance(a, Array) and a.type == "vector":
        
        if not isinstance(args, Array):
            args = Array(args, "[")
        
        return Array(a + args, "[")
    else:
        raise Exception("Not implemented")
        
ns = {
    '+': lambda a,b: a+b,
    '-': lambda a,b: a-b,
    '*': lambda a,b: a*b,
    '/': lambda a,b: int(a/b),
    
    '=': lambda a,b: true() if a==b else false(),
    '<': lambda a,b: true() if a<b else false(),
    '<=': lambda a,b: true() if a<=b else false(),
    '>': lambda a,b: true() if a>b else false(),
    '>=': lambda a,b: true() if a>=b else false(),
    
    'list': lambda *args: Array(args, "("),
    'list?': lambda *args:true() if isinstance(args[0], list) else false(),
    'empty?': lambda *args: true() if len(Array(args[0],"(")) == 0 else false(),
    'count': lambda *args: len(args[0]),
       
    'prn': _prn,
    'pr-str': lambda *args: ' '.join([pr_str(x, print_readably=True) for x in args]),
    'str': lambda *args: ''.join([pr_str(x, print_readably=False) for x in args]),
    'println': lambda *args: _println(*args),
    
    'read-string': reader.read_str,
    'slurp': lambda a: open(a, "r").read(),
    
    'atom': lambda val: atom(val),
    'atom?': lambda a: true() if isinstance(a, atom) else false(),
    'deref': lambda a: a.reference,
    'reset!': _reset_atom,
    'swap!': _swap_atom,
    
    'cons': lambda a,b: Array([a]+b,"("),
    'concat': lambda *args: Array([x for y in args for x in y], "("),
    
    'vec': lambda a: Array(a, "["),
    
    'nth': lambda l, i: l[i],
    'first': lambda l: l[0] if len(l) > 0 else None,
    'rest' : _rest,
    
    'throw': _raise_exception,
    'apply': _apply,
    'map': _map,
    
    'nil?': lambda a: true() if a == None else false(),
    'true?': lambda a: true() if isinstance(a, true) else false(),
    'false?': lambda a: true() if isinstance(a, false) else false(),
    'symbol?': lambda a: true() if isinstance(a, Symbol) else false(),
        
    'symbol': lambda a: Symbol(a),
    'keyword': lambda a: u"0x29E" + a if a[0] != u"0x29E" else a,
    'keyword?': lambda a: true() if isinstance(a, str) and a.startswith(u"0x29E") else false(),
    'vector': lambda *args: Array(args, "["),
    'vector?': lambda a: true() if isinstance(a, Array) and a.type == "vector" else false(),
    'sequential?': lambda a: true() if isinstance(a, Array) and a.type in ["vector","list"] else false(),
    'hash-map': lambda *args: Array(args, "{"),
    'map?': lambda a: true() if isinstance(a, Array) and a.type == "hash-map" else false(),
    'assoc': _assoc,
    'dissoc': _dissoc,
    'get': lambda hash, key: hash[hash.index(key)+1] if isinstance(hash, Array) and key in hash else None,
    'contains?': lambda hash, key: true() if key in hash else false(),
    'keys': lambda hash: Array(hash[::2],"("),
    'vals': lambda hash: Array(hash[1::2],"("),
    
    'readline': _readline,
    'time-ms': lambda: round(time() * 1000),
    'meta': lambda a: a.metadata if hasattr(a, "metadata") else None,
    'with-meta': _with_meta,
    'fn?': lambda a: true() if (isinstance(a, Function) and not a.is_macro) or callable(a) else false(),
    'macro?': lambda a: true() if isinstance(a, Function) and a.is_macro else false(),
    'string?': lambda a: true() if isinstance(a, str) and not a.startswith(u"0x29E") else false(),
    'number?': lambda a: true() if isinstance(a, (int, float, complex)) else false(),
    'seq': _seq,
    'conj': _conj,
    
}



