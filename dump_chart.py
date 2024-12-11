"""
Usage:
  # Print events to stdout
  python dump_chart.py --bin-file <chart_bin_file> --format [old|new] [--raw|--serial] [--out-file <output_file>]
"""
if __name__ == "__main__":
  import argparse
  import json

  try:
    from parse_chart import get_events, get_events_by_timestamp
  except ImportError:
    from .parse_chart import get_events, get_events_by_timestamp

  parser = argparse.ArgumentParser()
  parser.add_argument("--raw", action="store_true")
  parser.add_argument("--serial", action="store_true")
  parser.add_argument("--bin-file", required=True)
  parser.add_argument("--format", help="'new' or 'old'", required=True)
  parser.add_argument("--out-file", help="Output file. If omitted, will output to stdout.")
  args = parser.parse_args()

  if args.raw and args.serial:
    print("only one of --raw and --serial may be used")
    exit(1)
  
  if not args.raw and not args.serial:
    print("one of --raw and --serial must be provided")
    exit(1)

  bin_filename = args.bin_file
  new_format = args.format == "new"
  out_filename = args.out_file

  if args.raw:
    events = get_events(bin_filename, new_format, True)

    if out_filename:
      with open(out_filename, "w") as f:
        for timestamp, event_name, value, length in events:
          f.write("%s,%s,%s,%s\n" % (timestamp, event_name, value, length))
    else:
      for timestamp, event_name, value, length in events:
        print("%s,%s,%s,%s" % (timestamp, event_name, value, length))

  else: # serial
    events_by_timestamp = get_events_by_timestamp(bin_filename, new_format)
    timing_event_tss = [ts for ts, events in events_by_timestamp.items() if "timing" in events]
    has_variable_timing = len([events for events in events_by_timestamp.values() if "timing" in events]) >= 2

    if out_filename:
      with open(out_filename, "w") as f:
        if has_variable_timing:
          f.write("timestamp,key,keyon,keyoff,measurebeatend,bpm,timing\n")
          for timestamp in sorted(events_by_timestamp.keys()):
            events = events_by_timestamp[timestamp]
            f.write(",".join(map(str, [
              timestamp,
              events.get("key", ""),
              events.get("keyon", ""),
              events.get("keyoff", ""),
              events.get("end", events.get("measure", events.get("beat", ""))),
              events.get("bpm", ""),
              timing_event_tss.index(timestamp) if "timing" in events else "",
            ])) + "\n")
        else:
          f.write("timestamp,key,keyon,keyoff,measurebeatend,bpm\n")
          for timestamp in sorted(events_by_timestamp.keys()):
            events = events_by_timestamp[timestamp]
            f.write(",".join(map(str, [
              timestamp,
              events.get("key", ""),
              events.get("keyon", ""),
              events.get("keyoff", ""),
              events.get("end", events.get("measure", events.get("beat", ""))),
              events.get("bpm", ""),
            ])) + "\n")

    else:
      if has_variable_timing:
        print("timestamp,key,keyon,keyoff,measurebeatend,bpm,timing")
        for timestamp in sorted(events_by_timestamp.keys()):
          events = events_by_timestamp[timestamp]
          print(",".join(map(str, [
            timestamp,
            events.get("key", ""),
            events.get("keyon", ""),
            events.get("keyoff", ""),
            events.get("end", events.get("measure", events.get("beat", ""))),
            events.get("bpm", ""),
            timing_event_tss.index(timestamp) if "timing" in events else "",
          ])))
      else:
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
