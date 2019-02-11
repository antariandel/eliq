# Source: https://stackoverflow.com/questions/3711657/can-i-prevent-modifying-an-object-in-python

# Put in const.py...
# from http://code.activestate.com/recipes/65207-constants-in-python

import sys


class _const:
    class ConstError(TypeError):
        pass  # base exception class

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError('Can\'t change const.%s!' % name)
        if not name.isupper():
            raise self.ConstCaseError('Const name %r is not all uppercase!' % name)
        self.__dict__[name] = value
    
    # I added __delattr___
    def __delattr__(self, name):
        if name in self.__dict__:
            raise self.ConstError('Can\'t delete const.%s!' % name)


# replace module entry in sys.modules[__name__] with instance of _const
# (and create additional reference to module so it's not deleted --
# see Stack Overflow question: http://bit.ly/ff94g6)

_ref, sys.modules[__name__] = sys.modules[__name__], _const()

if __name__ == '__main__':
    import const  # test this module...

    try:
        const.Answer = 42  # not OK, mixed-case attribute name
    except const.ConstCaseError as exc:  # pylint: disable=no-member
        print(exc)
    else:  # test failed - no ConstCaseError exception generated
        raise RuntimeError("Mixed-case const names should't have been allowed!")

    const.ANSWER = 42  # should be OK, all uppercase

    try:
        const.ANSWER = 17  # not OK, attempts to change defined constant
    except const.ConstError as exc:  # pylint: disable=no-member
        print(exc)
    else:  # test failed - no ConstError exception generated
        raise RuntimeError("Shouldn't have been able to change const attribute!")
