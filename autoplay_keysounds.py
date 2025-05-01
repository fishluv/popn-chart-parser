from parse_chart import get_events

"""
Merge two sorted iterables based on some predicate. If the predicate returns the same value for each iterable, prefer the first.
"""
def _merge(first, second, predicate):
  out = []
  i_first, i_second = 0, 0
  while i_first < len(first) and i_second < len(second):
    next_first = first[i_first] 
    next_second = second[i_second]
    # Prefer first for equality.
    if predicate(next_first) <= predicate(next_second):
      out.append(next_first)
      i_first += 1
    else:
      out.append(next_second)
      i_second += 1
  out += first[i_first:]
  out += second[i_second:]
  return out

"""
Disables/autoplays keysounds for a chart.

Accomplishes this by converting `loadsample` commands into `playsample` commands.

Usage:
  python autoplay_keysounds.py --bin-in-file sorasumi_op.bin --bin-out-file sorasumi_op_new.bin
"""
if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("-b", "--bin-in-file", required=True)
  parser.add_argument("-o", "--bin-out-file", required=True)
  args = parser.parse_args()

  bin_in_file = args.bin_in_file
  bin_out_file = args.bin_out_file

  if bin_in_file == bin_out_file:
    print("Not recommended to output to (and effectively overwrite) input bin file.")
    exit(1)

  old_events = get_events(bin_in_file)
  old_events_without_loadsample = [event for event in old_events if event[1] != "loadsample"]

  first_key_timestamp = next(event for event in old_events if event[1] == "key")[0]
  # All charts (even non-keysounded ones) have 9 loadsample events somewhere between 130-250 ms before the first key event.
  # One loadsample event for each key. Some of these events load sample 0 (necessary dummy events) but others are real.
  # In the output chart we just want 9 dummy events, with sample index 0.
  # loadsample values are calculated by `key << 12 | sample_idx` but since sample_idx is 0 we can just do `key << 12`.
  new_dummy_loadsample_events = [(first_key_timestamp - 200, "loadsample", key << 12, 0) for key in range(9)]

  # Convert loadsample events to playsample events.
  new_playsample_events = []
  for i, event in enumerate(old_events):
    timestamp, event_name, event_value, _ = event
    if event_name != "loadsample":
      continue
    # Ignore dummy loadsample events!
    if event_value & 0xff == 0:
      continue

    key, sample_idx = event_value >> 12, event_value & 0xff
    matching_key_event = next(e for j, e in enumerate(old_events) if j > i and e[1] == "key" and e[2] == key)
    playsample_val = (8 << 12) | sample_idx # Purpose of `8` is unknown but all playsample events have it.
    new_playsample_events.append((matching_key_event[0], "playsample", playsample_val, 0))

  new_events = _merge(new_dummy_loadsample_events, new_playsample_events, lambda event: event[0])
  final_events = _merge(old_events_without_loadsample, new_events, lambda event: event[0])

  event_name_to_id = {
    "key": 0x0145,
    "loadsample": 0x0245,
    "playbgsample": 0x0345,
    "bpm": 0x0445,
    "timesig": 0x0545,
    "end": 0x0645,
    "playsample": 0x0745,
    "timing": 0x0845,
    "unk0945": 0x0945,
    "unk0d45": 0x0d45,
    "measure": 0x0a00,
    "beat": 0x0b00,
    "unk000f": 0x000f,
  }

  with open(bin_out_file, "wb") as f:
    for timestamp, event_name, event_value, _ in final_events:
      f.write(timestamp.to_bytes(4, byteorder="little"))
      f.write(event_name_to_id[event_name].to_bytes(2, byteorder="little"))
      f.write(event_value.to_bytes(2, byteorder="little"))
