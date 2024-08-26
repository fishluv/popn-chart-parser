def parse_chart(bin_filename, new_format, debug=False):
  if not bin_filename.endswith(".bin"):
    print("[fatal] only bin files are supported")
    exit(1)

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
          print("[fatal] too many unknown events")
          exit(1)
      
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

"""
Usage:
  # Extract bin files from ifs first
  ifstools iidx_kida.ifs

  # Print events to stdout
  python parse_chart.py --bin-file iidx_kida_ifs/iidx_kida_op.bin --format new
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

  events = parse_chart(bin_filename, new_format, True)

  for timestamp, event_name, value, length in events:
    print("%s,%s,%s,%s" % (timestamp, event_name, value, length))
