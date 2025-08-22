from object_definitions import Train, Section



def step_setup():

    step_dict = {}
    # form {"A1" : {"upcount" : {"old_berth_sections": [section, section], "new_beth_section: section}},
    # "Pad1": {instantaneous : {"old_berth_sections": [section, section] "new_beth_section: section}}}
    feeder_dict = {}
    # in form {new_section : [old_section, old_section]}

    # create a lookup table of sections by decrementing axlecounter :
    dec_trig_lookup = {} # form {"A1" : {"upcount" : [Section, Section]}}
    for section in Section.instances.values():
        for dectrig, direction in section.dectrig.items():
            if dectrig in dec_trig_lookup:
                if direction in dec_trig_lookup[dectrig]:
                    dec_trig_lookup[dectrig][direction].append(section)
                else:
                    dec_trig_lookup[dectrig][direction] = [section]
            else:
                dec_trig_lookup[dectrig] = {direction: [section]}

    for section in Section.instances.values():
        feeder_sections = []
        for inctrig, direction in section.inctrig.items():
            # find corresponding dectrig section
            if inctrig in dec_trig_lookup:
                if direction in dec_trig_lookup[inctrig]:
                    feeder_sections.append(dec_trig_lookup[inctrig][direction])  # list of feeder sections for that AC
                    #put it all into the step_dict
                    step_dict[inctrig]= {direction : {"old_berth_sections": feeder_sections, "new_berth_section": section}}
                    if section in feeder_dict.keys():
                       feeder_dict[section].extend(feeder_sections)
                    else:
                        feeder_dict[section] = feeder_sections

    return step_dict, feeder_dict

def new_unknown_train(berth_section: Section):
    """used when a new train appears on the network"""
    trainID = Train.next_ID_counter
    Train.instances[trainID] = Train()
    train = Train.instances[trainID]
    train.berth_section = berth_section
    berth_section.trains.append(train)
    train.journey_log.append(berth_section.ref)
    #Add in a default headcode allocation, based on sequential from 1C00

def berth_set(berth_section: Section):
    """Used for initially setting a headcode & ID, before any train is in the berth"""
    # on mqtt berth set message
    trainID = Train.next_ID_counter
    Train.instances[trainID] = Train()
    train = Train.instances[trainID]
    train.berth_section = berth_section
    berth_section.trains.append(train)
    return


def headcode_update(trains:dict, old_headcode: str, new_headcode: str):
    """Used for updating headcode from MQTT interface"""
    train = Train.headcode_lookup[old_headcode]
    train.headcode = new_headcode
    Train.headcode_lookup.pop(old_headcode)
    Train.headcode_lookup[new_headcode] = train
    return


def berth_RFID_set(trains:dict, RFID, berth_section: Section):
    """Used to update berth based on RFID read"""
    # find the right train from the berth
    # lookup if the RFID is already associated with a headcode; if it is, update the headcode in the berth
    # If not, update the locos, carriages, driver, guard & routes from previous allocation
    pass


def berth_step(old_berth_section: Section, new_berth_section: Section):
    """Takes berth-step info and updates all relevant references"""
    train = Train.find_by_berth(old_berth_section)
    train.berth_section = new_berth_section
    old_berth_section.trains.remove(train)
    new_berth_section.trains.append(train)
    train.journey_log.append(new_berth_section.ref)
    if len(new_berth_section.trains)>1:
        #setup SPAD alert here - wont work as new berth occupancy not detected. Need to look for loss of berth occ.
        pass
    return


def train_clear(berth_section: Section = None, train: Train = None):
    """Used when to clear links between headcode and track circuits"""
    if berth_section:
        train = Train.find_by_berth(berth_section)
    #remove train from section and from dictionary
    train.berth_section.trains.remove(train)
    # TODO - copy journey to log
    Train.instances.pop(train.ID)

    return


def berth_calculate(feeder_dict, logger, mqtt_client):
    """Determines what stepping is required when not implicit from axlecounter etc"""
    for section in Section.instances.values():
        #logic for treadle / reed operated train detection
        if section.mode: # == "trackcircuit": test using this for backup for everything
            if section.occstatus and not section.trains:
                if section in feeder_dict:
                    for feeder_list in feeder_dict[section]:
                        for feeder in feeder_list:
                            if feeder.trains and not feeder.occstatus:
                                berth_step(old_berth_section=feeder, new_berth_section=section)
        # TODO add in signal and point logic. Could use routes?

        #logic for axlecounters
        if section.mode == "axlecounter":
            pass # managed by section update checking routine.

        # logic for treadlepads
        if section.mode == "treadlepad":
            pass  # managed by section uodate checking routine.

        #if section.occstatus and not section.trains:
        #    new_unknown_train(section)

    return


def journey_logging():
    """record all the journeys for logging and stats purposes"""
    pass
