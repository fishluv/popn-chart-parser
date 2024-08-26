from collections import defaultdict

from parse_chart import parse_chart

def get_events_by_timestamp(bin_filename, new_format):
  events = parse_chart(bin_filename, new_format)

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

  return events_by_timestamp

"""
Usage:
  # Extract bin files from ifs first
  ifstools iidx_kida.ifs

  # Print serialized chart to stdout
  python serialize_chart.py --bin-file iidx_kida_ifs/iidx_kida_op.bin --format new
"""
if __name__ == "__main__":
  import argparse
  import json

  parser = argparse.ArgumentParser()
  parser.add_argument("--bin-file", required=True)
  parser.add_argument("--format", help="'new' or 'old'", required=True)
  args = parser.parse_args()

  bin_filename = args.bin_file
  new_format = args.format == "new"

  events_by_timestamp = get_events_by_timestamp(bin_filename, new_format)

  print("timestamp,key,keyon,keyoff,measurebeatend,bpm")
  for timestamp in sorted(events_by_timestamp.keys()):
    events = events_by_timestamp[timestamp]
    print(",".join(map(str, [
      timestamp,
      events.get("key", ""),
      events.get("keyon", ""),
      events.get("keyoff", ""),
      events.get("end", events.get("measure", events.get("beat", ""))),
      events.get("bpm", ""),
    ])))
