"""A simple sequential state machine was used for the experiment with synthetically 
generated packets for the flows. The state machine used was the simplest possible:
1 → 2 → 3 → 4.... → 10."""
class StateMachine:
    def __init__(self):
        self.current_state = 1  

    def transition_state(self):
        if self.current_state < 10:
            self.current_state += 1
        else:
            self.reset()

    def reset(self):
        self.current_state = 1

    def get_state(self):
        return self.current_state