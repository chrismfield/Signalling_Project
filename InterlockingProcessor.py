# Core processing of inputs for signal interlocking.
from Common_Signalling_Defs import axlecounter, signal, section, route, point, plunger
print(section.sectiondict)
# load configuration (e.g. com ports)


#Call another function to aquire all inputs and updates, including axle counters, track circuits and points.

# train protection:

# Update section occupation.

# Set all protecting signals to danger.

# route setting:

# Clear used route segments
# Check route triggers
# check conflicting sections
# apply interlocking doublecheck
# Set routes (will need to iterate this to wait for point detection)

#
# Send outputs to relevant points and all signals