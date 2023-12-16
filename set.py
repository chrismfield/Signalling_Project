
def set_point(point, direction):
    if direction == "normal":
        try:
            point.slave.write_bit(self.reverse_coil, 0)
            point.slave.write_bit(self.normal_coil, 1)
            return True
        except ValueError:
            status = "Comms failure" # add details and logging
            return False
    if direction == "reverse":
        try:
            point.slave.write_bit(self.normal_coil, 0)
            point.slave.write_bit(self.reverse_coil, 1)
            return True
        except ValueError:
            status = "Comms failure" # add details and logging
            return False

def  set_route(route):
    # check route is clear to set
    # return "not_available" if not available
    # set points
    # return "setting" while points are setting
    # set signals
    # return "set" once points and signals set
    pass