from renderapi.client import client_calls

def arg2params(args, key, flag=None):

    if flag is None:
        flag = "--" + key

    if key in args.keys():
        return client_calls.get_param(args[key], flag)

    else:
        return []


