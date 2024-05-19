import itertools
import json
import random
import re
import sys

# TODO: Add Exception

PRINT_OUTPUT = False


def dieroller(args):
    random.seed()
    try:
        actions = parse_args(args[0].split(" "))
    except ValueError:
        sys.stdout.write(json.dumps({"items": [error_to_alfred("Unable to parse arguments.")]}))
    result = []
    for action in actions:
        try:
            result.append(do_action(action, result))
        except ValueError:
            sys.stdout.write(json.dumps({"items": [error_to_alfred("Action %s must have die rolls before it." % action['action'])]}))
            raise
    sys.stdout.write(json.dumps({"items": list(map(lambda a: a['alfred'], result[::-1]))}))


def error_to_alfred(error_string):
    alfred = {
        "title": "error",
        "subtitle": error_string,
        "arg": error_string,
        "icon": {"path": "./icon.png"}
    }
    return alfred


def to_alfred(title, subtitle, arg):
    alfred = {
        "title": title,
        "subtitle": subtitle,
        "arg": arg,
        "icon": {"path": "./icon.png"}
    }
    return alfred


def parse_args(args):
    idx = 0
    actions = []
    while idx < len(args):
        if re.match(r'\d+$', args[idx]):
            actions.append({'action': 'roll', 'args': {'sides': int(args[idx]), 'amount': 1}})
        elif re.match(r'\d+d\d+$', args[idx]):
            expr = re.match(r'(\d+)d(\d+)', args[idx])
            actions.append({'action': 'roll', 'args': {'sides': int(expr.group(2)), 'amount': int(expr.group(1))}})
        elif re.match(r'sum', args[idx]):
            actions.append({'action': 'sum'})
        elif re.match(r'(bottom|bot)\d+', args[idx]):
            expr = re.match(r'(bottom|bot)(\d+)', args[idx])
            actions.append({'action': 'bottom', 'args': {'num': int(expr.group(2))}})
        elif re.match(r'(top)\d+', args[idx]):
            expr = re.match(r'(top)(\d+)', args[idx])
            actions.append({'action': 'top', 'args': {'num': int(expr.group(2))}})
        elif re.match(r'(<|>|>=|<=)\d+', args[idx]):
            expr = re.match(r'(<|>|>=|<=)(\d+)', args[idx])
            actions.append({'action': 'hits', 'args': {'operator': expr.group(1), 'num': int(expr.group(2))}})
        elif re.match(r'(/?[\+\-\*/]\d+)', args[idx]):
            actions.append({'action': 'math', 'args': {'expr': args[idx]}})
        elif args[idx].strip() == "":
            pass
        else:
            raise ValueError
        idx += 1
    return actions


def do_action(action, result):
    if action['action'] == 'roll':
        return roll_die(action['args'])
    elif action['action'] == 'top':
        return bottom(action['args'], result[-1], reverse=True)
    elif action['action'] == 'bottom':
        return bottom(action['args'], result[-1])
    elif action['action'] == 'hits':
        return hits(action['args'], result[-1])
    elif action['action'] == 'sum':
        return sum_dice(result[-1])
    elif action['action'] == 'math':
        return math(action['args'], result[-1])
    else:
        return result


def roll_die(args):
    result = []
    for i in range(args['amount']):
        result.append(random.randrange(1, args['sides'] + 1))
    str_result = ", ".join(map(str, result))
    if PRINT_OUTPUT is True:
        print("Roll %dd%d: " % (args['amount'], args['sides']) + str_result)
    alfred = to_alfred(str_result,
                       "Roll %dd%d: " % (args['amount'], args['sides']),
                       str_result)
    return {'result': result, 'prev': None, 'alfred': alfred}


def sum_dice(result):
    if type(result['result']) is not list:
        raise ValueError
    total = sum(result['result'])
    if PRINT_OUTPUT is True:
        print("Sum: %d" % total)
    alfred = to_alfred("%d" % total, ", ".join(map(str, result['result'])), "%d" % total)
    return {'result': total, 'prev': result, 'alfred': alfred}


def hits(args, result):
    expr = "list(filter(lambda d: d %s %d, result['result']))" % (args['operator'], args['num'])
    if type(result['result']) is not list:
        raise ValueError
    hits = len(eval(expr))
    subtitle = "Total %s %d : %d" % (args['operator'], args['num'], hits)
    if PRINT_OUTPUT is True:
        print(subtitle)
    alfred = to_alfred("%d" % hits, subtitle, "%d" % hits)
    return {'result': hits, 'prev': result, 'alfred': alfred}


def bottom(args, result, reverse=False):
    if type(result['result']) is not list:
        raise ValueError
    li = list(sorted(result['result'], reverse=reverse))[:args['num']]
    str_result = ", ".join(map(str, li))
    if reverse is True:
        subtitle = "Top %d : %s" % (args['num'], str_result)
    else:
        subtitle = "Bottom %d : %s" % (args['num'], str_result)
    if PRINT_OUTPUT is True:
        print(subtitle)
    alfred = to_alfred(str_result, subtitle, str_result)
    return {'result': li, 'prev': result, 'alfred': alfred}


def math(args, result):
    if type(result['result']) is not list:
        raise ValueError
    exprs = re.findall(r'/?[\+\-\*/]\d+', args['expr'])
    operations = []
    first = False
    for item in exprs:
        if first is True:
            operations.append(item[1:])
        else:
            operations.append(item)
        first = True
    if len(operations) == 1:
        operations = operations * len(result['result'])
    ops = itertools.zip_longest(result['result'], operations, fillvalue="+0")
    result_list = []
    for op in ops:
        evalstr = "%d %s %d" % (op[0], op[1][0], int(op[1][1:]))
        result_list.append(eval(evalstr))
    str_result = ", ".join(map(str, result_list))
    subtitle = "%s: %s" % ("".join(exprs), str_result)
    if PRINT_OUTPUT is True:
        print(subtitle)
    alfred = to_alfred(str_result, subtitle, str_result)
    return {'result': result_list, 'prev': result, 'alfred': alfred}

# if __name__ == "__main__":
#     PRINT_OUTPUT = True
#     dieroller(sys.argv[1:])


dieroller(sys.argv[1:])
