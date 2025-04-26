from parse_chart import get_events

"""
Currently only supports old format.

Usage:
  # Prerequisites:
  #   1) bin file for chart whose notes you want to replace
  #   2) serial chart dump file with new notes

  python replace_notes.py --old-bin-file sorasumi_op.bin --new-serial-file sorasumi_op_new_serial.csv --out-file sorasumi_op_new.bin
"""
if __name__ == "__main__":
  import argparse
  import csv

  parser = argparse.ArgumentParser()
  parser.add_argument("--old-bin-file", required=True)
  parser.add_argument("--new-serial-file", required=True)
  parser.add_argument("--out-file", required=True)
  args = parser.parse_args()

  old_bin_filename = args.old_bin_file
  new_serial_filename = args.new_serial_file
  out_filename = args.out_file

  if old_bin_filename == out_filename:
    print("Not recommended to output to (and effectively overwrite) old bin file.")
    exit(1)

  old_events = get_events(old_bin_filename)
  old_events_without_key = [event for event in old_events if event[1] != "key"]

  new_key_events = []
  with open(new_serial_filename, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
      if not row["key"]:
        continue
      
      encoded_key_int = int(row["key"])
      keys = [ord for ord in range(9) if encoded_key_int >> ord & 1]
      for key in keys:
        new_key_events.append((int(row["timestamp"]), "key", key, 0)) # only old format for now
  
  # Merge events. Events must remain ordered by timestamp. For each timestamp, key events go first.
  new_events = []
  i_old, i_new = 0, 0
  while i_old < len(old_events_without_key) and i_new < len(new_key_events):
    next_old = old_events_without_key[i_old] 
    next_new = new_key_events[i_new]
    if next_new[0] <= next_old[0]:
      new_events.append(next_new)
      i_new += 1
    else:
      new_events.append(next_old)
      i_old += 1
  new_events += old_events_without_key[i_old:]
  new_events += new_key_events[i_new:]

  event_name_to_id = {
    "key": 0x0145,
    "sample": 0x0245,
    "unk0345": 0x0345,
    "bpm": 0x0445,
    "timesig": 0x0545,
    "end": 0x0645,
    "sample2": 0x0745,
    "timing": 0x0845,
    "unk0945": 0x0945,
    "unk0d45": 0x0d45,
    "measure": 0x0a00,
    "beat": 0x0b00,
    "unk000f": 0x000f,
  }

  with open(out_filename, "wb") as f:
    for timestamp, event_name, event_value, _ in new_events:
      f.write(timestamp.to_bytes(4, byteorder="little"))
      f.write(event_name_to_id[event_name].to_bytes(2, byteorder="little"))
      f.write(event_value.to_bytes(2, byteorder="little"))
