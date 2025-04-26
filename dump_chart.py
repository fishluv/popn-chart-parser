"""
Usage:
  # Print events to stdout
  python dump_chart.py --bin-file <chart_bin_file> [--raw|--serial] [--out-file <output_file>]
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
  parser.add_argument("--out-file", help="Output file. If omitted, will output to stdout.")
  args = parser.parse_args()

  if args.raw and args.serial:
    print("only one of --raw and --serial may be used")
    exit(1)
  
  if not args.raw and not args.serial:
    print("one of --raw and --serial must be provided")
    exit(1)

  bin_filename = args.bin_file
  out_filename = args.out_file

  if args.raw:
    events = get_events(bin_filename, True)

    if out_filename:
      with open(out_filename, "w") as f:
        for timestamp, event_name, value, length in events:
          f.write("%s,%s,%s,%s\n" % (timestamp, event_name, value, length))
    else:
      for timestamp, event_name, value, length in events:
        if event_name == "timesig":
          top, bottom = value >> 8, value & 0xff
          value = f"{top}/{bottom}"
        elif event_name == "timing":
          frame_idx, frame_val = value >> 12, value & 0xff
          value = f"{frame_idx}/{frame_val}"
        elif event_name == "loadsample" or event_name == "playsample":
          # For loadsample, val1 is the key that will trigger the sample.
          # For playsample, val1 is unknown.
          val1, sample_idx = value >> 12, value & 0xff
          value = f"{val1}/{sample_idx}"
        print("%s,%s,%s,%s" % (timestamp, event_name, value, length))

  else: # serial
    events_by_timestamp = get_events_by_timestamp(bin_filename)
    timing_event_tss = [ts for ts, events in events_by_timestamp.items() if "timing" in events]
    has_variable_timing = len([events for events in events_by_timestamp.values() if "timing" in events]) >= 2
    has_variable_timesig = len([events for events in events_by_timestamp.values() if "timesig" in events]) >= 2

    headers = ["timestamp", "key", "keyon", "keyoff", "measurebeatend", "bpm"]
    if has_variable_timing:
      headers.append("timing")
    if has_variable_timesig:
      headers.append("timesig")

    if out_filename:
      f = open(out_filename, "w")
      out_func = lambda s: f.write(s + "\n")
    else:
      out_func = print

    try:
      out_func(",".join(headers))

      for timestamp in sorted(events_by_timestamp.keys()):
        events = events_by_timestamp[timestamp]

        vals = [
          timestamp,
          events.get("key", ""),
          events.get("keyon", ""),
          events.get("keyoff", ""),
          events.get("end", events.get("measure", events.get("beat", ""))),
          events.get("bpm", ""),
        ]
        if has_variable_timing:
          vals.append(timing_event_tss.index(timestamp) if "timing" in events else "")
        if has_variable_timesig:
          vals.append(events.get("timesig", ""))

        out_func(",".join(map(str, vals)))
    finally:
      if out_filename:
        f.close()
