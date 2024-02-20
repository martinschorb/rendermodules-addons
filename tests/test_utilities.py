#!/usr/bin/env python
'''
'''
import pytest
import string
import random

from rmaddons.utilities import arg2params

def test_arg2params():
    args={"a1":"v1", "a2":2}

    for key in args.keys():
        out1 = arg2params(args, key)
        assert out1 == ["--" + key, args[key]]

        letters = string.ascii_lowercase
        flag = ''.join(random.choice(letters) for i in range(4))

        out2 = arg2params(args, key, flag=flag)
        assert out2 == [flag, args[key]]

    assert arg2params(args, 'thiskeydoesnotexist') == []
