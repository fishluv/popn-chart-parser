from collections import defaultdict

def get_events(bin_filename, new_format, debug=False):
  if not bin_filename.endswith(".bin"):
    raise RuntimeError("only bin files are supported")

  event_id_to_name = {
    0x0145: "key",
    0x0245: "sample",
    0x0345: "unk0345",
    0x0445: "bpm",
    0x0545: "timesig",
    0x0645: "end",
    0x0745: "sample2",
    0x0845: "timing",
    0x0945: "unk0945",
    0x0d45: "unk0d45",
    0x0a00: "measure",
    0x0b00: "beat",
    0x000f: "unk000f",
  }

  events = []
  event_size = 12 if new_format else 8
  unknown_events = 0

  with open(bin_filename, "rb") as file:
    while event_bytes := file.read(event_size):
      if len(event_bytes) < event_size:
        if debug:
          print("[warn] %s: last event is incomplete. expected %s bytes and got %s." % (hex(file.tell()-event_size), event_size, len(event_bytes)))
        break

      timestamp = int.from_bytes(event_bytes[0:4], "little")
      event_id = int.from_bytes(event_bytes[4:6], "little")
      event_name = event_id_to_name.get(event_id)

      if not event_name:
        unknown_events += 1
        if debug:
          print("[warn] %s: unknown event_id 0x%s with timestamp 0x%s" % (hex(file.tell()-event_size), hex(event_id).lstrip("0x").rjust(4, "0"), hex(timestamp).lstrip("0x").rjust(8, "0")))
          if file.tell() - event_size == 0 and event_id == 0:
            print("[warn] are you sure the format is correct?")
        if unknown_events > 30:
          raise RuntimeError("too many unknown events")
      
      if new_format:
        events.append((
          timestamp,
          event_name,
          int.from_bytes(event_bytes[6:8], "little"),
          int.from_bytes(event_bytes[8:12], "little"), # length (for hold notes)
        ))
      else:
        events.append((
          timestamp,
          event_name,
          int.from_bytes(event_bytes[6:8], "little"),
          0, # no length in old format bc no hold notes
        ))

  return events

def get_events_by_timestamp(bin_filename, new_format):
  events = get_events(bin_filename, new_format)

  events_by_timestamp = defaultdict(dict)

  for timestamp, event_name, value, length in events:
    if event_name == "bpm":
      events_by_timestamp[timestamp][event_name] = value
    
    elif event_name == "end":
      events_by_timestamp[timestamp][event_name] = "e"
    
    elif event_name == "beat":
      events_by_timestamp[timestamp][event_name] = "b"
    
    elif event_name == "measure":
      events_by_timestamp[timestamp][event_name] = "m"

    elif event_name == "key":
      btn_ord = value & 0xff
      btn_comm = btn_ord + 1

      if length > 0: # hold note
        if "keyon" not in events_by_timestamp[timestamp]:
          events_by_timestamp[timestamp]["keyon"] = 0
        events_by_timestamp[timestamp]["keyon"] |= 1 << btn_ord

        keyoff_timestamp = timestamp + length
        if "keyoff" not in events_by_timestamp[keyoff_timestamp]:
          events_by_timestamp[keyoff_timestamp]["keyoff"] = 0
        events_by_timestamp[keyoff_timestamp]["keyoff"] |= 1 << btn_ord

      else:
        if "key" not in events_by_timestamp[timestamp]:
          events_by_timestamp[timestamp]["key"] = 0
        events_by_timestamp[timestamp]["key"] |= 1 << btn_ord

    elif event_name == "timing":
      if "timing" not in events_by_timestamp[timestamp]:
        events_by_timestamp[timestamp]["timing"] = {}
      frame_idx, frame_val = value >> 12, value & 0xff
      events_by_timestamp[timestamp]["timing"][frame_idx] = frame_val

  return events_by_timestamp
