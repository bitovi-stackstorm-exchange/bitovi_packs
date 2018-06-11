
from st2common.runners.base_action import Action


class FooAction(Action):
    '''
    output bar
    '''
    def run(self):
        return (True, "bar")